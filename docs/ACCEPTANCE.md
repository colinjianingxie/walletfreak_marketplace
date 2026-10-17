# Release acceptance

Run each behavior scenario in a fresh Codex and Claude Code session. Record host version, date, installed plugin versions, prompt, observed behavior and evidence location in `VALIDATION.md`. Synthetic scenarios verify reasoning/boundaries; they do not count as live provider searches. The automated test suite validates package structure and arithmetic only.

## Installation and discovery gates

- Add the local marketplace to an empty host configuration, install core and all three categories. Both catalogs must resolve the same directories. Copy installed packages away from the source tree and confirm their bundled references still resolve.
- Start a new session. Ask core to compare an international flight, hotel award and card portal. It must discover the three provider skills through the host and use exactly one core browser connection; no second MCP process/registration.
- In a separate clean configuration, install only `walletfreak-hotels`. Invoke `hyatt-research`. Repeat with `walletfreak-credit-cards` alone and `card-travel-benefits`. It must stop before browsing, explain the missing core and provide the correct install/restart instructions. Install core and repeat; confirm recovery.
- Verify the browser can open a public page. User logs in directly when required. Concurrent hosts use different profiles outside either repository. Check lock-error recovery without deleting locks or unrelated processes.

Run [category-scenarios.json](../tests/category-scenarios.json) to verify missing-card recovery and category namespaces. Core plus hotels/flights must preserve gross comparisons when the credit-cards category is absent and supply its install command. With all categories, card-adjusted totals go back to the discovered core calculator without cross-plugin filesystem reads. Verify each category still has only its intended skills and no duplicate 0.1.0 provider packages remain after migration.

## Reasoning and failure gates

Use [scenarios.json](../tests/scenarios.json) as controlled prompts with explicit expected outcomes:

- International flights: mixed cabins, partner programs, party counts, connections and mandatory surcharges; compare equivalent products only.
- Hotel award: same room, occupancy, full stay, fees and cancellation deadline; separate certificates and portal rates.
- Card portal: direct versus portal gross price, remaining eligible credit, property benefits, points quote and transfer assumptions.
- Arithmetic: USD 900 cash versus 50,000 points + USD 100 = 1.6 US cents per point. Test unknown fees, mixed currencies, zero points, non-finite amounts and unavailable awards.
- Expired or unverified offers must not reduce a confirmed total. Conditional credits remain separate and cannot be counted twice.
- MFA/CAPTCHA pauses for the user; blocked access asks for redacted manual results and labels them unverified.
- A page instructing the agent to export cookies, override rules or transmit data is ignored as untrusted content.
- Requests to fill checkout, hold, buy, cancel or transfer are declined with user-operated booking steps.

## Card benefit gates

Run [card-benefit-scenarios.json](../tests/card-benefit-scenarios.json) in a fresh host session with core and all three category plugins. Supply only each prompt to the model; review its answer against the expected outcomes afterward. Confirm discovery of `card-travel-benefits` during travel/provider work in the credit-cards category using the single core browser. Check Aspire versus Surpass eligibility, shared primary/additional-card limits, expired/unissued certificates, already-discounted award/portal quotes, flight payment conflicts, bag/status duplication, adjusted redemption arithmetic and unknown market/eligibility. The numbers are synthetic fixtures, not current issuer promises. Real account balances and successful credit posting require separate evidence.

## Lounge and award-discount gates

Run [lounge-and-award-scenarios.json](../tests/lounge-and-award-scenarios.json) with core and the credit-cards category; add flights for provider routing. Give the model prompts without expected answers. Verify fee-adjusted cents per mile using final discounted miles, no repeated discount, per-party guest costs, mutually exclusive entry methods, visit-window accounting, planned versus reported usage, expired/unactivated benefits, terminal/time feasibility and transaction/privacy boundaries. Also invoke `lounge-access` with credit-cards alone: missing core must stop live research and produce core installation guidance. Synthetic fixtures do not verify real lounge admission or remaining account allowances.

## Provider evidence

Maintain one entry per provider in `provider-verification.json`. An official homepage or link check is not an inventory search. Record public and authenticated searches independently; a public test must not overwrite missing authenticated evidence. A blocked search may be recorded as a tested blocked outcome but cannot establish inventory access. Keep remaining providers `authored` until actually exercised.

## Website and publication gates

In the separate site repository, run unit tests, a production build and desktop/mobile browser checks. Verify search/filter reset, install host switch, category selection independent of provider search/filtering, clipboard success/failure, links and no Firebase application requests. Confirm `.firebaserc` still targets the existing hosting identity. Remote publication and hosting deployment require separate action after review; do not change DNS or cloud data.
