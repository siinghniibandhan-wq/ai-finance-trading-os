# Theme migration — remaining work and review notes

## Confirmed work on `theme-tokens`
- The supplied theme migration stylesheets remain as provided; the assistant's broad colour substitutions have been reverted.
- `theme-tokens.css` contains the theme token contract and 18 theme selectors.
- Startup theme initialisation, removal of the deprecated Glass theme entry, and deletion of the two deprecated override stylesheets remain.
- Build and theme audit are configured in GitHub Actions.

## Remaining verification
- Run the build and audit against the latest commit.
- Review `!important` declarations individually; do not remove them wholesale because cascade and visual behaviour may change.
- Verify the 18 themes visually, including light themes, Playground, instrument details, holdings, and Buy/Sell flows.

All work remains on `theme-tokens`. Do not merge to `main` until verification is complete.
