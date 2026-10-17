# Changelog

## 0.2.0 — category packages

- Prioritize a card-based lounge-access tracker with traveler/guest eligibility, terminal feasibility, fees and planned/used visit ledgers.
- Make award cash charges and already-applied mileage discounts explicit, with dated Delta/United official-source guidance.

- Replace 31 individual provider packages with `walletfreak-hotels`, `walletfreak-flights` and `walletfreak-credit-cards`; preserve all 31 provider skills and their bundled guides.
- Move `card-travel-benefits` from core to the credit-cards category alongside the four portal skills; core retains planning, setup and the sole browser.
- Add category selection to the website, public GitHub marketplace links, provider-to-category metadata and 0.1.0 migration instructions.
- Keep provider evidence separate by provider ID and distinguish historical 0.1.0 checks from 0.2.0 results in `docs/VALIDATION.md`.

## 0.1.0 — initial provider packages

- Core card-travel-benefits skill for Hilton Aspire/Surpass and other hotel/flight cards, with shared-allowance checks and provider routing.
- Shared travel core, setup diagnostics and one pinned local Playwright MCP connection.
- 31 independently installable hotel, airline/program and card-portal plugins.
- Codex and Claude catalogs referencing the same self-contained plugin directories.
- Sourced result contract, checked redemption arithmetic and explicit privacy/transaction boundaries.
- Installation, contributor, acceptance and provider-verification documentation.

Release readiness depends on the actual results in `docs/VALIDATION.md`. Provider guidance is authored; authenticated inventory and eligibility are not certified.
