// OS-specific installation commands for Daily Briefing

export type OS = 'macos' | 'windows' | 'linux';

export interface CommandSet {
  checkPython: string;
  installDeps: string;
  createScriptsDir: string;
  downloadScript: string;
  createCommandDir: string;
  downloadCommand: string;
  testScript: string;
  createGoogleDir: string;
}

const SCRIPT_URL = 'https://raw.githubusercontent.com/Raleighawesome/ai-dadmode/main/public/downloads/daily-briefing/fetch_today_events.py';
const COMMAND_URL = 'https://raw.githubusercontent.com/Raleighawesome/ai-dadmode/main/public/downloads/daily-briefing/daily-briefing.md';

export const commands: Record<OS, CommandSet> = {
  macos: {
    checkPython: 'python3 --version',
    installDeps: 'python3 -m pip install google-auth google-auth-oauthlib google-api-python-client',
    createScriptsDir: 'mkdir -p ~/scripts/calendar-events',
    downloadScript: `curl -o ~/scripts/calendar-events/fetch_today_events.py \\
  ${SCRIPT_URL} && chmod +x ~/scripts/calendar-events/fetch_today_events.py`,
    createCommandDir: 'mkdir -p ~/.claude/commands',
    downloadCommand: `curl -o ~/.claude/commands/daily-briefing.md \\
  ${COMMAND_URL}`,
    testScript: '~/scripts/calendar-events/fetch_today_events.py --help',
    createGoogleDir: 'mkdir -p ~/.google',
  },
  linux: {
    checkPython: 'python3 --version',
    installDeps: 'python3 -m pip install google-auth google-auth-oauthlib google-api-python-client',
    createScriptsDir: 'mkdir -p ~/scripts/calendar-events',
    downloadScript: `curl -o ~/scripts/calendar-events/fetch_today_events.py \\
  ${SCRIPT_URL} && chmod +x ~/scripts/calendar-events/fetch_today_events.py`,
    createCommandDir: 'mkdir -p ~/.claude/commands',
    downloadCommand: `curl -o ~/.claude/commands/daily-briefing.md \\
  ${COMMAND_URL}`,
    testScript: '~/scripts/calendar-events/fetch_today_events.py --help',
    createGoogleDir: 'mkdir -p ~/.google',
  },
  windows: {
    checkPython: 'python --version',
    installDeps: 'python -m pip install google-auth google-auth-oauthlib google-api-python-client',
    createScriptsDir: 'mkdir %USERPROFILE%\\scripts\\calendar-events',
    downloadScript: `Invoke-WebRequest -Uri "${SCRIPT_URL}" -OutFile "$env:USERPROFILE\\scripts\\calendar-events\\fetch_today_events.py"`,
    createCommandDir: 'mkdir %USERPROFILE%\\.claude\\commands',
    downloadCommand: `Invoke-WebRequest -Uri "${COMMAND_URL}" -OutFile "$env:USERPROFILE\\.claude\\commands\\daily-briefing.md"`,
    testScript: 'python %USERPROFILE%\\scripts\\calendar-events\\fetch_today_events.py --help',
    createGoogleDir: 'mkdir %USERPROFILE%\\.google',
  },
};

export function getCommands(os: OS): CommandSet {
  return commands[os];
}
