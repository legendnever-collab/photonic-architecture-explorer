import { syncMedia } from './media';
import type { DesignDocument, PortName, Preset, Result, ScenarioEntry } from './types';

export interface AppState {
  doc: DesignDocument;
  presets: Preset[];
  scenarios: ScenarioEntry[];
  preview: Result | null;
  result: Result | null;     // last design for `resultFor`
  resultFor: string | null;  // JSON of the document the result belongs to
  selected: string | null;   // candidate id
  activePort: PortName | null;
  busy: boolean;
  error: string | null;
}

type Listener = (state: AppState, changed: Set<keyof AppState>) => void;

export class Store {
  private listeners: Listener[] = [];
  constructor(public state: AppState) {}

  subscribe(listener: Listener) {
    this.listeners.push(listener);
  }

  set(patch: Partial<AppState>) {
    if (patch.doc) patch = { ...patch, doc: syncMedia(patch.doc) };
    const changed = new Set(Object.keys(patch) as (keyof AppState)[]);
    this.state = { ...this.state, ...patch };
    for (const listener of this.listeners) listener(this.state, changed);
  }

  /** True when the shown design result was computed for the current document. */
  get resultIsCurrent(): boolean {
    return this.state.result !== null && this.state.resultFor === JSON.stringify(this.state.doc);
  }

  get currentResult(): Result | null {
    return this.resultIsCurrent ? this.state.result : null;
  }

  get selectedCandidate() {
    const result = this.currentResult;
    if (!result) return null;
    return result.candidates.find((c) => c.id === this.state.selected) ?? result.candidates[0] ?? null;
  }
}

export const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
