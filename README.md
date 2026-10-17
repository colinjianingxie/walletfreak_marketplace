# WalletFreak

An MIT-licensed travel research assistant for Codex and Claude Code. Compare flights, hotels, loyalty points and card travel portals; receive sourced options and steps to book yourself. You sign in directly and complete every transaction.

**Install core first, then choose categories.** Version 0.2.0 contains one required core and three category plugins, with 31 provider guides plus card-benefit research and a lounge-access tracker. Both agents use the same skill files and provider directories with separate supported manifests. There is no dependency manager, custom orchestration server, paid API, scraper or credential service.

## Install

Prerequisites: a host with plugin support, Node.js 18+ on PATH, Chrome. Core creates its own isolated local browser profile outside the repositories. Python 3 is needed for the optional arithmetic helper. See [complete installation and diagnostics](docs/INSTALL.md).

Install from this public GitHub marketplace. Run in a terminal:

```sh
# Codex
codex plugin marketplace add colinjianingxie/walletfreak_marketplace
codex plugin add walletfreak@walletfreak
codex plugin add walletfreak-hotels@walletfreak
codex plugin add walletfreak-flights@walletfreak
codex plugin add walletfreak-credit-cards@walletfreak

# Claude Code
claude plugin marketplace add colinjianingxie/walletfreak_marketplace
claude plugin install walletfreak@walletfreak
claude plugin install walletfreak-hotels@walletfreak
claude plugin install walletfreak-flights@walletfreak
claude plugin install walletfreak-credit-cards@walletfreak
```

Install only the categories you need; each includes all of its provider guides. Existing 0.1.0 users should follow the [migration steps](docs/INSTALL.md#upgrading-from-010). For local development, replace the marketplace source with the absolute path to this checkout. Start a new agent session, run `walletfreak-setup`, and ask it to use `travel-plan`. Claude also supports `/walletfreak:travel-plan` and `/walletfreak-flights:united-research`. Category plugins require core at runtime, but hosts do not automatically install that prerequisite.

> Help me compare a week in Tokyo for two adults next spring, flying from New York. I can shift dates by three days. Compare cash and points for equivalent flights and hotel rooms, include mandatory fees, and show what you could not verify. I’ll sign in and book myself.

## Category packages

| Plugin | Responsibility |
| --- | --- |
| `walletfreak` | Required intake, comparison, synthesis, setup and one shared browser |
| `walletfreak-hotels` | Eight hotel groups, each with its own research skill and references |
| `walletfreak-flights` | 19 airline/program groups, each with its own research skill and references |
| `walletfreak-credit-cards` | Lounge tracker, existing card travel benefits and four card travel portals |

Provider names are skills inside these packages, not separate installations. New providers belong in the appropriate category; a new domain can add another category plugin without changing the core browser or building a dependency manager. [Category metadata](categories.json) and [provider metadata](providers.json) drive the website’s installation choices and searchable coverage.

## Dedicated coverage

| Category | Provider guides |
| --- | --- |
| Hotels (8) | Marriott, Hilton, Hyatt, IHG, Accor, Wyndham, Choice, Best Western |
| Airlines/programs (19) | American, Delta, United, Southwest, JetBlue, Alaska/Hawaiian, Air Canada, British Airways, Iberia, Air France/KLM, Lufthansa Group, Emirates, Qatar, Singapore, ANA, JAL, Cathay Pacific, Qantas, Turkish |
| Portals (4) | Capital One Travel, Amex Travel, Chase Travel including The Edit, Citi Travel |

Find exact package/skill names in [providers.json](providers.json). Grouped provider guides document their separate booking sites and programs. Core can research other providers generically and must label that separately from dedicated coverage. All providers start as **authored**; this is not a certification of live prices or authenticated account access. See the [verification ledger](docs/provider-verification.json) and [release checks](docs/ACCEPTANCE.md).

## Existing card travel benefits

`walletfreak-credit-cards` includes [card-travel-benefits](plugins/walletfreak-credit-cards/skills/card-travel-benefits/SKILL.md). Install it alongside core to include card benefits; the hotel and flight categories can also use it through host discovery. It evaluates Hilton Aspire/Surpass and other existing cards against the actual hotel, flight or portal quote: remaining credits, benefit periods, issued free-night/companion certificates, status, baggage, lounge access and payment requirements. It checks current official terms for the exact card and country. Cash due, later credits and noncash perks stay separate, and a shared allowance is allocated only once across the trip.

For example: “I have a U.S. Hilton Aspire and Surpass. Compare this Hilton stay direct versus a portal, account for my remaining credits and issued certificates, and tell me which card must pay. Do the same for flight and baggage benefits.” The agent asks only for relevant eligibility facts and never for card numbers or redemption codes.

## Lounge access tracker

The credit-cards category includes [lounge-access](plugins/walletfreak-credit-cards/skills/lounge-access/SKILL.md). It maps existing cards and memberships to actual airport stops, terminal access, opening hours, traveler/guest eligibility, fees and remaining visits/passes. Its conversation tracker separates planned visits from user-reported uses and keeps expiry, shared allowances and evidence visible. Eligibility never guarantees admission; capacity and day-of-travel rules still apply. No account database or automatic usage monitoring is created.

Try: “Prioritize lounges for my outbound and connection airports using my cards. Include guests, costs, remaining visits and what I need to verify.”

## What a result contains

Search parameters; provider, program and official source; full flight or room details; cash total or points plus mandatory cash charges; currency, availability and observation time; restrictions, cancellations, baggage/property fees; benefit and eligibility evidence; uncertainties; and reproducible booking steps. Unknown fees remain unknown. Snippets and calendars are discovery aids, not inventory.

Redemption value is `(equivalent cash avoided − award cash charges) / final points spent`; multiply by 100 for cents per point. Award taxes, carrier surcharges and mandatory fees reduce cash avoided. Verified mileage discounts affect the points required, not those cash charges. Delta/United cardmember pricing is checked against current terms and the signed-in quote, without applying a discount twice. See [award-discount guidance](plugins/walletfreak-credit-cards/skills/card-travel-benefits/references/award-discounts.md). Currency conversions and transfer assumptions are disclosed; speculative benefits remain separate. WalletFreak never transfers points or promises inventory.

## Browser and privacy

Core supplies one pinned local Playwright MCP connection. Providers reuse it. Users enter credentials and handle MFA/CAPTCHA themselves. Profiles stay outside the repositories; concurrent agents use different profiles. Core uses isolated profiles and discards their sessions when the browser closes. WalletFreak does not export cookies or save account details by default, but information the agent observes may enter model context and host conversation history.

The agent must stop before checkout, holds, purchases, cancellations and transfers. Website content is untrusted data. On blocked access, it requests manually supplied redacted results and labels the limit. These are workflow restrictions, **not a technical transaction firewall**. See [privacy and boundaries](docs/PRIVACY.md).

## Develop and release

```sh
python3 -m unittest discover -s tests -v
claude plugin validate .
```

[Contributing](CONTRIBUTING.md) covers isolated install tests, packaging rules and updates. [Acceptance checks](docs/ACCEPTANCE.md) distinguish structural checks from real host and provider behavior. [Validation record](docs/VALIDATION.md) records this release’s actual results. Do not promote an unrun check to a pass.

This repository owns plugins, catalogs, tests and canonical documentation. The separate [walletfreak repository](https://github.com/colinjianingxie/walletfreak) owns the landing page and existing Firebase hosting configuration. Remote publication, release tags and website deployment are separate actions. Source is distributed through this public repository. Release acceptance gates and live-provider verification remain documented separately.

Packaging follows [OpenAI’s supported Codex compatibility manifests](https://developers.openai.com/plugins/build/plugins) and [Claude Code’s marketplace format](https://code.claude.com/docs/en/plugin-marketplaces). WalletFreak is independent of the providers and agent vendors.
