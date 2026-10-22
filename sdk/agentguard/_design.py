"""Generated offline BMD assets. Run scripts/sync_design_assets.py."""

CSS = """/* Generated from DESIGN.md v1.2.0; do not edit.
   Source SHA256: 3f92c372c69c7bbfa9f70b77b6dc4e75508cc3b5025e43a020456d0469cf5455 */
:root {
  --bmd-colors-background: #0a0a0a;
  --bmd-colors-surface: #161616;
  --bmd-colors-raised: #222222;
  --bmd-colors-border: #525252;
  --bmd-colors-control-border: #737373;
  --bmd-colors-text-primary: #f5f5f5;
  --bmd-colors-text-secondary: #b8b8b8;
  --bmd-colors-accent: #FF8200;
  --bmd-colors-on-accent: #111827;
  --bmd-colors-success: #34d399;
  --bmd-colors-warning: #fbbf24;
  --bmd-colors-danger: #f87171;
  --bmd-colors-light-background: #ffffff;
  --bmd-colors-light-surface: #f8fafc;
  --bmd-colors-light-border: #cbd5e1;
  --bmd-colors-light-control-border: #64748b;
  --bmd-colors-light-text: #111827;
  --bmd-colors-light-secondary: #475569;
  --bmd-colors-light-link: #B45309;
  --bmd-typography-display-font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
  --bmd-typography-display-font-size: 3rem;
  --bmd-typography-display-font-weight: 600;
  --bmd-typography-display-line-height: 1.15;
  --bmd-typography-h1-font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
  --bmd-typography-h1-font-size: 2rem;
  --bmd-typography-h1-font-weight: 600;
  --bmd-typography-h1-line-height: 1.2;
  --bmd-typography-h2-font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
  --bmd-typography-h2-font-size: 1.5rem;
  --bmd-typography-h2-font-weight: 600;
  --bmd-typography-h2-line-height: 1.3;
  --bmd-typography-h3-font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
  --bmd-typography-h3-font-size: 1.125rem;
  --bmd-typography-h3-font-weight: 600;
  --bmd-typography-h3-line-height: 1.4;
  --bmd-typography-body-font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
  --bmd-typography-body-font-size: 1rem;
  --bmd-typography-body-font-weight: 400;
  --bmd-typography-body-line-height: 1.6;
  --bmd-typography-secondary-font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
  --bmd-typography-secondary-font-size: 0.875rem;
  --bmd-typography-secondary-font-weight: 400;
  --bmd-typography-secondary-line-height: 1.5;
  --bmd-typography-mono-font-family: 'JetBrains Mono', ui-monospace, 'SFMono-Regular', Consolas, monospace;
  --bmd-typography-mono-font-size: 0.875rem;
  --bmd-typography-mono-font-weight: 400;
  --bmd-typography-mono-line-height: 1.6;
  --bmd-spacing-xs: 4px;
  --bmd-spacing-sm: 8px;
  --bmd-spacing-md: 16px;
  --bmd-spacing-lg: 24px;
  --bmd-spacing-xl: 32px;
  --bmd-spacing-2xl: 48px;
  --bmd-spacing-3xl: 64px;
  --bmd-rounded-none: 0px;
  --bmd-rounded-sm: 4px;
  --bmd-rounded-md: 8px;
  --bmd-motion-feedback: 150ms;
  --bmd-motion-transition: 220ms;
  --bmd-motion-easing: cubic-bezier(0.2, 0, 0, 1);
  --bmd-components-button-primary-background-color: #FF8200;
  --bmd-components-button-primary-text-color: #111827;
  --bmd-components-button-primary-rounded: 4px;
  --bmd-components-button-primary-padding: 12px 20px;
  --bmd-components-panel-background-color: #161616;
  --bmd-components-panel-text-color: #f5f5f5;
  --bmd-components-panel-rounded: 8px;
  --bmd-components-panel-padding: 24px;
  --bmd-components-email-background-color: #ffffff;
  --bmd-components-email-text-color: #111827;
  --bmd-components-email-padding: 24px;
}

/* Shared BMD presentation. Data and status semantics stay with each renderer. */
:root { color-scheme: dark; --bg:var(--bmd-colors-background); --fg:var(--bmd-colors-text-primary);
 --ink:var(--bmd-colors-text-primary); --dim:var(--bmd-colors-text-secondary);
 --muted:var(--bmd-colors-text-secondary); --line:var(--bmd-colors-border);
 --card:var(--bmd-colors-surface); --panel:var(--bmd-colors-surface);
 --red:var(--bmd-colors-danger); --green:var(--bmd-colors-success);
 --amber:var(--bmd-colors-warning); --accent:var(--bmd-colors-accent);
 --blue:var(--bmd-colors-accent); --verified:var(--bmd-colors-success);
 --claimed:var(--bmd-colors-warning); --failed:var(--bmd-colors-danger);
 --unknown:var(--bmd-colors-text-secondary); }
* { box-sizing:border-box; }
body { font-family:var(--bmd-typography-body-font-family); font-size: 16px; line-height:1.6;
 background:var(--bg); color:var(--fg); overflow-wrap:anywhere; }
.bmd-mark { width:48px; height:48px; object-fit:contain; padding:6px; flex:none; vertical-align:middle; }
.bmd-identity { display:flex; align-items:center; gap:12px; margin-bottom:24px; }
.bmd-identity h1 { margin:0; }
h1,h2,h3 { font-family:var(--bmd-typography-body-font-family); line-height:1.3; }
h1 { font-size:clamp(1.75rem,4vw,2.25rem); }
h2 { font-size:1.5rem; margin-top:32px; }
h3 { font-size:1.125rem; }
p { max-width:66ch; }
a { color:var(--accent); text-underline-offset:3px; }
button,summary { font-family:inherit; min-height:44px; }
:focus-visible { outline:2px solid var(--accent); outline-offset:4px; }
code,pre,.mono { font-family:var(--bmd-typography-mono-font-family); }
pre { overflow:auto; max-width:100%; font-size:14px; }
.wrap { max-width:1200px; margin-inline:auto; }
.card,.stat,.panel,.metric { border-radius:8px; }
.sub,.note,.panel,.badge,.tag,small,footer { font-size:14px; }
.stat .l,th { font-size:14px; text-transform:none; letter-spacing:normal; }
.scroll,.table-wrap { overflow:auto; max-width:100%; }
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation:none!important; transition:none!important; scroll-behavior:auto!important; } }
@media(max-width:600px) { body { padding:16px; } .bmd-identity { gap:8px; } .card,.panel { padding:16px; } }

table,td { font-size:14px; }
"""

LOGO = (
    '<img class="bmd-mark" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAACXB'
    'IWXMAAAsTAAALEwEAmpwYAAAgAElEQVR4nO2d+ZNW1bWG8/OCpmWMMgZBaMY4BQkq0ggIibFEoigiYqsRARVDVFSM0QYkYXJqiwj'
    'EUokpJTSIUsggMjVzQw8MMimD/h371jq55HKRobu/r8/a++znh7cqlUTkvOtZ67zfOXvv8zMRcQgPYAAGYAAGYECi8uBn1n8BhAc'
    'wAAMwAAMwIAQAIGAQwAAMwAAMwIDwBAAIGAQwAAMwAAMwILwCAAIGAQzAAAzAAAwIawCAgEEAAzAAAzAAA8IiQCBgEMAADMAADMC'
    'AsAsACBgEMAADMAADMCBsAwQCBgEMwAAMwIDgAecAAAGDAAZgAAZgQCL0gIOAPCgCwgMYgAEYgAEhAAABgwAGYAAGYAAGhCcAQMA'
    'ggAEYgAEYgAHhFQAQMAhgAAZgAAZgQFgDAAQMAhiAARiAARgQFgECAYMABmAABmAABoRdAEDAIIABGIABGIABYRsgEDAIYAAGYAA'
    'GJHoPOAcACKJvAhiAARiAAYnQAwKAB0VAeAADMAADMCAEACBgEMAADMAADMCA8AQACBgEMAADMAADMCC8AgACBgEMwAAMwAAMCGs'
    'AgIBBAAMwAAMwAAPCIkAgYBDAAAzAAAzAgLALAAgYBDAAAzAAAzAgbAMEAgYBDMAADMCARO8B5wAAQfRNAAMwAAMwIBF6QADwoAg'
    'ID2AABmAABoQAAAQMAhiAARiAARgQngAAAYMABmAABmAABoRXAEDAIIABGIABGIAB1gAAAYMABmAABmAABhyLAIGAQQADMAADMAA'
    'Djl0AQMAggAEYgAEYgAHHNkAgYBDAAAzAAAwIHnAOABAwCGAABmAABiQ+DwgAHhQB4QEMwAAMwIAQAICAQQADMAADMAADwhMAIGA'
    'QwAAMwAAMwIDwCgAIGAQwAAMwAAMwIKwBAAIGAQzAAAzAAAwIiwCBgEEAAzAAAzAAA8IuACBgEMAADMAADMCAsA0QCBgEMAADMAA'
    'DEr0HnAMABNE3AQzAAAzAgEToAQHAgyIgPIABGIABGBACABAwCGAABmAABmCAJwBAwCCAARiAARiAAccrACBgEMAADMAADMCAYw0'
    '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" width="48" height="48" alt="">'
)
