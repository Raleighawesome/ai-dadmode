# AI Tools Landing Page Design

**Date:** 2025-12-11
**Domain:** ai.dadmode.cc
**Status:** Approved

## Overview

A landing page to showcase AI tools, scripts, and commands for sharing with TikTok audiences. Hub-and-spoke architecture with tool cards linking to documentation subpages.

## Site Architecture

```
ai.dadmode.cc/
├── index.astro              # Landing page with tool grid
├── commands/
│   └── youtube.astro        # YouTube transcript extractor docs
├── projects/
│   └── ai-assistant.astro   # Card/redirect to ai-assistant.dadmode.cc
└── scripts/
    └── (future Python scripts)
```

## Tech Stack

- **Framework:** Astro
- **Styling:** Tailwind CSS 4 (dark theme from ai-assistant site)
- **Hosting:** Vercel
- **Analytics:** Self-hosted Umami
- **DNS:** Cloudflare

## Landing Page Layout

### Header
- Logo/site name: "AI Tools" (left)
- Nav: "Tools" dropdown (expandable as collection grows)
- TikTok button: "raleighawesome" display name, links to @raleighawesome84 (right)

### Hero Section
- Headline: "AI Tools by raleighawesome"
- Subtext: "Scripts, commands, and automation for getting things done with AI"
- Primary CTA: "Follow on TikTok" (links to tiktok.com/@raleighawesome84)
- Secondary CTA: "Browse Tools" (scrolls to grid)

### Tool Grid
- Card-based layout (2-3 columns desktop, 1 mobile)
- Each card shows: icon, name, description, category tag
- Cards link to subpages or external URLs

### Footer
- Social links (TikTok)
- Copyright

## Initial Tools

### 1. YouTube Transcript Extractor
- **Route:** `/commands/youtube`
- **Type:** Claude Code command
- **Description:** Extract YouTube transcripts to Obsidian notes
- **Page Content:**
  - Overview
  - Requirements
  - Installation steps
  - Usage examples
  - Download buttons (Python script + command file)

### 2. AI Executive Assistant
- **Route:** `/projects/ai-assistant`
- **Type:** External link card
- **Description:** Meeting processing, summaries, action items
- **Behavior:** Links to ai-assistant.dadmode.cc

## Umami Analytics Stack

**Location:** `~/scripts/umami-stack/`

### Docker Compose Services
- `umami` - Analytics app (ghcr.io/umami-software/umami)
- `umami-db` - PostgreSQL database
- `cloudflared` - Tunnel for analytics.dadmode.cc

### Tracked Sites
1. ai.dadmode.cc (new site)
2. ai-assistant.dadmode.cc (existing site)

## Cloudflare DNS Configuration

| Subdomain | Type | Target | Proxy |
|-----------|------|--------|-------|
| `ai` | CNAME | `cname.vercel-dns.com` | Proxied |
| `analytics` | CNAME | `<tunnel-id>.cfargotunnel.com` | Proxied |

## Manual Steps Required

1. Create Cloudflare tunnel for Umami in Zero Trust dashboard
2. Copy tunnel token to `~/scripts/umami-stack/.env`
3. Add DNS records in Cloudflare dashboard
4. After Umami first login, create two websites and get tracking IDs
5. Connect Vercel to GitHub repo and add `ai.dadmode.cc` domain
