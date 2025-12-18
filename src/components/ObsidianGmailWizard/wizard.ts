// Wizard state management with localStorage persistence for Obsidian Gmail

export interface WizardState {
  currentStep: number;
  completedSteps: number[];
  selectedOS: 'macos' | 'windows' | 'linux';
  answers: Record<string, boolean>;
  startedAt: string;
}

const STORAGE_KEY = 'obsidian-gmail-wizard-state';

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
