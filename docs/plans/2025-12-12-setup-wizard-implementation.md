# YouTube Setup Wizard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an interactive vertical stepper wizard that guides non-technical users through installing the YouTube Transcript Extractor.

**Architecture:** Astro components with vanilla TypeScript for client-side interactivity. State persisted in localStorage. OS detection via navigator.userAgent for platform-specific commands.

**Tech Stack:** Astro 5, Tailwind CSS 4, vanilla TypeScript (no framework dependencies)

---

## Task 1: Create CopyButton Component

**Files:**
- Create: `src/components/SetupWizard/CopyButton.astro`

**Step 1: Create the component file**

Create the CopyButton component that wraps a code snippet with a copy-to-clipboard button:

```astro
---
interface Props {
  code: string;
  label?: string;
}

const { code, label = 'Copy to clipboard' } = Astro.props;
const id = `copy-${Math.random().toString(36).slice(2, 9)}`;
---

<div class="copy-wrapper relative group">
  <pre class="code-block pr-12"><code id={id}>{code}</code></pre>
  <button
    type="button"
    class="copy-btn absolute top-2 right-2 p-2 rounded-md bg-surface-elevated border border-border hover:border-accent transition-colors"
    data-copy-target={id}
    aria-label={label}
  >
    <svg class="w-4 h-4 copy-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
    <svg class="w-4 h-4 check-icon hidden text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
    </svg>
  </button>
</div>

<style>
  .copy-wrapper .check-icon { display: none; }
  .copy-wrapper.copied .copy-icon { display: none; }
  .copy-wrapper.copied .check-icon { display: block; }
</style>

<script>
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const targetId = btn.getAttribute('data-copy-target');
      const codeEl = document.getElementById(targetId!);
      if (!codeEl) return;

      try {
        await navigator.clipboard.writeText(codeEl.textContent || '');
        const wrapper = btn.closest('.copy-wrapper');
        wrapper?.classList.add('copied');
        setTimeout(() => wrapper?.classList.remove('copied'), 2000);
      } catch {
        // Fallback: select the text
        const range = document.createRange();
        range.selectNodeContents(codeEl);
        const sel = window.getSelection();
        sel?.removeAllRanges();
        sel?.addRange(range);
      }
    });
  });
</script>
```

**Step 2: Verify the file was created**

Run: `ls -la src/components/SetupWizard/`

Expected: `CopyButton.astro` exists

**Step 3: Build to verify no syntax errors**

Run: `npm run build`

Expected: Build succeeds with no errors

**Step 4: Commit**

```bash
git add src/components/SetupWizard/CopyButton.astro
git commit -m "feat(wizard): add CopyButton component with clipboard support"
```

---

## Task 2: Create WizardStep Component

**Files:**
- Create: `src/components/SetupWizard/WizardStep.astro`

**Step 1: Create the component file**

Create the WizardStep component for individual steps in the wizard:

```astro
---
interface Props {
  stepNumber: number;
  title: string;
  description: string;
  status?: 'upcoming' | 'current' | 'completed';
}

const { stepNumber, title, description, status = 'upcoming' } = Astro.props;
---

<div
  class:list={[
    'wizard-step',
    'relative pl-12 pb-8 border-l-2',
    {
      'border-border opacity-50': status === 'upcoming',
      'border-accent': status === 'current',
      'border-green-500': status === 'completed',
    }
  ]}
  data-step={stepNumber}
  data-status={status}
>
  <!-- Step indicator circle -->
  <div
    class:list={[
      'absolute -left-[13px] w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium',
      {
        'bg-surface border-2 border-border text-text-muted': status === 'upcoming',
        'bg-accent border-2 border-accent text-white': status === 'current',
        'bg-green-500 border-2 border-green-500 text-white': status === 'completed',
      }
    ]}
  >
    {status === 'completed' ? (
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
    ) : (
      stepNumber
    )}
  </div>

  <!-- Step content -->
  <div class="step-header mb-4">
    <h3 class="text-lg font-semibold text-text-primary">{title}</h3>
    <p class="text-sm text-text-secondary">{description}</p>
  </div>

  <div class:list={['step-content', { 'hidden': status === 'upcoming' }]}>
    <slot />
  </div>
</div>
```

**Step 2: Build to verify no syntax errors**

Run: `npm run build`

Expected: Build succeeds

**Step 3: Commit**

```bash
git add src/components/SetupWizard/WizardStep.astro
git commit -m "feat(wizard): add WizardStep component with status indicators"
```

---

## Task 3: Create Wizard State Management (TypeScript)

**Files:**
- Create: `src/components/SetupWizard/wizard.ts`

**Step 1: Create the TypeScript state management file**

```typescript
// Wizard state management with localStorage persistence

export interface WizardState {
  currentStep: number;
  completedSteps: number[];
  selectedOS: 'macos' | 'windows' | 'linux';
  answers: Record<string, boolean>;
  startedAt: string;
}

const STORAGE_KEY = 'youtube-wizard-state';

export function detectOS(): 'macos' | 'windows' | 'linux' {
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes('win')) return 'windows';
  if (ua.includes('mac')) return 'macos';
  return 'linux';
}

export function getDefaultState(): WizardState {
  return {
    currentStep: 0,
    completedSteps: [],
    selectedOS: detectOS(),
    answers: {},
    startedAt: new Date().toISOString(),
  };
}

export function loadState(): WizardState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored) as WizardState;
    }
  } catch {
    // Ignore parse errors
  }
  return getDefaultState();
}

export function saveState(state: WizardState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore storage errors
  }
}

export function resetState(): WizardState {
  localStorage.removeItem(STORAGE_KEY);
  return getDefaultState();
}

export function completeStep(state: WizardState, step: number): WizardState {
  const newState = {
    ...state,
    completedSteps: [...new Set([...state.completedSteps, step])],
    currentStep: step + 1,
  };
  saveState(newState);
  return newState;
}

export function setAnswer(state: WizardState, key: string, value: boolean): WizardState {
  const newState = {
    ...state,
    answers: { ...state.answers, [key]: value },
  };
  saveState(newState);
  return newState;
}

export function setOS(state: WizardState, os: 'macos' | 'windows' | 'linux'): WizardState {
  const newState = { ...state, selectedOS: os };
  saveState(newState);
  return newState;
}
```

**Step 2: Build to verify TypeScript compiles**

Run: `npm run build`

Expected: Build succeeds

**Step 3: Commit**

```bash
git add src/components/SetupWizard/wizard.ts
git commit -m "feat(wizard): add state management with localStorage persistence"
```

---

## Task 4: Create OS-Specific Commands Data

**Files:**
- Create: `src/components/SetupWizard/commands.ts`

**Step 1: Create the commands data file**

```typescript
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
```

**Step 2: Build to verify**

Run: `npm run build`

Expected: Build succeeds

**Step 3: Commit**

```bash
git add src/components/SetupWizard/commands.ts
git commit -m "feat(wizard): add OS-specific command definitions"
```

---

## Task 5: Create Main SetupWizard Component

**Files:**
- Create: `src/components/SetupWizard/SetupWizard.astro`

**Step 1: Create the main wizard component**

```astro
---
import CopyButton from './CopyButton.astro';
---

<div id="setup-wizard" class="wizard-container my-8">
  <!-- Collapsed state (before starting) -->
  <div id="wizard-intro" class="card text-center py-8">
    <h3 class="text-xl font-semibold text-text-primary mb-2">Ready to install?</h3>
    <p class="text-text-secondary mb-6">This takes about 2 minutes. We'll guide you through each step.</p>
    <button id="start-wizard-btn" class="btn-primary">
      Start Setup
    </button>
  </div>

  <!-- Welcome back state -->
  <div id="wizard-resume" class="card text-center py-8 hidden">
    <h3 class="text-xl font-semibold text-text-primary mb-2">Welcome back!</h3>
    <p class="text-text-secondary mb-6">You were on step <span id="resume-step">1</span> of 5.</p>
    <div class="flex justify-center gap-4">
      <button id="continue-wizard-btn" class="btn-primary">Continue</button>
      <button id="restart-wizard-btn" class="btn-secondary">Start Over</button>
    </div>
  </div>

  <!-- Active wizard -->
  <div id="wizard-steps" class="hidden">
    <!-- OS Selector -->
    <div class="mb-6 flex items-center gap-2 text-sm">
      <span class="text-text-muted">Showing commands for:</span>
      <select id="os-selector" class="bg-surface border border-border rounded px-2 py-1 text-text-primary">
        <option value="macos">macOS</option>
        <option value="linux">Linux</option>
        <option value="windows">Windows</option>
      </select>
    </div>

    <!-- Step 1: Prerequisites -->
    <div class="wizard-step" data-step="1">
      <div class="step-indicator">
        <div class="step-number">1</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <h3 class="step-title">Let's check a couple things first</h3>
        <p class="step-description">First, a couple quick checks...</p>

        <div class="prereq-check my-4" data-prereq="claude">
          <p class="mb-3">Do you have <strong>Claude Code</strong> installed?</p>
          <div class="flex gap-3">
            <button class="btn-secondary prereq-yes" data-answer="claude-yes">Yes</button>
            <button class="btn-secondary prereq-no" data-answer="claude-no">Not yet</button>
          </div>
          <div class="prereq-help hidden mt-4 p-4 bg-surface rounded-lg border border-border">
            <p class="text-text-secondary mb-3">No problem! Here's how to get it:</p>
            <a href="https://docs.anthropic.com/en/docs/claude-code" target="_blank" class="text-accent hover:underline">
              Install Claude Code →
            </a>
            <button class="btn-primary mt-4 prereq-continue">All set? Let's keep going →</button>
          </div>
        </div>

        <div class="prereq-check my-4 hidden" data-prereq="python">
          <p class="mb-3">Do you have <strong>Python 3.8+</strong> installed?</p>
          <div class="flex gap-3">
            <button class="btn-secondary prereq-yes" data-answer="python-yes">Yes</button>
            <button class="btn-secondary prereq-no" data-answer="python-no">Not sure</button>
          </div>
          <div class="prereq-help hidden mt-4 p-4 bg-surface rounded-lg border border-border">
            <p class="text-text-secondary mb-3">Easy to check! Paste this in your terminal:</p>
            <div id="check-python-cmd"></div>
            <p class="text-text-secondary mt-3 text-sm">If you see a version number (like "Python 3.11.4"), you're good! If not, <a href="https://www.python.org/downloads/" target="_blank" class="text-accent hover:underline">download Python here</a>.</p>
            <button class="btn-primary mt-4 prereq-continue">All set? Let's keep going →</button>
          </div>
        </div>

        <button class="step-done-btn btn-primary hidden mt-4" data-next="2">
          Nice! Let's continue →
        </button>
      </div>
    </div>

    <!-- Step 2: Install pip package -->
    <div class="wizard-step opacity-50" data-step="2">
      <div class="step-indicator">
        <div class="step-number">2</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <h3 class="step-title">Install the transcript library</h3>
        <p class="step-description">Now we'll add a small helper that grabs YouTube transcripts.</p>

        <div class="step-body hidden">
          <p class="text-text-secondary mb-4">Just paste this in your terminal and hit Enter. You've got this!</p>
          <div id="install-pip-cmd"></div>
          <button class="step-done-btn btn-primary mt-6" data-next="3">
            Done - one down, two to go!
          </button>
        </div>
      </div>
    </div>

    <!-- Step 3: Download script -->
    <div class="wizard-step opacity-50" data-step="3">
      <div class="step-indicator">
        <div class="step-number">3</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <h3 class="step-title">Download the script</h3>
        <p class="step-description">Next, we'll download the script that does the heavy lifting.</p>

        <div class="step-body hidden">
          <p class="text-text-secondary mb-4">Paste this in terminal, hit Enter, and you're golden.</p>
          <div id="download-script-cmd"></div>
          <button class="step-done-btn btn-primary mt-6" data-next="4">
            Done - almost there!
          </button>
        </div>
      </div>
    </div>

    <!-- Step 4: Create command -->
    <div class="wizard-step opacity-50" data-step="4">
      <div class="step-indicator">
        <div class="step-number">4</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <h3 class="step-title">Create the Claude command</h3>
        <p class="step-description">Almost there! This last step connects everything to Claude Code.</p>

        <div class="step-body hidden">
          <p class="text-text-secondary mb-4">One more paste-and-enter, then we'll make sure it all works.</p>
          <div id="download-command-cmd"></div>
          <button class="step-done-btn btn-primary mt-6" data-next="5">
            Done - let's verify it works!
          </button>
        </div>
      </div>
    </div>

    <!-- Step 5: Verify -->
    <div class="wizard-step opacity-50" data-step="5">
      <div class="step-indicator">
        <div class="step-number">5</div>
        <div class="step-line"></div>
      </div>
      <div class="step-content">
        <h3 class="step-title">Verify installation</h3>
        <p class="step-description">Let's make sure everything's working...</p>

        <div class="step-body hidden">
          <p class="text-text-secondary mb-4">Run this test command:</p>
          <div id="test-script-cmd"></div>
          <p class="text-text-secondary mt-4 text-sm">See a bunch of JSON text? You're all set!</p>
          <button class="step-done-btn btn-primary mt-6" data-next="complete">
            It works! Complete setup
          </button>

          <details class="mt-4">
            <summary class="text-text-muted cursor-pointer hover:text-text-secondary">Having trouble?</summary>
            <div class="mt-2 p-4 bg-surface rounded-lg border border-border text-sm">
              <p class="text-text-secondary">Common issues:</p>
              <ul class="list-disc list-inside mt-2 text-text-muted space-y-1">
                <li>Make sure Python is in your PATH</li>
                <li>Try <code>python</code> instead of <code>python3</code></li>
                <li>Check that the script file exists in ~/scripts/</li>
              </ul>
            </div>
          </details>
        </div>
      </div>
    </div>
  </div>

  <!-- Completed state -->
  <div id="wizard-complete" class="hidden">
    <div class="card text-center py-8 border-green-500/50">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
        <svg class="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h3 class="text-xl font-semibold text-text-primary mb-2">You did it!</h3>
      <p class="text-text-secondary mb-4">The <code>/youtube</code> command is ready to use.</p>
      <p class="text-text-muted text-sm">Scroll down to see usage examples.</p>
      <button id="reset-wizard-btn" class="text-text-muted text-sm mt-4 hover:text-text-secondary underline">
        Reset wizard
      </button>
    </div>
  </div>
</div>

<style>
  .wizard-step {
    display: flex;
    gap: 1rem;
    padding-bottom: 1.5rem;
  }

  .step-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex-shrink: 0;
  }

  .step-number {
    width: 2rem;
    height: 2rem;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    background-color: var(--color-surface);
    border: 2px solid var(--color-border);
    color: var(--color-text-muted);
  }

  .wizard-step.active .step-number {
    background-color: var(--color-accent);
    border-color: var(--color-accent);
    color: white;
  }

  .wizard-step.completed .step-number {
    background-color: #22c55e;
    border-color: #22c55e;
    color: white;
  }

  .step-line {
    width: 2px;
    flex-grow: 1;
    background-color: var(--color-border);
    margin-top: 0.5rem;
  }

  .wizard-step.completed .step-line {
    background-color: #22c55e;
  }

  .wizard-step:last-child .step-line {
    display: none;
  }

  .step-content {
    flex-grow: 1;
    padding-bottom: 1rem;
  }

  .step-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 0.25rem;
  }

  .step-description {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .wizard-step.active {
    opacity: 1;
  }

  .wizard-step.active .step-body {
    display: block !important;
  }
</style>

<script>
  import { loadState, saveState, resetState, detectOS, type WizardState } from './wizard.ts';
  import { getCommands } from './commands.ts';
  import CopyButton from './CopyButton.astro';

  // DOM Elements
  const wizardIntro = document.getElementById('wizard-intro');
  const wizardResume = document.getElementById('wizard-resume');
  const wizardSteps = document.getElementById('wizard-steps');
  const wizardComplete = document.getElementById('wizard-complete');
  const osSelector = document.getElementById('os-selector') as HTMLSelectElement;
  const resumeStepSpan = document.getElementById('resume-step');

  let state: WizardState;

  function init() {
    state = loadState();

    // Check if returning user
    if (state.currentStep > 0 && state.currentStep <= 5) {
      wizardIntro?.classList.add('hidden');
      wizardResume?.classList.remove('hidden');
      if (resumeStepSpan) resumeStepSpan.textContent = String(state.currentStep);
    } else if (state.currentStep > 5) {
      showComplete();
    }

    // Set OS selector
    if (osSelector) {
      osSelector.value = state.selectedOS;
    }

    updateCommands();
    bindEvents();
  }

  function updateCommands() {
    const cmds = getCommands(state.selectedOS);

    // Update command displays
    updateCommandDisplay('check-python-cmd', cmds.checkPython);
    updateCommandDisplay('install-pip-cmd', cmds.installPip);
    updateCommandDisplay('download-script-cmd', `${cmds.createScriptsDir} && ${cmds.downloadScript}`);
    updateCommandDisplay('download-command-cmd', `${cmds.createCommandDir} && ${cmds.downloadCommand}`);
    updateCommandDisplay('test-script-cmd', cmds.testScript);
  }

  function updateCommandDisplay(id: string, code: string) {
    const container = document.getElementById(id);
    if (container) {
      // Create a simple code block with copy functionality
      container.innerHTML = `
        <div class="copy-wrapper relative group">
          <pre class="code-block pr-12 text-sm"><code>${escapeHtml(code)}</code></pre>
          <button
            type="button"
            class="copy-btn absolute top-2 right-2 p-2 rounded-md bg-surface-elevated border border-border hover:border-accent transition-colors"
            data-code="${escapeAttr(code)}"
            aria-label="Copy to clipboard"
          >
            <svg class="w-4 h-4 copy-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <svg class="w-4 h-4 check-icon hidden text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </button>
        </div>
      `;

      // Bind copy event
      const btn = container.querySelector('.copy-btn');
      btn?.addEventListener('click', async () => {
        const code = btn.getAttribute('data-code') || '';
        try {
          await navigator.clipboard.writeText(code);
          const wrapper = btn.closest('.copy-wrapper');
          wrapper?.classList.add('copied');
          setTimeout(() => wrapper?.classList.remove('copied'), 2000);
        } catch {
          // Fallback handled by CSS
        }
      });
    }
  }

  function escapeHtml(str: string): string {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function escapeAttr(str: string): string {
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function bindEvents() {
    // Start wizard
    document.getElementById('start-wizard-btn')?.addEventListener('click', () => {
      state = { ...state, currentStep: 1, startedAt: new Date().toISOString() };
      saveState(state);
      showWizard();
    });

    // Continue wizard
    document.getElementById('continue-wizard-btn')?.addEventListener('click', showWizard);

    // Restart wizard
    document.getElementById('restart-wizard-btn')?.addEventListener('click', () => {
      state = resetState();
      state.currentStep = 1;
      saveState(state);
      showWizard();
    });

    // Reset wizard
    document.getElementById('reset-wizard-btn')?.addEventListener('click', () => {
      state = resetState();
      wizardComplete?.classList.add('hidden');
      wizardIntro?.classList.remove('hidden');
    });

    // OS selector
    osSelector?.addEventListener('change', () => {
      state.selectedOS = osSelector.value as 'macos' | 'windows' | 'linux';
      saveState(state);
      updateCommands();
    });

    // Prereq yes/no buttons
    document.querySelectorAll('.prereq-yes').forEach(btn => {
      btn.addEventListener('click', () => {
        const check = btn.closest('.prereq-check');
        check?.classList.add('hidden');
        showNextPrereq(check);
      });
    });

    document.querySelectorAll('.prereq-no').forEach(btn => {
      btn.addEventListener('click', () => {
        const check = btn.closest('.prereq-check');
        check?.querySelector('.prereq-help')?.classList.remove('hidden');
        btn.closest('.flex')?.classList.add('hidden');
      });
    });

    document.querySelectorAll('.prereq-continue').forEach(btn => {
      btn.addEventListener('click', () => {
        const check = btn.closest('.prereq-check');
        check?.classList.add('hidden');
        showNextPrereq(check);
      });
    });

    // Step done buttons
    document.querySelectorAll('.step-done-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const nextStep = btn.getAttribute('data-next');
        if (nextStep === 'complete') {
          state.currentStep = 6;
          state.completedSteps = [1, 2, 3, 4, 5];
          saveState(state);
          showComplete();
        } else {
          const next = parseInt(nextStep || '1');
          state.currentStep = next;
          state.completedSteps = [...new Set([...state.completedSteps, next - 1])];
          saveState(state);
          updateStepStates();
        }
      });
    });
  }

  function showNextPrereq(currentCheck: Element | null) {
    if (currentCheck?.getAttribute('data-prereq') === 'claude') {
      const pythonCheck = document.querySelector('[data-prereq="python"]');
      pythonCheck?.classList.remove('hidden');
    } else {
      // All prereqs done, show done button
      const doneBtn = currentCheck?.closest('.step-content')?.querySelector('.step-done-btn');
      doneBtn?.classList.remove('hidden');
    }
  }

  function showWizard() {
    wizardIntro?.classList.add('hidden');
    wizardResume?.classList.add('hidden');
    wizardSteps?.classList.remove('hidden');
    updateStepStates();
  }

  function showComplete() {
    wizardIntro?.classList.add('hidden');
    wizardResume?.classList.add('hidden');
    wizardSteps?.classList.add('hidden');
    wizardComplete?.classList.remove('hidden');
  }

  function updateStepStates() {
    document.querySelectorAll('.wizard-step').forEach(step => {
      const stepNum = parseInt(step.getAttribute('data-step') || '0');

      step.classList.remove('active', 'completed', 'opacity-50');

      if (state.completedSteps.includes(stepNum)) {
        step.classList.add('completed');
        step.querySelector('.step-body')?.classList.remove('hidden');
      } else if (stepNum === state.currentStep) {
        step.classList.add('active');
        step.querySelector('.step-body')?.classList.remove('hidden');
      } else {
        step.classList.add('opacity-50');
      }
    });
  }

  // Initialize on load
  init();
</script>
```

**Step 2: Build to verify**

Run: `npm run build`

Expected: Build succeeds

**Step 3: Commit**

```bash
git add src/components/SetupWizard/SetupWizard.astro
git commit -m "feat(wizard): add main SetupWizard component with full flow"
```

---

## Task 6: Integrate Wizard into YouTube Page

**Files:**
- Modify: `src/pages/commands/youtube.astro`

**Step 1: Update the youtube.astro page**

Replace the static Installation section with the SetupWizard component. The file should look like this:

```astro
---
import DocsLayout from '../../layouts/DocsLayout.astro';
import SetupWizard from '../../components/SetupWizard/SetupWizard.astro';
---

<DocsLayout
  title="YouTube Transcript Extractor"
  description="Extract YouTube transcripts and create summarized Obsidian notes with Claude Code"
  category="Command"
>
  <h2>Overview</h2>

  <p>
    The <code>/youtube</code> command extracts transcripts from any YouTube video and creates
    a structured Obsidian note with an AI-generated summary, key takeaways, and the full transcript.
  </p>

  <h2>What You'll Get</h2>

  <ul>
    <li><strong>Executive Summary</strong> - 2-3 paragraph overview of the video content</li>
    <li><strong>Key Takeaways</strong> - Bullet points of the most important insights</li>
    <li><strong>Notable Quotes</strong> - Memorable quotes with timestamps</li>
    <li><strong>Topics Covered</strong> - List of main themes discussed</li>
    <li><strong>Full Transcript</strong> - Complete transcript in a collapsible section</li>
  </ul>

  <h2 id="installation">Installation</h2>

  <SetupWizard />

  <h2 id="usage">Usage</h2>

  <p>In Claude Code, run the command with a YouTube URL:</p>

  <pre><code>/youtube https://www.youtube.com/watch?v=VIDEO_ID</code></pre>

  <p>Claude will:</p>

  <ol>
    <li>Extract the transcript from the video</li>
    <li>Generate a comprehensive summary</li>
    <li>Create a structured Obsidian note</li>
    <li>Save it to your <code>youtube/</code> folder</li>
  </ol>

  <h3>Supported URL Formats</h3>

  <ul>
    <li><code>https://www.youtube.com/watch?v=VIDEO_ID</code></li>
    <li><code>https://youtu.be/VIDEO_ID</code></li>
    <li><code>https://www.youtube.com/embed/VIDEO_ID</code></li>
  </ul>

  <h2 id="output">Output Format</h2>

  <p>The generated Obsidian note follows this structure:</p>

  <pre><code>---
title: Video Title Here
source: https://www.youtube.com/watch?v=VIDEO_ID
video_id: VIDEO_ID
type: video
tags:
  - youtube
  - topic-tag
  - another-tag
created: 2025-12-11
---

# Video Title Here

## Summary
A concise 2-3 paragraph summary of the main content...

## Key Takeaways
&gt; [!important]
&gt; - First key insight
&gt; - Second key insight
&gt; - Third key insight

## Notable Quotes
&gt; "Quote from the video" (timestamp)

## Topics Covered
- Topic 1
- Topic 2
- Topic 3

## Full Transcript
&lt;details&gt;
&lt;summary&gt;Click to expand full transcript&lt;/summary&gt;

Full transcript text here...

&lt;/details&gt;</code></pre>

  <h2 id="downloads">Downloads</h2>

  <p>Prefer to install manually? Download the files directly:</p>

  <div class="flex flex-wrap gap-4 my-6 not-prose">
    <a
      href="/downloads/youtube_transcript_extractor.py"
      download
      class="download-btn"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      youtube_transcript_extractor.py
    </a>
    <a
      href="/downloads/youtube.md"
      download
      class="download-btn"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      youtube.md (Claude Command)
    </a>
  </div>

  <h2>Troubleshooting</h2>

  <h3>Error: Transcripts are disabled for this video</h3>
  <p>
    Some videos have transcripts disabled by the uploader. Try a different video,
    or check if the video has auto-generated captions available.
  </p>

  <h3>Error: No transcript found</h3>
  <p>
    The video may not have any captions available. This is common for very new videos
    or videos in languages without auto-caption support.
  </p>

  <h3>Error: youtube-transcript-api not installed</h3>
  <p>
    Run <code>pip install youtube-transcript-api</code> to install the required dependency.
  </p>

  <h3>Command not found: /youtube</h3>
  <p>
    Make sure the <code>youtube.md</code> file is in your <code>~/.claude/commands/</code> directory
    and restart Claude Code.
  </p>
</DocsLayout>
```

**Step 2: Build and verify**

Run: `npm run build`

Expected: Build succeeds, 2 pages built

**Step 3: Test locally**

Run: `npm run dev`

Open: `http://localhost:4321/commands/youtube`

Verify: Wizard displays with "Ready to install?" card

**Step 4: Commit**

```bash
git add src/pages/commands/youtube.astro
git commit -m "feat(wizard): integrate SetupWizard into YouTube docs page"
```

---

## Task 7: Add Wizard-Specific CSS to Global Styles

**Files:**
- Modify: `src/styles/global.css`

**Step 1: Add wizard styles to global.css**

Add these styles at the end of the file, inside `@layer components`:

```css
  /* Setup Wizard styles */
  .wizard-step .copy-wrapper .check-icon { display: none; }
  .wizard-step .copy-wrapper.copied .copy-icon { display: none; }
  .wizard-step .copy-wrapper.copied .check-icon { display: block; }

  .bg-surface-elevated {
    background-color: var(--color-surface-elevated);
  }

  .border-green-500\/50 {
    border-color: rgb(34 197 94 / 0.5);
  }

  .bg-green-500\/20 {
    background-color: rgb(34 197 94 / 0.2);
  }

  .text-green-400 {
    color: #4ade80;
  }
```

**Step 2: Build and verify**

Run: `npm run build`

Expected: Build succeeds

**Step 3: Commit**

```bash
git add src/styles/global.css
git commit -m "feat(wizard): add wizard-specific CSS utilities"
```

---

## Task 8: Manual Testing & Final Polish

**Files:**
- None (testing only)

**Step 1: Start dev server**

Run: `npm run dev`

**Step 2: Test the full wizard flow**

1. Open `http://localhost:4321/commands/youtube`
2. Click "Start Setup"
3. Complete each step (click Yes for prerequisites)
4. Verify OS switching works (change dropdown)
5. Verify copy buttons work
6. Complete to the success screen
7. Click "Reset wizard" and verify it resets

**Step 3: Test localStorage persistence**

1. Start wizard, complete step 1
2. Refresh the page
3. Verify "Welcome back" screen appears with correct step number
4. Click "Continue" and verify correct step is active

**Step 4: Test mobile responsiveness**

1. Open browser DevTools
2. Toggle device toolbar (mobile view)
3. Verify wizard is usable on small screens

**Step 5: Production build and verify**

Run: `npm run build && npm run preview`

Open: `http://localhost:4321/commands/youtube`

Verify: Wizard works in production build

**Step 6: Final commit**

If any fixes were needed, commit them:

```bash
git add -A
git commit -m "fix(wizard): polish and bug fixes from manual testing"
```

---

## Task 9: Merge to Main

**Step 1: Verify all tests pass**

Run: `npm run build`

Expected: Build succeeds with no errors

**Step 2: Create summary of changes**

Review commits:

```bash
git log main..HEAD --oneline
```

**Step 3: Merge or create PR**

Option A - Direct merge (if you have permissions):
```bash
git checkout main
git merge feature/setup-wizard
git push
```

Option B - Create PR:
```bash
git push -u origin feature/setup-wizard
gh pr create --title "feat: interactive setup wizard for YouTube command" --body "..."
```

---

## Summary

This implementation creates:

1. **CopyButton** - Reusable clipboard component
2. **WizardStep** - Step indicator with status states
3. **wizard.ts** - State management with localStorage
4. **commands.ts** - OS-specific command definitions
5. **SetupWizard** - Main wizard component with full flow
6. Integration into the YouTube docs page
7. CSS utilities for wizard styling

The wizard guides users through 5 steps with friendly language, OS detection, and persistent state.
