# YouTube Transcript Extractor Setup Wizard Design

**Date:** 2025-12-12
**Status:** Approved

## Overview

An interactive web-based setup wizard for the YouTube Transcript Extractor that guides users through installation step-by-step. Replaces static terminal commands with a friendly, approachable experience for casual tech users, light developers, and content creators.

## Target Audience

- Casual tech users comfortable with technology but wanting streamlined setup
- Light developers who know terminal basics but prefer efficiency
- Content creators focused on technical content (coming from TikTok)

## Design Decisions

- **Format:** Interactive web wizard embedded in the docs page
- **Intelligence level:** Guided clipboard experience with OS detection and copy buttons
- **Prerequisite handling:** Self-check prompts (Yes/No buttons with install guidance)
- **Visual style:** Vertical stepper with all steps visible, current step expanded

## User Flow

### Step 1: Welcome & Prerequisites Check
- Header: "Let's get you set up! This takes about 2 minutes."
- "First, a couple quick checks..."
- "Do you have Claude Code installed?" → Yes / "Not yet"
  - If "Not yet" → "No problem! Here's how to get it..." with link, then "All set? Let's keep going →"
- "Do you have Python installed?" → Yes / "Not sure"
  - If "Not sure" → "Easy to check! Paste this in your terminal..." shows version check command

### Step 2: Install the Transcript Library
- "Now we'll add a small helper that grabs YouTube transcripts."
- Shows `pip install youtube-transcript-api` with copy button
- "Just paste this in your terminal and hit Enter. You've got this!"
- "Done" button with: "Nice! One down, two to go."

### Step 3: Download the Script
- "Next, we'll download the script that does the heavy lifting."
- Copy button with friendly "Copy to clipboard" label
- "Paste this in terminal, hit Enter, and you're golden."

### Step 4: Create the Command
- "Almost there! This last step connects everything to Claude Code."
- Copy button for command
- "One more paste-and-enter, then we'll make sure it all works."

### Step 5: Verify & Celebrate
- "Let's make sure everything's working..."
- Shows test command
- "See a bunch of JSON text? You're all set!"
- Completion: "You did it! The `/youtube` command is ready to use."

## Component Architecture

```
src/
├── components/
│   └── SetupWizard/
│       ├── SetupWizard.astro      # Main wrapper, handles layout
│       ├── WizardStep.astro       # Individual step component
│       ├── CopyButton.astro       # Reusable copy-to-clipboard
│       ├── OSDetector.astro       # Client-side OS detection
│       └── wizard.ts              # Client-side state & interactions
```

### Component Responsibilities

- **SetupWizard.astro** - Container with vertical stepper layout. Renders all 5 steps, manages active/completed states via CSS classes controlled by JavaScript.

- **WizardStep.astro** - Props: `title`, `description`, `stepNumber`. Slots for custom content (commands, buttons). Shows checkmark when completed, greys out when upcoming.

- **CopyButton.astro** - Wraps any code block. On click, copies text to clipboard and shows brief "Copied!" feedback.

- **OSDetector.astro** - Client-side script detecting macOS/Windows/Linux via `navigator.userAgent`. Stores result for OS-appropriate commands.

- **wizard.ts** - Vanilla TypeScript handling:
  - Step navigation (next/back)
  - localStorage persistence of current step
  - Yes/No button interactions
  - Marking steps complete

### Styling
Uses existing Tailwind dark theme. Active step has highlighted left border or glow effect.

## OS Detection & Command Variants

### Detection Method
On page load, checks `navigator.userAgent` and `navigator.platform` to identify OS.

### Command Variants

| Step | macOS/Linux | Windows |
|------|-------------|---------|
| Check Python | `python3 --version` | `python --version` or `py --version` |
| Install pip package | `pip install youtube-transcript-api` | Same (or `pip3` fallback) |
| Create scripts folder | `mkdir -p ~/scripts` | `mkdir %USERPROFILE%\scripts` |
| Download script | `curl -o ~/scripts/...` | `Invoke-WebRequest -Uri ... -OutFile ...` |
| Create command folder | `mkdir -p ~/.claude/commands` | `mkdir %USERPROFILE%\.claude\commands` |

### UI Behavior
- Auto-detected but user can override with "Not on [OS]? Switch to..." link
- Selected OS stored in localStorage
- Fallback: defaults to macOS if detection fails, shows switcher prominently

## Page Integration

### Structure After Integration

```
/commands/youtube.astro
├── Overview (unchanged)
├── What You'll Get (unchanged)
├── Installation → SetupWizard component
├── Usage (unchanged)
├── Output Format (unchanged)
├── Downloads (keep as fallback for power users)
├── Troubleshooting (unchanged)
```

### Entry Point
- Wizard starts collapsed with intro: "Ready to install? This takes about 2 minutes."
- "Start Setup" button expands the wizard
- Power users can scroll to Downloads section for manual install

### Completed State
- Collapses to success banner: "Installed! Scroll down to see how to use it."
- "Reset wizard" link for reinstallation

### Mobile Considerations
- Vertical stepper works well on mobile
- Touch-friendly copy buttons (larger tap targets)
- Horizontal scroll for code blocks if needed

## Edge Cases & Polish

### Stuck Users
- Each step has "Having trouble?" expandable section
- Links to Troubleshooting section
- Step 1 includes social link back to TikTok for help

### Interrupted Sessions
- localStorage saves: current step, completed steps, selected OS
- On return, wizard auto-expands to saved position
- Shows: "Welcome back! You were on step 3 of 5."

### Clipboard Failures
- Fallback: code block is selectable
- Shows "Select and copy manually" message instead of failing silently

### Accessibility
- Semantic HTML (`<ol>` with `<li>` for steps)
- `aria-label` on copy buttons
- Visible focus states for keyboard navigation
- Progress announced to screen readers

### Analytics (Optional)
- Track wizard starts, completions, drop-off points via Umami
- Identify where users get stuck

## State Persistence

Uses localStorage with the following schema:

```typescript
interface WizardState {
  currentStep: number;
  completedSteps: number[];
  selectedOS: 'macos' | 'windows' | 'linux';
  startedAt: string; // ISO timestamp
}
```
