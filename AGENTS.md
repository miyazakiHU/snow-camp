# 潮風工房 — development instructions

## Direction

Continue the coastal workshop game in `index.html` and `game.js`; read `DESIGN.md`.
Preserve the original prototype's direct movement, visible material flow and on-ground investments. Do not turn it into a dashboard or tower-defense game.
The game is now an original three-island repair campaign with a repair robot, driftwood resources, workshop, shipment dock, canal and lighthouse. Do not reintroduce snow hunting, polar bears, a steak restaurant or assets copied from other games/advertisements.
The working title has not received trademark clearance. Design changes are not a legal clearance.

## Runtime and publishing

GitHub Pages publishes `main` / `/(root)`. Keep `.nojekyll`.
`index.html` is the entry point and loads `./game.js`. All asset paths must be relative so a project Pages URL works.
The WebGL renderer uses procedural geometry. Canvas 2D is a compatibility fallback with the same simulation.
There is no runtime package installation, build system, server, advertising, account system, paid service or analytics.
Never add credentials or deployment tokens to publish the game.

## CSP and Subresource Integrity

`index.html` pins the exact bytes of `game.js` in both Content Security Policy and Subresource Integrity.
After ANY change to `game.js`, run:

```sh
python tools/update_hash.py
node --check game.js
```

Commit the resulting `index.html` together with `game.js`.
Do not add `unsafe-eval`, broaden script sources or remove integrity checks to make a test pass.
Changes to inline styles do not require a JavaScript hash change.

## State and progression

The campaign uses `shiokaze_workshop_v3` plus `.backup`. Local stage state and persistent progress are saved in a single validated snapshot.
The legacy key `snowcamp_direct_v2_1` must NEVER be overwritten or deleted. A valid legacy save is recognized with tools and a fresh campaign, not a transfer of old currency/buildings.
Stage transitions reset local money, inventories, equipment and staff while preserving tools, completed islands, records and sound settings. A player chooses one tool to carry.
Keep completion and order rewards idempotent. Retain partially paid upgrades and incomplete visiting-boat orders.
Preserve conservation: money + uncollected tills + expenditure = earnings + starting grant. Harvested materials must be accounted for in inventories, shipments, repair and partial orders.
Do not spend the player's money before the first input after loading a save.

## Validation

```sh
python -m pip install playwright==1.57.0
python -m playwright install --with-deps chromium
python tests/test_game.py
```

Normal tests serve the actual entry point over local HTTP and use browser storage. They check desktop/mobile startup, WebGL and fallback, direct touch, economics, staff paths, save recovery and campaign progression.
`--in-memory` is only an explicitly labeled fallback test mode for restricted environments. It uses substitute storage and does not verify HTTP loading. Never describe it as real-device, real-storage or hosted-site verification.
Temporary test hooks must not enter production `game.js`.
Physically test iPhone/Android separately before claiming compatibility. Human playtime, enjoyment and balance still need playtesting.

## Public repository and provenance

Commit only game code, original or properly licensed assets, tests and general documentation. Do not publish conversations, personal names, private email addresses, contacts, private projects, tokens, environment files, browser saves or local absolute paths.
Keep a specific public-file allowlist; do not upload entire working directories.
Use a non-personal commit identity and a verified GitHub no-reply address when the tool supports author configuration. For connector-managed commits, check returned author metadata; never invent an account identifier or change global Git settings.
Do not change another repository or its visibility.
All runtime visuals are procedural and audio is synthesized. System fonts are used without redistribution. Review asset provenance and license obligations before adding any external material.

## Delivery

Work on a feature branch from current main and create a pull request. Do not merge automatically or directly overwrite the published branch.
Describe exactly what was tested and what was not. The user reviews and merges; Pages deploys from main.
Do not claim that the live game changed merely because a branch or pull request exists.
