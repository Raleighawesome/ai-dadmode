// OS-specific installation commands for Obsidian Gmail

export type OS = 'macos' | 'windows' | 'linux';

export interface CommandSet {
  checkPython: string;
  installDeps: string;
  createScriptsDir: string;
  downloadScript: string;
  testScript: string;
  createGoogleDir: string;
  createOAuthDir: string;
}

const SCRIPT_URL = 'https://raw.githubusercontent.com/Raleighawesome/ai-dadmode/main/public/downloads/obsidian-gmail/imap_ingest_md_only.py';

export const commands: Record<OS, CommandSet> = {
  macos: {
    checkPython: 'python3 --version',
    installDeps: 'python3 -m pip install imapclient google-auth google-auth-oauthlib',
    createScriptsDir: 'mkdir -p ~/scripts/ai_scripts',
    downloadScript: `curl -o ~/scripts/ai_scripts/imap_ingest_md_only.py \\
  ${SCRIPT_URL} && chmod +x ~/scripts/ai_scripts/imap_ingest_md_only.py`,
    testScript: 'python3 ~/scripts/ai_scripts/imap_ingest_md_only.py --help',
    createGoogleDir: 'mkdir -p ~/.google',
    createOAuthDir: 'mkdir -p ~/scripts/ai_scripts',
  },
  linux: {
    checkPython: 'python3 --version',
    installDeps: 'python3 -m pip install imapclient google-auth google-auth-oauthlib',
    createScriptsDir: 'mkdir -p ~/scripts/ai_scripts',
    downloadScript: `curl -o ~/scripts/ai_scripts/imap_ingest_md_only.py \\
  ${SCRIPT_URL} && chmod +x ~/scripts/ai_scripts/imap_ingest_md_only.py`,
    testScript: 'python3 ~/scripts/ai_scripts/imap_ingest_md_only.py --help',
    createGoogleDir: 'mkdir -p ~/.google',
    createOAuthDir: 'mkdir -p ~/scripts/ai_scripts',
  },
  windows: {
    checkPython: 'python --version',
    installDeps: 'python -m pip install imapclient google-auth google-auth-oauthlib',
    createScriptsDir: 'mkdir %USERPROFILE%\\scripts\\ai_scripts',
    downloadScript: `Invoke-WebRequest -Uri "${SCRIPT_URL}" -OutFile "$env:USERPROFILE\\scripts\\ai_scripts\\imap_ingest_md_only.py"`,
    testScript: 'python %USERPROFILE%\\scripts\\ai_scripts\\imap_ingest_md_only.py --help',
    createGoogleDir: 'mkdir %USERPROFILE%\\.google',
    createOAuthDir: 'mkdir %USERPROFILE%\\scripts\\ai_scripts',
  },
};

export function getCommands(os: OS): CommandSet {
  return commands[os];
}
