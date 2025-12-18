#!/usr/bin/env python3
"""
Local Gmail IMAP → Obsidian Markdown (NO QDRANT EMBEDDING)
Dedup-safe: never create duplicates; update-in-place when content changes.

This is an alternate version of imap_ingest.py that only creates markdown files
without embedding to Qdrant. Perfect for when you want to just organize emails
in your Obsidian vault without vector database storage.

- Auth: OAuth 2.0 (XOAUTH2) using google-auth-oauthlib (works with Workspace SSO).
- Dedupe: persistent index keyed by X-GM-MSGID and Message-ID.
- No embedding: Skips all embedding operations entirely.
"""

from __future__ import annotations
import argparse
import datetime as dt
import email
import email.policy
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# --- deps ---
from imapclient import IMAPClient
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# -------------------- Defaults --------------------

# Set your Gmail address here or via environment variable
# os.environ['GMAIL_USER'] = 'your-email@gmail.com'

DEFAULT_VAULT_ROOT = "~/Obsidian/YourVault"
EMAILS_DIR         = "Emails"
ASSETS_DIR         = "Assets/Emails"
STATE_FILE         = ".imap_ingest_state.json"       # legacy; kept for backwards compat
INDEX_FILE         = ".imap_ingest_index.json"       # new: dedupe index

# OAuth files (can override via CLI) - relative to script directory
SCRIPT_DIR = Path(__file__).parent.absolute()
DEFAULT_OAUTH_CLIENT = str(SCRIPT_DIR / "client_secret.json")
DEFAULT_OAUTH_TOKEN  = str(SCRIPT_DIR / "gmail_oauth_token.json")
SCOPES = ["https://mail.google.com/"]

# NO EMBEDDING COMMAND - This is the key difference from the original script
# EMBED_CMD is removed entirely

LABEL_ALIASES = {
    "AI/Ingest": "Save",
    "ai/ingest": "Save",
    "To-Embed": "Save",  # backwards compatibility
    "Slack Thread": "Slack-Thread",
    "AI/Slack-Thread": "Slack-Thread",
}
CANONICAL_LABELS = {"Save", "Slack-Thread"}

# -------------------- Utils --------------------

def slugify(text: str, max_len: int = 80) -> str:
    s = (text or "email").lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    return (s or "email")[:max_len]

def decode_words(s: Optional[str]) -> str:
    if not s: return ""
    try:
        parts = email.header.decode_header(s)
        out = []
        for text, enc in parts:
            out.append(text.decode(enc or "utf-8","replace") if isinstance(text, bytes) else text)
        return "".join(out)
    except Exception:
        return s

def parse_addr_list(hdr_val: str) -> List[Dict[str, str]]:
    if not hdr_val: return []
    addrs = email.utils.getaddresses([hdr_val])
    return [{"name": decode_words(name).strip('"'), "email": addr} for name, addr in addrs]

def parsedate_to_iso(hdr_date: Optional[str], fallback_dt: Optional[dt.datetime] = None) -> str:
    try:
        d = email.utils.parsedate_to_datetime(hdr_date) if hdr_date else None
        if d and d.tzinfo is None: d = d.replace(tzinfo=dt.timezone.utc)
        return (d or fallback_dt or dt.datetime.now(dt.timezone.utc)).isoformat()
    except Exception:
        return (fallback_dt or dt.datetime.now(dt.timezone.utc)).astimezone().isoformat()

def html_to_md_quick(html: str) -> str:
    if not html: return ""
    s = re.sub(r"<head[\s\S]*?</head>", "", html, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", "", s, flags=re.I)
    s = re.sub(r"<script[\s\S]*?</script>", "", s, flags=re.I)
    s = re.sub(r"</?br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?p[^>]*>", "\n\n", s, flags=re.I)
    s = re.sub(r"</?li[^>]*>", "\n- ", s, flags=re.I)
    s = re.sub(r"</?h([1-6])[^>]*>(.*?)</h\1>", lambda m: "\n" + ("#"*int(m.group(1))) + " " + m.group(2) + "\n", s, flags=re.I|re.S)
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("&nbsp;"," ").replace("&amp;","&").replace("&lt;","<").replace("&gt;",">").strip()

def body_from_email(msg: email.message.EmailMessage) -> Tuple[str, str]:
    text_plain, text_html = [], []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment": continue
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try: text_plain.append(part.get_content().strip())
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    text_plain.append(payload.decode(part.get_content_charset() or "utf-8","replace").strip())
            elif ctype == "text/html":
                try: text_html.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    text_html.append(payload.decode(part.get_content_charset() or "utf-8","replace"))
    else:
        ctype = msg.get_content_type()
        if ctype == "text/plain": text_plain.append(msg.get_content().strip())
        elif ctype == "text/html": text_html.append(msg.get_content())
    plain = "\n\n".join(x for x in text_plain if x).strip()
    html  = "\n\n".join(x for x in text_html if x).strip()
    if plain: return plain, "plain"
    if html:  return html_to_md_quick(html), "html->md"
    return (msg.as_string()[:40000], "raw")

def checksum_for(payload: Dict) -> str:
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{h}"

def read_existing_checksum(md_path: Path) -> Optional[str]:
    if not md_path.exists(): return None
    try:
        head = md_path.read_text("utf-8")[:4000]
        m = re.search(r'^\s*checksum:\s*"(sha256:[a-f0-9]+)"\s*$', head, flags=re.M)
        return m.group(1) if m else None
    except Exception:
        return None

def extract_ids_from_file_head(md_path: Path) -> Tuple[Optional[str], Optional[int]]:
    """
    Returns (message_id_string_without_angles, x_gm_msgid_int) if found in YAML front-matter head.
    """
    try:
        head = md_path.read_text("utf-8")[:4000]
    except Exception:
        return (None, None)
    msgid = None
    # message_id: "<...>"
    m1 = re.search(r'^\s*message_id:\s*"?<?([^">\n]+)>?"?\s*$', head, flags=re.M)
    if m1: msgid = m1.group(1).strip()
    # x_gm_msgid: "12345"
    m2 = re.search(r'^\s*x_gm_msgid:\s*"?(\d+)"?\s*$', head, flags=re.M)
    gm = int(m2.group(1)) if m2 else None
    return (msgid, gm)

def canonicalize_labels(labels: List[str]) -> List[str]:
    out = []
    for lbl in labels:
        l = LABEL_ALIASES.get(lbl.strip(), lbl.strip())
        if l not in out: out.append(l)
    return out

def wants_processing(labels: List[str]) -> bool:
    """
    Renamed from wants_embedding to wants_processing since we're not embedding.
    Checks for 'Save' and 'Slack-Thread' labels to determine if email should be processed.
    """
    return any(l in ("Save", "Slack-Thread") for l in labels)

def infer_doc_type(labels: List[str]) -> str:
    return "slack" if "Slack-Thread" in labels else "email"

def ensure_dirs(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

# -------------------- OAuth / IMAP auth --------------------

def load_creds(client_secret_path: Path, token_path: Path) -> Credentials:
    creds: Optional[Credentials] = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent")
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds

def imap_oauth2_login(server: IMAPClient, user_email: str, creds: Credentials):
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    token = creds.token
    try:
        server.oauth2_login(user_email, token)
    except AttributeError:
        auth_string = f"user={user_email}\1auth=Bearer {token}\1\1"
        server._imap.authenticate("XOAUTH2", lambda x: auth_string)

# -------------------- Dedupe index --------------------

def load_index(path: Path) -> Dict:
    if not path.exists():
        return {"by_gm_msgid": {}, "by_message_id": {}}
    try:
        data = json.loads(path.read_text("utf-8"))
        data.setdefault("by_gm_msgid", {})
        data.setdefault("by_message_id", {})
        return data
    except Exception:
        return {"by_gm_msgid": {}, "by_message_id": {}}

def save_index(path: Path, data: Dict):
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logging.warning("Failed to save dedupe index: %s", e)

def scan_recent_for_existing(vault_root: Path, years_back: int = 3) -> Dict:
    """
    Lightweight scan of recent Emails to rebuild a minimal id→path map.
    Scans both old structure (year/month/day) and new structure (year/quarter).
    """
    base = vault_root / EMAILS_DIR
    now_y = dt.datetime.now().year
    found = {}
    for y in range(now_y, now_y - years_back, -1):
        ydir = base / str(y)
        if not ydir.exists(): continue
        for md in ydir.rglob("*.md"):
            mid, gmid = extract_ids_from_file_head(md)
            if mid:  found.setdefault("by_message_id", {})[mid] = str(md)
            if gmid: found.setdefault("by_gm_msgid", {})[str(gmid)] = str(md)
    return {"by_gm_msgid": found.get("by_gm_msgid", {}), "by_message_id": found.get("by_message_id", {})}

# -------------------- Build Markdown --------------------

def build_markdown(
    *,
    vault_root: Path,
    msg: email.message.EmailMessage,
    gm_labels: List[str],
    gm_msgid: Optional[int],
    gm_thrid: Optional[int],
    internaldate: Optional[dt.datetime],
) -> Tuple[Path, str, Dict]:
    subject = decode_words(msg.get("Subject") or "(no subject)")
    from_hdr = decode_words(msg.get("From") or "")
    to_hdr   = decode_words(msg.get("To") or "")
    cc_hdr   = decode_words(msg.get("Cc") or "")
    message_id = (msg.get("Message-Id") or msg.get("Message-ID") or "").strip().strip("<>")
    from_list = parse_addr_list(from_hdr)
    to_list   = parse_addr_list(to_hdr)
    cc_list   = parse_addr_list(cc_hdr)
    date_iso  = parsedate_to_iso(msg.get("Date"), internaldate)
    body_md, _ = body_from_email(msg)

    canon_labels = canonicalize_labels(gm_labels)
    doc_type = infer_doc_type(canon_labels)

    d_local = dt.datetime.fromisoformat(date_iso.replace("Z", "+00:00")).astimezone()
    y, m, d_ = d_local.year, d_local.month, f"{d_local.day:02d}"

    # Calculate quarter based on month
    quarter = (m - 1) // 3 + 1
    quarter_str = f"Q{quarter}{str(y)[-2:]}"  # e.g., Q425 for Q4 2025

    slug = slugify(subject)
    short = (str(gm_msgid) if gm_msgid else hashlib.md5((message_id or subject).encode()).hexdigest())[-6:]

    rel_dir  = Path(EMAILS_DIR) / str(y) / quarter_str
    rel_path = rel_dir / f"{slug}-{short}.md"
    abs_path = vault_root / rel_path

    gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{gm_msgid or ''}"

    payload_for_checksum = {
        "subject": subject,
        "from": from_list,
        "to": to_list,
        "cc": cc_list,
        "date": date_iso,
        "labels": canon_labels,
        "body": body_md[:200000],
        "doc_type": doc_type,
        "gm_msgid": gm_msgid,
        "gm_thrid": gm_thrid,
        "message_id": message_id,
    }
    checksum = checksum_for(payload_for_checksum)

    yaml = [
        "---",
        f"type: {doc_type}",
        "source: imap/gmail",
        "gmail:",
        f"  x_gm_msgid: \"{gm_msgid or ''}\"",
        f"  x_gm_thrid: \"{gm_thrid or ''}\"",
        f"  message_id: \"{message_id}\"",
        f"subject: {json.dumps(subject)}",
        f"from: {json.dumps(from_list[0] if from_list else {'name':'','email':''})}",
        f"to: {json.dumps(to_list)}",
        f"cc: {json.dumps(cc_list)}",
        f"date: {date_iso}",
        f"labels: {json.dumps(canon_labels)}",
        "attachments: []",
        f"checksum: \"{checksum}\"",
        f"ingested_at: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        f"canonical_url: {json.dumps(gmail_url)}",
        "---",
        "",
    ]
    md = "".join(line + ("\n" if not line.endswith("\n") else "") for line in yaml) + body_md + "\n"

    meta = {
        "path_abs": str(abs_path),
        "path_rel": str(rel_path),
        "checksum": checksum,
        "doc_type": doc_type,
        "message_id": message_id,
        "x_gm_msgid": str(gm_msgid) if gm_msgid else None,
    }
    return abs_path, md, meta

# REMOVED: embed_file function - not needed for markdown-only version

def gmail_label_query(labels: List[str], since: Optional[str]) -> str:
    parts = []
    if labels: parts.append("(" + " OR ".join([f'label:\"{l}\"' for l in labels]) + ")")
    if since:
        rel = re.fullmatch(r"(\d+)([dwmy])", since.strip(), flags=re.I)
        if rel:
            num, unit = int(rel.group(1)), rel.group(2).lower()
            days = num * {"d":1, "w":7, "m":30, "y":365}[unit]
            cutoff = (dt.datetime.utcnow() - dt.timedelta(days=days)).date().strftime("%Y/%m/%d")
            parts.append(f"after:{cutoff}")
        else:
            parts.append(f"after:{since.replace('-', '/')}")
    return " ".join(parts) if parts else "in:anywhere"

# -------------------- Main --------------------

def main():
    ap = argparse.ArgumentParser(description="Fetch labeled Gmail via IMAP (OAuth2/SSO), write Obsidian Markdown only. NO EMBEDDING. Dedup-safe.")
    ap.add_argument("--vault-root", default=DEFAULT_VAULT_ROOT)
    ap.add_argument("--labels", nargs="+", default=["Save"])
    ap.add_argument("--since", default=None)
    ap.add_argument("--max", type=int, default=500)
    # REMOVED: --no-embed and --embed-cmd options - embedding is never done
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state-file", default=STATE_FILE)              # kept for compat
    ap.add_argument("--index-file", default=INDEX_FILE)              # new dedupe index
    ap.add_argument("--log-level", default="INFO")
    # IMAP
    ap.add_argument("--imap-host", default="imap.gmail.com")
    ap.add_argument("--imap-port", type=int, default=993)
    ap.add_argument("--imap-ssl", action="store_true", default=True)
    # OAuth
    ap.add_argument("--oauth-client", default=DEFAULT_OAUTH_CLIENT)
    ap.add_argument("--oauth-token", default=DEFAULT_OAUTH_TOKEN)
    args = ap.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(levelname)s: %(message)s")

    user_email = os.environ.get("GMAIL_USER")
    if not user_email:
        logging.error("Set GMAIL_USER (e.g., export GMAIL_USER='you@gmail.com').")
        sys.exit(2)

    vault_root = Path(args.vault_root).expanduser().resolve()
    vault_root.mkdir(parents=True, exist_ok=True)

    # legacy state (still loaded/written for back-compat)
    state_path = (vault_root / args.state_file) if not os.path.isabs(args.state_file) else Path(args.state_file)
    try:
        legacy_state = json.loads(state_path.read_text("utf-8")) if state_path.exists() else {}
    except Exception:
        legacy_state = {}

    # dedupe index
    index_path = (vault_root / args.index_file) if not os.path.isabs(args.index_file) else Path(args.index_file)
    index = load_index(index_path)

    # opportunistic repair of index (fast scan of recent years)
    if not index["by_gm_msgid"] and not index["by_message_id"]:
        logging.info("Dedupe index empty; scanning recent notes to seed it…")
        seeded = scan_recent_for_existing(vault_root, years_back=3)
        # merge
        index["by_gm_msgid"].update(seeded["by_gm_msgid"])
        index["by_message_id"].update(seeded["by_message_id"])

    client_path = Path(args.oauth_client).expanduser().resolve()
    token_path  = Path(args.oauth_token).expanduser().resolve()
    creds = load_creds(client_path, token_path)

    query = gmail_label_query(args.labels, args.since)
    logging.info("Gmail raw query: %s", query)

    with IMAPClient(args.imap_host, port=args.imap_port, ssl=args.imap_ssl) as srv:
        imap_oauth2_login(srv, user_email, creds)

        folder = "[Gmail]/All Mail"
        folders = {name.decode() if isinstance(name, bytes) else name for _, _, name in srv.list_folders()}
        if folder not in folders: folder = "INBOX"
        srv.select_folder(folder, readonly=True)

        uids = srv.search(["X-GM-RAW", query])
        logging.info("Matched %d messages", len(uids))
        if not uids: return

        uids = list(sorted(uids, reverse=True))[: args.max]
        fetch_keys = [b"BODY[]", b"ENVELOPE", b"X-GM-LABELS", b"X-GM-THRID", b"X-GM-MSGID", b"INTERNALDATE", b"RFC822.SIZE"]
        resp = srv.fetch(uids, fetch_keys)

        processed = 0
        index_updated = False

        for uid in uids:
            data = resp.get(uid) or {}
            raw = data.get(b"BODY[]") or data.get(b"RFC822")
            if not raw:
                logging.warning("No BODY for UID %s; skipping.", uid); continue

            try:
                msg: email.message.EmailMessage = email.message_from_bytes(raw, policy=email.policy.default)
            except Exception as e:
                logging.warning("Parse error UID %s: %s", uid, e); continue

            gm_labels = [lbl.decode() if isinstance(lbl, bytes) else lbl for lbl in (data.get(b"X-GM-LABELS") or [])]
            gm_msgid  = int(data.get(b"X-GM-MSGID")) if data.get(b"X-GM-MSGID") else None
            gm_thrid  = int(data.get(b"X-GM-THRID")) if data.get(b"X-GM-THRID") else None
            internal  = data.get(b"INTERNALDATE")
            internal_dt = internal if isinstance(internal, dt.datetime) else None

            canon_labels = canonicalize_labels(gm_labels)
            if not wants_processing(canon_labels):  # renamed from wants_embedding
                logging.debug("Skip UID %s (no canonical processing labels)", uid)
                continue

            # ---------- DEDUPE: find existing note path (index → legacy → scan) ----------
            message_id = (msg.get("Message-Id") or msg.get("Message-ID") or "").strip().strip("<>")
            existing_path: Optional[Path] = None

            if gm_msgid and str(gm_msgid) in index["by_gm_msgid"]:
                existing_path = Path(index["by_gm_msgid"][str(gm_msgid)])
            elif message_id and message_id in index["by_message_id"]:
                existing_path = Path(index["by_message_id"][message_id])
            else:
                # fallback scan (cheap head parse) to repair index
                seeded = scan_recent_for_existing(vault_root, years_back=3)
                index["by_gm_msgid"].update(seeded["by_gm_msgid"])
                index["by_message_id"].update(seeded["by_message_id"])
                index_updated = True
                if gm_msgid and str(gm_msgid) in index["by_gm_msgid"]:
                    existing_path = Path(index["by_gm_msgid"][str(gm_msgid)])
                elif message_id and message_id in index["by_message_id"]:
                    existing_path = Path(index["by_message_id"][message_id])

            # Build markdown & default target path (used if no existing)
            abs_path, md, meta = build_markdown(
                vault_root=vault_root,
                msg=msg,
                gm_labels=canon_labels,
                gm_msgid=gm_msgid,
                gm_thrid=gm_thrid,
                internaldate=internal_dt,
            )

            # If we already have a file for this message, use that path instead
            target_path = existing_path if existing_path else abs_path

            existing_checksum = read_existing_checksum(target_path)
            if existing_checksum == meta["checksum"]:
                # No changes — truly skip (no re-import)
                logging.info("Duplicate/no-change: %s", target_path)
            else:
                action = "Update" if target_path.exists() else "Write"
                logging.info(("%s (deduped): " if existing_path else "%s: ") % action + "%s", target_path)
                if not args.dry_run:
                    ensure_dirs(target_path)
                    target_path.write_text(md, encoding="utf-8")

            # Update indices (path + checksum) after write/skip
            key = str(gm_msgid) if gm_msgid else None
            if key:
                if index["by_gm_msgid"].get(key) != str(target_path):
                    index["by_gm_msgid"][key] = str(target_path); index_updated = True
            if message_id:
                if index["by_message_id"].get(message_id) != str(target_path):
                    index["by_message_id"][message_id] = str(target_path); index_updated = True

            # maintain legacy state for compat (optional)
            legacy_key = str(gm_msgid or uid)
            legacy_entry = legacy_state.get(legacy_key)
            if (not legacy_entry) or (legacy_entry.get("checksum") != meta["checksum"]) or (legacy_entry.get("path") != str(target_path.relative_to(vault_root))):
                legacy_state[legacy_key] = {
                    "path": str(target_path.relative_to(vault_root)),
                    "checksum": meta["checksum"],
                    "type": meta["doc_type"],
                }

            # NO EMBEDDING - This is the key difference!
            # The original script would embed here, but we skip that entirely.
            logging.debug("Markdown-only mode: skipping embedding for %s", target_path)

            processed += 1

        # persist index + legacy state
        if index_updated and not args.dry_run:
            save_index(index_path, index)
        if not args.dry_run:
            try: state_path.write_text(json.dumps(legacy_state, indent=2), encoding="utf-8")
            except Exception: pass

        logging.info("Done. Processed %d message(s) - MARKDOWN ONLY (no embedding).", processed)

if __name__ == "__main__":
    main()
