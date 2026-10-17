# Installation and setup

Version 0.2.0 uses the supported `.codex-plugin/plugin.json` compatibility format and Claude’s `.claude-plugin/plugin.json`. Both catalogs point to the same `plugins/` directories. Install one core and whichever categories you choose; do not install a separate Playwright server for each provider.

## Prepare a local browser

Install Node.js 18+ and Chrome. `npx` must be on the agent host’s PATH. The core pins `@playwright/mcp@0.0.68`; the first run downloads that exact package. Python 3 is optional for the bundled arithmetic helper.

The bundled configuration starts headed Chrome with `--isolated`, `--output-mode stdout` and `--codegen none`. Each host gets its own dedicated temporary profile outside the repositories. Session cookies are discarded when that browser closes; sign in again next time. Both agents can run concurrently because they have separate isolated profiles. No profile environment variables or password files are needed.

Observations are returned to the agent instead of automatically saved as snapshot/log files. They may still enter model context and host conversation history. Do not enable session recording, import/export storage state, attach your personal browser or save account screenshots by default. This is not a technical transaction firewall; skills instruct the agent to stop before transactions.

The version pin preserves this tested output behavior. A newer release must pass the profile/output checks before adoption. See [bundled browser details](../plugins/walletfreak/skills/travel-plan/references/browser.md).

## Codex

Run these commands in your shell using the public GitHub marketplace:

```sh
codex plugin marketplace add colinjianingxie/walletfreak_marketplace
codex plugin add walletfreak@walletfreak
codex plugin add walletfreak-hotels@walletfreak
codex plugin add walletfreak-flights@walletfreak
codex plugin add walletfreak-credit-cards@walletfreak
```

The three category plugins are optional; each includes all of its provider skills. Inspect available packages with `codex plugin list`. Start a fresh session after installation and ask for `walletfreak-setup`, then `travel-plan`. In a desktop client that supports local marketplaces, use the Plugins UI to select the WalletFreak source and install core first. CLI commands were checked against the local CLI; desktop discovery still needs its own acceptance test.

## Claude Code

In your shell:

```sh
claude plugin marketplace add colinjianingxie/walletfreak_marketplace
claude plugin install walletfreak@walletfreak
claude plugin install walletfreak-hotels@walletfreak
claude plugin install walletfreak-flights@walletfreak
claude plugin install walletfreak-credit-cards@walletfreak
```

Inside an interactive Claude session, the equivalent commands begin `/plugin marketplace add` and `/plugin install`. Restart the session, run `/walletfreak:walletfreak-setup`, then `/walletfreak:travel-plan`. Provider skill invocations include `/walletfreak-hotels:hyatt-research`. Use `claude plugin list` to inspect installation.

## Card benefits in the credit-cards category

Ask `card-travel-benefits` to evaluate your existing cards alongside flight/hotel quotes. Claude supports `/walletfreak-credit-cards:card-travel-benefits`. `travel-plan` and provider skills also discover it when card benefits matter. Install `walletfreak-credit-cards@walletfreak` for this skill; it reuses core’s browser. Core alone does not provide card-benefit research in 0.2.0. Without it, hotel/flight comparisons can continue at gross prices with card savings explicitly unverified.

## Lounge tracking

With core and `walletfreak-credit-cards` installed, ask for `lounge-access` (Claude: `/walletfreak-credit-cards:lounge-access`). Supply card products/countries, airports/terminals, travel times and guests; only share remaining visits or pass expiry when relevant. The skill keeps a conversation ledger of eligibility, fees and planned versus used visits. It does not enroll you, reserve entry or monitor your account automatically.

## Local development

To try changes before they are pushed, use the absolute checkout directory as the marketplace source:

```sh
codex plugin marketplace add /absolute/path/to/walletfreak_marketplace
claude plugin marketplace add /absolute/path/to/walletfreak_marketplace
```

Then install core and categories using the same package selectors above. Category packages must work when copied out of the checkout: no neighboring-plugin files, relative imports or symlinks may be required. Core’s skills may read their own bundled references and helper script.

## Diagnose before research

| Symptom | Recovery |
| --- | --- |
| Category installed but core absent | Stop; install `walletfreak@walletfreak`, start a new session, load core instructions |
| Marketplace not found | Add the repository (or local checkout for development), then retry installation |
| Installed skills missing | Check enabled status and host version, restart the session, use the namespaced Claude invocation or Codex skill picker |
| Browser tools missing | Verify core is installed/enabled, Node/npx and Chrome exist, package download works and the host permitted its MCP connection |
| Host refuses MCP tool approval | Stop the search; use a host session that can request normal approval. A noninteractive `never` policy cannot approve browser tools. Do not bypass the policy or report this as provider blocking |
| Two browser servers | Use core’s `walletfreak-browser`; do not add another server or remove unrelated integrations automatically |
| Profile already in use | Close the other WalletFreak session and verify isolated mode; do not delete lock files |
| Login/MFA/CAPTCHA | Pause for the user to complete it in the browser; never request a password or code in chat |
| Blocked provider | Stop bypass attempts; use user-supplied redacted results and label them unverified |

Successful setup requires actual host discovery of core, the selected provider, and a single functioning browser connection. A manifest validation pass alone does not establish it. Verify current installation syntax using each CLI’s help if its version differs.

## Updating

Codex: refresh the marketplace using `codex plugin marketplace upgrade walletfreak`, then use the host’s install/update UI or `codex plugin add <plugin>@walletfreak` to refresh the selected package. Claude: `claude plugin marketplace update walletfreak`, then `claude plugin update <plugin>@walletfreak`. For a local directory marketplace, edit the source and re-run `codex plugin add <plugin>@walletfreak`; `marketplace upgrade` requires a Git marketplace. Start a new session after changes. Keep all manifests and catalog metadata on 0.2.0 for this category release; subsequent releases must update metadata consistently and repeat acceptance checks.

## Upgrading from 0.1.0

The individual provider packages were replaced, not aliased. Skill names such as `hilton-research` stay the same; their plugin namespaces change. This is a source/package migration, not a change to your travel accounts.

| Previous installation | Replacement |
| --- | --- |
| Any hotel provider, e.g. `walletfreak-hilton`, `walletfreak-hyatt` | `walletfreak-hotels` |
| Any airline provider, e.g. `walletfreak-united`, `walletfreak-delta` | `walletfreak-flights` |
| Any portal, e.g. `walletfreak-chase-travel`, `walletfreak-amex-travel` | `walletfreak-credit-cards` |
| Core’s `card-travel-benefits` skill | `walletfreak-credit-cards` plus updated core |

1. Refresh the marketplace with the updating command above. Reinstall/update `walletfreak@walletfreak` and install the desired category plugins using the commands above. Users who relied on card benefits in 0.1.0 core need the credit-cards category.
2. Inspect `codex plugin list` or `claude plugin list`. Remove only the retired WalletFreak provider plugins you actually installed, for example `codex plugin remove walletfreak-hilton@walletfreak` or `claude plugin uninstall walletfreak-hilton@walletfreak`. Do not remove core, the new categories or unrelated plugins. Updating the catalog does not automatically remove cached old packages.
3. Start a fresh session and run `walletfreak-setup`. Confirm one core, the intended categories, no duplicate legacy skills, and one shared browser. Claude invocations now include `/walletfreak-hotels:hilton-research`, `/walletfreak-flights:united-research` and `/walletfreak-credit-cards:card-travel-benefits`.

Sources: [OpenAI packaging](https://developers.openai.com/plugins/build/plugins), [Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference), [pinned Playwright MCP](https://github.com/microsoft/playwright-mcp/tree/v0.0.68).
