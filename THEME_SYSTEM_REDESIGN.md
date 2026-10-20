# Financial OS — Theme System Redesign

## Source and scope

- Base: `main` at the time the redesign branch was created.
- Working branch: `refactor/theme-design-system`.
- Scope: frontend appearance/theme architecture only. Preserve finance, tax, market-data, broker, account, and transaction behaviour.
- Do not merge to `main` or deploy until review and verification.

## Initial source audit (2026-10-20)

The current UI registers **17 selectable themes** in `frontend/src/App.jsx`:
Default, Light, Dark, Aurora, Emerald, Ocean, Sunset, Minimal, Retro Terminal, Glass, Neumorphism, Claymorphism, Brutalism, Maximalism, Liquid Glass, Bento Grid, Elegant Plain.

The stylesheet source also contains stale theme selectors for Skeuomorphism, Glassmorphism, and Neomorphism even though those are not in the current selector list. This creates ambiguity between the supported theme registry and legacy styling.

Current CSS footprint:
- `theme-unify.css`: 22 lines, 7,816 characters; defines central `--th-*` tokens.
- `theme-styles.css`: 4,809 lines, 1,341 `!important` declarations.
- `theme-fixes.css`: 3,618 lines, 972 `!important` declarations.
- `visual-design.css`: 3,383 lines, 536 `!important` declarations.
- `styles.css`: 2,860 lines.
- `instrument-interaction-contrast.css`: 50 lines.
- `holdings-dark-cards.css`: 96 lines.

The main stylesheet imports seven CSS files, with `theme-unify.css` last. Loading central tokens last does not override component rules that set concrete colours, nor does it resolve conflicts between legacy `--t-*`, `--finos-*`, and `--th-*` systems. The large number of important overrides and obsolete selectors are confirmed maintenance risks.

## Proposed intentional theme lineup

Keep a smaller, visibly differentiated set:
1. **Default** — preserve the existing Financial OS identity.
2. **Dark** — neutral low-glare charcoal, distinct from Default.
3. **Neumorphism** — tactile raised/inset surfaces, carefully preserved readable contrast.
4. **Brutalism** — hard edges, bold ink borders, high-contrast accent, offset shadows.
5. **Retro Terminal** — black/green phosphor palette, monospace, terminal-like controls.
6. **Elegant Plain** — restrained editorial typography, quiet surfaces, thin separators.
7. **Bento Grid** — modular, intentionally varied grid/card hierarchy.
8. **Nordic** *(new)* — calm, light stone/ice palette, clear spacing and subtle blue/teal accents.
9. **Editorial** *(new)* — warm paper/ink palette, refined typography and restrained accent colour.

This lineup preserves the user's named favourites and keeps Default and Dark as independent designs—not visual references. Other similar or redundant variants are candidates for removal from the selector. Legacy selector cleanup must be coordinated with the registry and tests.

## Component inventory to implement

### Foundations
- Page/canvas background, app shell, navigation/sidebar, overlays and modal backdrop.
- Surface levels: primary, raised/card, nested/inset, floating/popover, disabled.
- Text: primary, secondary, muted, inverse, link, placeholder, disabled.
- Borders: subtle, standard, strong, focus, selected, danger.
- Shape/depth: radius scale, shadow/elevation, inset/raised effect, blur/transparency.
- Typography: family, size/weight hierarchy, line height, numeric/data typography.

### Shared components
- Buttons: primary, secondary, quiet/ghost, outline, danger, icon-only, loading/disabled.
- Tabs: container, inactive, active, hover, focus, disabled.
- Form controls: text/number/date inputs, select/dropdown, checkbox, radio, toggle, textarea.
- Search: field, action button, results list, empty state.
- Cards/panels: base, interactive, summary/metric, chart, nested section.
- Tables: header, row, zebra/hover, selected, empty/loading.
- Badges/chips/status labels, alerts/toasts, tooltips, popovers, dialogs/drawers.
- Icons: default, muted, accent, positive, negative, warning, interactive/disabled; inherit theme semantics.
- Charts: surface, axis, grid, tooltip, legend, series palette, positive/negative series.
- Feedback: validation errors, success/warning/info, loading skeletons, empty/error states.
- Responsive layout and keyboard/focus states.

## Architecture rules

1. Theme registry is the single source of truth for available themes and their labels/slugs/descriptions.
2. Each theme owns a complete token set: palette, semantic roles, typography, shape, border, elevation, and interaction states.
3. Shared components consume semantic component tokens, not individual theme names or hard-coded palette values.
4. Module CSS may define layout/size only unless a component genuinely needs a documented semantic variant. It must not independently redefine theme colours for common components.
5. A documented exception is allowed only where the component's domain meaning or visual identity genuinely requires it (e.g. financial positive/negative data); the exception must still use semantic theme tokens.
6. No foreground/background pair may collapse to the same colour. Text, meaningful icons, controls, and selected/focus indicators must remain perceivable.
7. Distinct visual languages remain distinct; consistency means shared component semantics and behaviour, not identical appearance across themes.

## Verification / acceptance criteria

- Only supported themes appear in the theme selector; stored removed-theme values safely migrate to a supported fallback.
- Every supported theme defines every required token (no silent missing-token fallback).
- Same component type has consistent geometry and state semantics across modules within a theme.
- Changing one theme token updates all applicable components without module-specific edits.
- Check text contrast against WCAG guidance (4.5:1 normal text, 3:1 large text; meaningful controls/icons 3:1 against adjacent colours).
- Test default, hover, selected, keyboard focus, disabled, error, loading, and empty states.
- Run static theme audit, production build, and available regression tests.
- Browser verification must be reported separately from static checks; do not claim visual verification without running it.
- Preserve application logic and data flows; no financial/business behaviour changes.
- Keep the work on the redesign branch until reviewed. Do not merge/deploy automatically.
