# WalletFreak

An MIT-licensed travel research assistant for Codex and Claude Code. Compare flights, hotels, loyalty points and card travel portals; receive sourced options and steps to book yourself. You sign in directly and complete every transaction.

**Install core first, then choose providers.** Version 0.1.0 contains one required core and 31 independent provider plugins. Both agents use the same skill files and provider directories with separate supported manifests. There is no dependency manager, custom orchestration server, paid API, scraper or credential service.

## Install

Prerequisites: a host with plugin support, Node.js 18+ on PATH, Chrome. Core creates its own isolated local browser profile outside the repositories. Python 3 is needed for the optional arithmetic helper. See [complete installation and diagnostics](docs/INSTALL.md).

After this repository has been published, run in a terminal:

```sh
# Codex
codex plugin marketplace add colinjianingxie/walletfreak_marketplace
codex plugin add walletfreak@walletfreak
codex plugin add walletfreak-marriott@walletfreak
codex plugin add walletfreak-united@walletfreak

# Claude Code
claude plugin marketplace add colinjianingxie/walletfreak_marketplace
claude plugin install walletfreak@walletfreak
claude plugin install walletfreak-marriott@walletfreak
claude plugin install walletfreak-united@walletfreak
```

Marriott and United are examples; install only what you need. For local development, replace the marketplace source with the absolute path to this checkout. Start a new agent session, run `walletfreak-setup`, and ask it to use `travel-plan`. Claude also supports `/walletfreak:travel-plan` and `/walletfreak-united:united-research`. Providers require core at runtime, but hosts do not automatically install that prerequisite.

> Help me compare a week in Tokyo for two adults next spring, flying from New York. I can shift dates by three days. Compare cash and points for equivalent flights and hotel rooms, include mandatory fees, and show what you could not verify. I’ll sign in and book myself.

## Dedicated coverage

| Category | Plugins |
| --- | --- |
| Hotels (8) | Marriott, Hilton, Hyatt, IHG, Accor, Wyndham, Choice, Best Western |
| Airlines/programs (19) | American, Delta, United, Southwest, JetBlue, Alaska/Hawaiian, Air Canada, British Airways, Iberia, Air France/KLM, Lufthansa Group, Emirates, Qatar, Singapore, ANA, JAL, Cathay Pacific, Qantas, Turkish |
| Portals (4) | Capital One Travel, Amex Travel, Chase Travel including The Edit, Citi Travel |

Find exact package/skill names in [providers.json](providers.json). Grouped plugins document their separate booking sites and programs. Core can research other providers generically and must label that separately from dedicated coverage. All providers start as **authored**; this is not a certification of live prices or authenticated account access. See the [verification ledger](docs/provider-verification.json) and [release checks](docs/ACCEPTANCE.md).

## Existing card travel benefits

Core includes [card-travel-benefits](plugins/walletfreak/skills/card-travel-benefits/SKILL.md); no extra plugin is needed. It evaluates Hilton Aspire/Surpass and other existing cards against the actual hotel, flight or portal quote: remaining credits, benefit periods, issued free-night/companion certificates, status, baggage, lounge access and payment requirements. It checks current official terms for the exact card and country. Cash due, later credits and noncash perks stay separate, and a shared allowance is allocated only once across the trip.

For example: “I have a U.S. Hilton Aspire and Surpass. Compare this Hilton stay direct versus a portal, account for my remaining credits and issued certificates, and tell me which card must pay. Do the same for flight and baggage benefits.” The agent asks only for relevant eligibility facts and never for card numbers or redemption codes.

## What a result contains

Search parameters; provider, program and official source; full flight or room details; cash total or points plus mandatory cash charges; currency, availability and observation time; restrictions, cancellations, baggage/property fees; benefit and eligibility evidence; uncertainties; and reproducible booking steps. Unknown fees remain unknown. Snippets and calendars are discovery aids, not inventory.

Redemption value is `(equivalent cash avoided − award cash charges) / points spent`. Currency conversions and transfer assumptions are disclosed; speculative benefits remain separate. WalletFreak never transfers points or promises inventory.

## Browser and privacy

Core supplies one pinned local Playwright MCP connection. Providers reuse it. Users enter credentials and handle MFA/CAPTCHA themselves. Profiles stay outside the repositories; concurrent agents use different profiles. Core uses isolated profiles and discards their sessions when the browser closes. WalletFreak does not export cookies or save account details by default, but information the agent observes may enter model context and host conversation history.

The agent must stop before checkout, holds, purchases, cancellations and transfers. Website content is untrusted data. On blocked access, it requests manually supplied redacted results and labels the limit. These are workflow restrictions, **not a technical transaction firewall**. See [privacy and boundaries](docs/PRIVACY.md).

## Develop and release

```sh
python3 -m unittest discover -s tests -v
claude plugin validate .
```

[Contributing](CONTRIBUTING.md) covers isolated install tests, packaging rules and updates. [Acceptance checks](docs/ACCEPTANCE.md) distinguish structural checks from real host and provider behavior. [Validation record](docs/VALIDATION.md) records this release’s actual results. Do not promote an unrun check to a pass.

This repository owns plugins, catalogs, tests and canonical documentation. The separate [walletfreak repository](https://github.com/colinjianingxie/walletfreak) owns the landing page and existing Firebase hosting configuration. Remote publication, release tags and website deployment are separate actions. The local 0.1.0 preparation does not publish anything.

Packaging follows [OpenAI’s supported Codex compatibility manifests](https://developers.openai.com/plugins/build/plugins) and [Claude Code’s marketplace format](https://code.claude.com/docs/en/plugin-marketplaces). WalletFreak is independent of the providers and agent vendors.
