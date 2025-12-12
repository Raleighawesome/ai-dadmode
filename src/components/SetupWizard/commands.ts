// OS-specific installation commands

export type OS = 'macos' | 'windows' | 'linux';

export interface CommandSet {
  checkPython: string;
  installPip: string;
  createScriptsDir: string;
  downloadScript: string;
  createCommandDir: string;
  downloadCommand: string;
  testScript: string;
}

const SCRIPT_URL = 'https://raw.githubusercontent.com/Raleighawesome/ai-dadmode/main/downloads/youtube_transcript_extractor.py';
const COMMAND_URL = 'https://raw.githubusercontent.com/Raleighawesome/ai-dadmode/main/downloads/youtube.md';

export const commands: Record<OS, CommandSet> = {
  macos: {
    checkPython: 'python3 --version',
    installPip: 'python3 -m pip install youtube-transcript-api',
    createScriptsDir: 'mkdir -p ~/scripts',
    downloadScript: `curl -o ~/scripts/youtube_transcript_extractor.py \\
  ${SCRIPT_URL}`,
    createCommandDir: 'mkdir -p ~/.claude/commands',
    downloadCommand: `curl -o ~/.claude/commands/youtube.md \\
  ${COMMAND_URL}`,
    testScript: 'python3 -m youtube_transcript_api',
  },
  linux: {
    checkPython: 'python3 --version',
    installPip: 'python3 -m pip install youtube-transcript-api',
    createScriptsDir: 'mkdir -p ~/scripts',
    downloadScript: `curl -o ~/scripts/youtube_transcript_extractor.py \\
  ${SCRIPT_URL}`,
    createCommandDir: 'mkdir -p ~/.claude/commands',
    downloadCommand: `curl -o ~/.claude/commands/youtube.md \\
  ${COMMAND_URL}`,
    testScript: 'python3 -m youtube_transcript_api',
  },
  windows: {
    checkPython: 'python --version',
    installPip: 'python -m pip install youtube-transcript-api',
    createScriptsDir: 'mkdir %USERPROFILE%\\scripts',
    downloadScript: `Invoke-WebRequest -Uri "${SCRIPT_URL}" -OutFile "$env:USERPROFILE\\scripts\\youtube_transcript_extractor.py"`,
    createCommandDir: 'mkdir %USERPROFILE%\\.claude\\commands',
    downloadCommand: `Invoke-WebRequest -Uri "${COMMAND_URL}" -OutFile "$env:USERPROFILE\\.claude\\commands\\youtube.md"`,
    testScript: 'python -m youtube_transcript_api',
  },
};

export function getCommands(os: OS): CommandSet {
  return commands[os];
}
