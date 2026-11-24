import type { DesignDocument, Preset, Result, ScenarioEntry, WhatIfResult } from './types';

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return (await response.json()) as T;
}

export const api = {
  presets: async () => (await json<{ presets: Preset[] }>(await fetch('api/presets'))).presets,
  scenarios: async () => (await json<{ scenarios: ScenarioEntry[] }>(await fetch('api/scenarios'))).scenarios,
  scenario: async (id: string) => json<DesignDocument>(await fetch(`api/scenarios/${encodeURIComponent(id)}`)),
  preview: async (doc: DesignDocument) => post('api/preview', doc),
  design: async (doc: DesignDocument) => post('api/design', doc),
  whatif: async (doc: DesignDocument) => json<WhatIfResult>(await fetch('api/whatif', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(doc) })),
};

async function post(path: string, doc: DesignDocument): Promise<Result> {
  return json<Result>(await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(doc) }));
}
