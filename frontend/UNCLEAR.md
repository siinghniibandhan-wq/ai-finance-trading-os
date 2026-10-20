# Theme migration — remaining work and review notes

## Completed on `theme-tokens`
- Added `src/theme-tokens.css` with 18 theme selectors, shared chart/control tokens, and semantic status-colour tokens.
- Added `src/theme-components.css` for theme-aware surfaces and controls.
- Updated startup imports and applied the saved theme slug before React renders.
- Removed the deprecated `Glass` theme entry and corrected the gallery count to 18. `Glassmorphism` and `Liquid Glass` remain.
- Removed imports and files for the deprecated instrument-contrast and holdings-dark-card override stylesheets.
- Added build + theme audit to GitHub Actions and extended the audit for theme startup, the 18-theme list, and deprecated imports.
- Replaced repeated semantic success/danger/warning colours in `App.jsx` with shared tokens.

## Not yet safe to call complete
- Literal colour values in `App.jsx`, `styles.css`, `visual-design.css`, `theme-fixes.css`, and `theme-styles.css` have been moved behind named tokens in `theme-tokens.css`. Values are currently preserved to avoid an unreviewed visual redesign; the next step is to consolidate these into semantic, theme-specific tokens.
- The CSS still contains many `!important` declarations. They have **not** been removed automatically because removing them wholesale can change cascade and theme behaviour; these need selector-by-selector review.
- The audit now checks that colour declarations outside `theme-tokens.css` do not contain literal hex/RGB/HSL values, in addition to theme registration, token presence, selected component selectors, startup wiring, CSS brace balance, and BUY/SELL regression guards. Confirm this audit passes on the latest commit.
- Browser visual/accessibility checks across all 18 themes have not been run from this workflow. Build success alone does not prove visual parity.

## Required before merge
1. Finish context-aware colour tokenisation in the remaining CSS and inline styles.
2. Expand the audit to fail on disallowed colour literals outside the approved token file, with explicit exceptions for semantic/status data where needed.
3. Run build + audit after the final migration changes.
4. Smoke-test light themes, dark themes, Playground, instrument details, holdings, Buy/Sell flows, login and landing-page first paint.
5. Keep all work on `theme-tokens`; do not merge to `main` until all checks pass.

No transaction calculations, routes, API calls, or backend logic were intentionally changed by these theme-only edits.
