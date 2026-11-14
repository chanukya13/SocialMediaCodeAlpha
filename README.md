# Connectly

A responsive social homepage built with HTML5, modular CSS3, and vanilla JavaScript ES modules. Phase 1 is frontend only: all people and activity are fictional mock data, and nothing is sent to a backend.

## Run locally

Prerequisite: Python 3. Node.js/npm is optional, used only as a script shortcut. No dependency installation or build is needed.

```sh
cd /workspace/SocialMediaCodeAlpha
npm run dev
# Or, without Node.js:
python3 -m http.server 3000 --bind 0.0.0.0 --directory public
```

Open `http://localhost:3000`. Serve over HTTP; JavaScript modules do not work reliably by opening `index.html` directly. This static server is for development, not production deployment.

## Features

- Three-column desktop layout, tablet compact navigation, and mobile bottom navigation.
- Search people, text, or topics; For you and Following feeds; latest/popular sorting.
- Likes, bookmarks, follow toggles, expandable comments, and mock profile dialogs.
- Composer with text, emoji, and an optional local photo (JPG/PNG/WebP, up to 5 MB).
- Topic discovery, shared links to seeded posts, reduced-motion support, and keyboard navigation.
- Local images; no external fonts, assets, or services required at runtime.

Likes, follows, and bookmarks use browser localStorage where available. Posts, attached photos, and comments stay in memory and reset on reload. A new browser profile starts with Maya followed and no bookmarks. Image previews use object URLs and do not upload files. Engagement totals and profile counts are sample data.

## Structure

```text
public/
  index.html
  css/                 # Tokens, base, layout, components, responsive rules
  js/
    data/              # Fictional users, posts, and trends
    services/          # Mock data access and preference persistence
    components/        # Rendering functions
    utils/             # Icons, image recovery, escaping, feedback, scrolling
    main.js            # Application state and event handling
  assets/              # Local photos, icons, attribution, fallback
tests/
  frontend_smoke.py     # Browser interaction and layout checks
  frontend_validation.py # Edge cases, navigation, and accessibility regressions
  frontend_images.py    # Image failures, subdirectory paths, and card containment
```

Components read through `feed-service.js`. Future backend integration can replace this boundary without coupling API requests to card markup. User-provided text is escaped before rendering. There are no Express APIs, database, authentication, or login screens.

## Browser validation

This environment provides Python Playwright and Chromium. With the server running:

```sh
npm run test:browser
# Or, without npm:
python3 tests/frontend_smoke.py && python3 tests/frontend_validation.py && python3 tests/frontend_images.py
```

The runner uses installed Chromium at `/usr/bin/chromium`. Set `CHROMIUM_PATH`, `CONNECTLY_URL`, or `CONNECTLY_TEST_OUTPUT` to override browser, address, or artifact folder. Playwright is test tooling only and is not required to run the app. Screenshots and test artifacts are ignored by Git.

Photo sources are listed in [SOURCES.md](public/assets/images/SOURCES.md), with upstream license notices retained alongside them. All photos are local. Failed avatars and post photos get separate local placeholders, with an inline SVG backup if those placeholders cannot load. The recovery handler also checks static photos that failed before the main JavaScript was ready.
