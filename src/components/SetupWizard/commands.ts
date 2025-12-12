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
    installPip: 'pip3 install youtube-transcript-api',
    createScriptsDir: 'mkdir -p ~/scripts',
    downloadScript: `curl -o ~/scripts/youtube_transcript_extractor.py \\
  ${SCRIPT_URL}`,
    createCommandDir: 'mkdir -p ~/.claude/commands',
    downloadCommand: `curl -o ~/.claude/commands/youtube.md \\
  ${COMMAND_URL}`,
    testScript: 'python3 ~/scripts/youtube_transcript_extractor.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"',
  },
  linux: {
    checkPython: 'python3 --version',
    installPip: 'pip3 install youtube-transcript-api',
    createScriptsDir: 'mkdir -p ~/scripts',
    downloadScript: `curl -o ~/scripts/youtube_transcript_extractor.py \\
  ${SCRIPT_URL}`,
    createCommandDir: 'mkdir -p ~/.claude/commands',
    downloadCommand: `curl -o ~/.claude/commands/youtube.md \\
  ${COMMAND_URL}`,
    testScript: 'python3 ~/scripts/youtube_transcript_extractor.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"',
  },
  windows: {
    checkPython: 'python --version',
    installPip: 'pip install youtube-transcript-api',
    createScriptsDir: 'mkdir %USERPROFILE%\\scripts',
    downloadScript: `Invoke-WebRequest -Uri "${SCRIPT_URL}" -OutFile "$env:USERPROFILE\\scripts\\youtube_transcript_extractor.py"`,
    createCommandDir: 'mkdir %USERPROFILE%\\.claude\\commands',
    downloadCommand: `Invoke-WebRequest -Uri "${COMMAND_URL}" -OutFile "$env:USERPROFILE\\.claude\\commands\\youtube.md"`,
    testScript: 'python %USERPROFILE%\\scripts\\youtube_transcript_extractor.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"',
  },
};

export function getCommands(os: OS): CommandSet {
  return commands[os];
}
