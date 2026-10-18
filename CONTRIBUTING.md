# Contributing

Maintain one installable walletfreak plugin. Provider additions belong in providers.json and skills/provider-research/references; keep the bundled provider catalog identical to the root catalog. Preserve stable IDs, aliases and provider-specific verification records.

Seven focused skills share research, privacy and browser contracts. Avoid copying the full common contract into each provider reference. Keep links within the installed plugin valid; no imports from neighboring packages or symlinks.

Local dashboard code lives in plugins/walletfreak/scripts and assets/dashboard. Use standard-library Python and plain browser JavaScript. Agent updates and browser actions have separate authority. Any new action needs boundary validation and observable tests, including invalid inputs and interrupted requests.

Run repository unit tests, official plugin/skill validators, native Claude validation and the local dashboard browser suite. Use synthetic trip data and a temporary WALLETFREAK_DATA. Never test account login without a user-operated sign-in. Run real provider checks separately and record limits in the verification ledger.

The public website owns its checked-in provider snapshot and local assets. Sync explicitly; no runtime sibling-repository dependency. Release source and website together only after verifying published guide links. Do not deploy as part of a code-only change.
