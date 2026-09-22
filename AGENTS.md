# SNOW CAMP — development instructions

## Scope and game direction
Continue the existing SNOW CAMP game in `index.html`. Do not replace it with a new application or a dashboard.
It is a browser game: move the character, collect resources, carry them, cook, sell, collect cash and stand on purchase zones to upgrade or hire workers. Preserve direct touch movement and the visible resource flow. Do not introduce tower defense or management panels without an explicit request.

## Publishing layout
This handoff uses the repository root, not a `docs/` folder.
GitHub Pages should publish `main` / `/(root)`. The game entry point is `index.html`.
Use relative paths for any new assets so a GitHub Pages project URL works.
Add an empty `.nojekyll` file at the repository root in the first maintenance change.
Do not add a build system, credentials, deployment tokens, analytics, a backend, or a paid service merely to publish the current game.

## Critical Content Security Policy requirement
The current HTML has a hash-based `Content-Security-Policy` for its inline JavaScript.
When changing any inline script, compute SHA-256 over the exact UTF-8 script text, including whitespace, then update the corresponding Base64 hash in the CSP.
Do not weaken or remove the policy merely to avoid updating a hash. Browser-test the page served over HTTP and check for CSP errors.
The current game contains its rendering code and does not require external libraries to run.

## Privacy and public repository
All repository files, branches, commit metadata and pull-request text may be public.
Commit only game code/assets and general game/development documentation.
Never publish chat transcripts, personal names, personal email addresses, contacts, private project material, access tokens, environment files, local absolute paths, browser saves or screenshots containing private account information.
Review the complete diff and staged file list before pushing; do not blindly upload a working directory.
Before creating commits, use a generic non-personal author name and a valid GitHub no-reply identity. Do not invent the account ID or change global Git settings. If no safe identity is available, report the issue before publishing.
Do not copy unrelated repositories or alter their visibility or configuration.
Existing GitHub account/profile information remains public; these instructions do not make publication anonymous.

## Development and validation
Use the existing implementation as the source of truth. Do not rely on access to a previous chat.
Preserve localStorage save compatibility or implement a migration if changing the schema.
Test a desktop viewport and a mobile-width viewport, pointer/touch movement, and the collection-to-sale loop when feasible.
Distinguish emulation from physical-device testing, and report what could not be tested.
Review JavaScript errors, CSP errors and asset paths. Avoid unrelated changes.

## Delivery workflow
Work on a feature branch based on the latest `main` and prepare a pull request targeting `main`.
Do not merge or publish unrelated changes without approval.
The user reviews the change and merges the pull request. GitHub Pages then handles deployment from `main`.
Do not claim the game is live or updated just because a PR was created. Verify the deployment status and the actual site when access is available.
