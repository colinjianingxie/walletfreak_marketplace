# Unified WalletFreak implementation

The minimum install is one `walletfreak` plugin. Eight focused skills replace five packages and dozens of repetitive provider entry skills. All 31 provider references, loyalty aliases, legacy command names and verification records remain in the catalog. Browser navigation, intake and comparison contracts are shared; provider-specific eligibility, fare, award and portal rules remain distinct.

## Implemented

1. **Package migration.** Move card benefits, lounges and trip board into WalletFreak; replace individual provider skills with one catalog-driven provider-research skill. Update both host catalogs, manifests, documentation, website links and structural tests. Legacy names route through catalog aliases; the old independently installed plugins are removed during upgrade.
2. **Local travel desk.** A standard-library Python loopback server serves a plain JavaScript dashboard. It displays itineraries and findings published from the host conversation, with local shortlist/comparison selections. The separate editable personal wallet stores cards, loyalty balances, status, credits and certificates. An export includes the proposed itinerary, saved shortlist and local comparison selections with partial totals. The public website never receives these records.
3. **Guided input.** Conversation collects origin, destination alternatives, precise date-window semantics, flexibility, duration, travelers, rooms, cash budget/currency/basis and priorities. Cards, points and status are optional. The agent asks only for missing essentials; the wallet is optional.
4. **Conversation-owned planning.** Intake, clarification, research and authentication coordination remain in the host conversation. The agent publishes sanitized results directly with revision checks. The viewer has no agent controls or request queue. Deleted results cannot be recreated by a stale update.
5. **Comparable findings.** Search/filter, shortlist comparison, evidence, unknowns and proposed itinerary are interactive. Structured decimal costs remain separate by currency and points program. Mutually exclusive alternatives cannot be selected together; incomplete or unverified prices stay outside verified subtotals. Conditional credits are not automatically deducted.
6. **Account connections.** The agent opens official provider pages in the sole research browser. Users enter credentials and complete MFA/CAPTCHA there. Temporary sessions are default; an opt-in dedicated profile remembers sign-ins. Discovery connections do not take ownership; actual browser use locks the profile until that host connection ends. Restart applies mode changes; forget-all removes saved sessions on the first browser action after restarting. A dated connection observation is not a promise that a session remains valid.
7. **Branding and website.** Recover the original blue-wallet/yellow-card mascot. Bundle sourced provider artwork and restore 149 historical card images. The public site has one installation path, guided prompt examples and a fictional interactive board. Brand provenance and historical-artwork labels are included.

## Delivery and remaining boundaries

Automated tests and native integration evidence are recorded in [validation](VALIDATION.md). Existing uncommitted work was preserved in source backups before applying the migration. The revised viewer preserves old dashboard findings/selections in a one-time state.json → results.json migration and removes obsolete request/intake/account state. Existing Markdown profiles and standalone trip files remain unchanged.

The compact viewer now includes a separate password-encrypted sign-in vault, searchable wallet grids, explicit legacy-profile import and a read-only local plugin/skill browser. Autofill, reading personal SMS, provider-specific automatic MFA and autonomous background agents remain deferred. Provider sign-in still occurs on official pages; storing credentials is not an account connection. No code accesses Messages, SMS or external password stores.

Before publication, commit and publish the matching marketplace release, verify fresh public installs and provider links, then deploy the reviewed website. Live authenticated provider searches and cross-platform runtime checks remain separate from synthetic tests. No push or hosting deployment is part of this local implementation.

## Spending extension

The marketplace now has three focused packages: walletfreak retains the eight travel/wallet skills and the single local runtime; walletfreak-finance supplies spending-analysis and bank-specific guides. The core server owns the separate spending.json ledger and browser-only CSV APIs. This keeps one workspace, one browser MCP and no duplicated server. No per-bank plugins are needed. Direct browser imports never invoke a model; agent-assisted document interpretation follows host data handling.

## Current package split

Travel (`walletfreak`) owns the local runtime, private wallet, confirmation import and visual itineraries. Finance (`walletfreak-finance`) supplies statement analysis and category/month chart guidance. Shopping (`walletfreak-shopping`) supplies sourced deal research. These are three installable packages with one local workspace. The public workspace demo uses the same timeline and chart scripts as the local dashboard.
