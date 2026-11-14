# Connectly Phase 1 validation

Date: 14 November 2026. Scope: existing HTML, CSS, and vanilla JavaScript frontend only.

## Final outcome

`npm run test:browser` completed successfully against the running application:

- 19 smoke-check groups passed.
- 13 additional browser regression tests passed.
- No final test failures, errors, or skips.
- All 8 JavaScript modules passed `node --check`.
- `git diff --check` passed.

The application was started using `npm run dev`. The homepage returned HTTP 200 on port 3000. An old static-server process initially held the port while returning empty responses; that exact process was stopped and restarted with output saved to `test-results/dev-server.log`. The server was verified again after the tests.

## Passed coverage

| Area | Verified behavior |
| --- | --- |
| Startup | Static server starts; homepage and local resources respond successfully. |
| Likes | Toggle both directions, totals update, and preferences survive reload. |
| Bookmarks | Save/remove, counter, bookmarks view, empty state, and persistence. |
| Comments | Expand/collapse, existing comments, new comments, count updates, whitespace rejection, 500-character input, and safe rendering of HTML-like text. |
| Follows | Follow/unfollow through discovery and profile dialogs; controls stay synchronized; Following feed updates and empty state works. |
| Composer | Whitespace cannot publish; text and emoji publish safely; length limit is respected, including selected text replacement. |
| Photos | Keyboard-operable picker; valid photo preview, removal, and publishing; oversize, incorrect type, and corrupt files rejected; valid selection works after rejection. No uploads occur. |
| Discovery | Expand/collapse all suggestions; every suggested profile opens; all four trending topics filter correctly; discovery CTA resets the filter. |
| Search and sorting | Search by person/topic/content, submit, clear, empty results, and latest/popular sorting. |
| Navigation and links | Home, Explore, Bookmarks, own profile, brand-home link, local link targets, stylesheets, icon, shared seeded-post fragment, and back-to-top. No broken application links found. |
| Sharing | Clipboard copy and copy-prompt fallback when clipboard access is denied. |
| Dialogs and notifications | Profile and About dialogs open and close with their controls, Escape, or outside click; dialogs have accessible titles; notifications toggle and dismiss on outside actions. |
| Keyboard | Skip-to-feed, search shortcut, photo picker, compact navigation names, and create-post focus. |
| Responsive layouts | Desktop, tablet, and mobile at 320–1920px widths, including breakpoint boundaries and landscape. No horizontal overflow. Desktop/tablet/mobile screenshots inspected. |
| Touch emulation | Mobile likes, comment submission, bookmark removal, bottom navigation, profile dialog, and landscape navigation. |
| Images and errors | Every shipped image decodes; normal operation needs no fallback or external requests. No uncaught JavaScript errors, browser console errors, or failed HTTP requests in the smoke run. |
| Resilience | Invalid or unavailable localStorage does not break the feed or interactions; malformed URL fragments are harmless; reduced-motion settings are respected. |

## Initial failures and fixes

Four additional regression test methods reproduced defects before the fixes; their assertions now pass:

| Defect | Fix |
| --- | --- |
| Adding the emoji to 998 characters produced 1001 characters despite the 1000-character limit. Selected text was not considered. | Calculate the resulting JavaScript string length, accounting for the selection and complete emoji; prevent insertion beyond the limit and show feedback. |
| Notifications remained open when delegated actions returned before the outside-click handler. | Run outside-click dismissal before delegated actions, keeping `aria-expanded` synchronized. |
| Compact tablet navigation and create-post buttons became unnamed when their text was hidden by responsive CSS. | Add stable accessible labels to those buttons. |
| Profile and About dialogs had no accessible names. | Link each dialog to its heading using `aria-labelledby`, including the dynamically rendered profile title. |

The test command now runs both browser suites. Smoke results are cleared at startup so an interrupted or failed run cannot leave an old passing JSON result behind. No application features were added.

## Evidence and reproduction

Keep the server running in a separate terminal:

```sh
npm run dev
```

Then run:

```sh
npm run test:browser
```

These tests use the environment's installed Chromium and Python Playwright. No dependencies were installed during this validation.

Current-instance artifacts are kept under `test-results/` and ignored by Git. They are not included in the repository. Running the suites regenerates smoke results and screenshots; console logs can be captured by redirecting test output.

- Combined final test output: `test-results/validation-final.log`
- Smoke-check JSON: `test-results/results.json`
- Before-fix regression output: `test-results/validation-before-fixes.log`
- Desktop screenshot: `test-results/connectly-1440.png`
- Tablet screenshot: `test-results/connectly-768.png`
- Mobile screenshot: `test-results/connectly-390.png`

## Remaining limitations

No unresolved functional failures were found in the tested scope. Coverage uses Chromium with desktop and mobile emulation; Safari, Firefox, and physical-device testing remain unrun. This is not a formal accessibility conformance audit.

Posts, comments, and selected photos reset on reload as designed; likes, bookmarks, and follows use browser storage when available. Profile counts and activity are mock data. No backend, authentication, database, or Phase 2 integration was added. No commits, pushes, or publication were performed during validation.
