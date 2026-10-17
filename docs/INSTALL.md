# Installation and setup

Version 0.1.0 uses the supported `.codex-plugin/plugin.json` compatibility format and Claude’s `.claude-plugin/plugin.json`. Both catalogs point to the same `plugins/` directories. Install one core and whichever providers you choose; do not install a separate Playwright server for each provider.

## Prepare a local browser

Install Node.js 18+ and Chrome. `npx` must be on the agent host’s PATH. The core pins `@playwright/mcp@0.0.68`; the first run downloads that exact package. Python 3 is optional for the bundled arithmetic helper.

The bundled configuration starts headed Chrome with `--isolated`, `--output-mode stdout` and `--codegen none`. Each host gets its own dedicated temporary profile outside the repositories. Session cookies are discarded when that browser closes; sign in again next time. Both agents can run concurrently because they have separate isolated profiles. No profile environment variables or password files are needed.

Observations are returned to the agent instead of automatically saved as snapshot/log files. They may still enter model context and host conversation history. Do not enable session recording, import/export storage state, attach your personal browser or save account screenshots by default. This is not a technical transaction firewall; skills instruct the agent to stop before transactions.

The version pin preserves this tested output behavior. A newer release must pass the profile/output checks before adoption. See [bundled browser details](../plugins/walletfreak/skills/travel-plan/references/browser.md).

## Codex

Run these commands in your shell after remote publication:

```sh
codex plugin marketplace add colinjianingxie/walletfreak_marketplace
codex plugin add walletfreak@walletfreak
codex plugin add walletfreak-united@walletfreak
codex plugin add walletfreak-hyatt@walletfreak
codex plugin add walletfreak-chase-travel@walletfreak
```

Those three providers are examples. Inspect available packages with `codex plugin list`. Start a fresh session after installation and ask for `walletfreak-setup`, then `travel-plan`. In a desktop client that supports local marketplaces, use the Plugins UI to select the WalletFreak source and install core first. CLI commands were checked against the local CLI; desktop discovery still needs its own acceptance test.

## Claude Code

In your shell:

```sh
claude plugin marketplace add colinjianingxie/walletfreak_marketplace
claude plugin install walletfreak@walletfreak
claude plugin install walletfreak-united@walletfreak
claude plugin install walletfreak-hyatt@walletfreak
claude plugin install walletfreak-chase-travel@walletfreak
```

Inside an interactive Claude session, the equivalent commands begin `/plugin marketplace add` and `/plugin install`. Restart the session, run `/walletfreak:walletfreak-setup`, then `/walletfreak:travel-plan`. Individual provider invocations include `/walletfreak-hyatt:hyatt-research`. Use `claude plugin list` to inspect installation.

## Card benefits included in core

Ask `card-travel-benefits` to evaluate your existing cards alongside flight/hotel quotes. Claude supports `/walletfreak:card-travel-benefits`. `travel-plan` and provider skills also discover it when card benefits matter. There is no extra card plugin or browser server to install. If an older local core lacks the skill, refresh core using the updating instructions and start a new session.

## Before publication / local development

The remote may have no refs during initial development. Use the absolute checkout directory as the marketplace source:

```sh
codex plugin marketplace add /absolute/path/to/walletfreak_marketplace
claude plugin marketplace add /absolute/path/to/walletfreak_marketplace
```

Then install core and providers using the same package selectors above. Provider packages must work when copied out of the checkout: no neighboring-plugin files, relative imports or symlinks may be required. Core’s skills may read their own bundled references and helper script.

## Diagnose before research

| Symptom | Recovery |
| --- | --- |
| Provider installed but core absent | Stop; install `walletfreak@walletfreak`, start a new session, load core instructions |
| Marketplace not found | Add the repository (or local checkout before publication), then retry installation |
| Installed skills missing | Check enabled status and host version, restart the session, use the namespaced Claude invocation or Codex skill picker |
| Browser tools missing | Verify core is installed/enabled, Node/npx and Chrome exist, package download works and the host permitted its MCP connection |
| Host refuses MCP tool approval | Stop the search; use a host session that can request normal approval. A noninteractive `never` policy cannot approve browser tools. Do not bypass the policy or report this as provider blocking |
| Two browser servers | Use core’s `walletfreak-browser`; do not add another server or remove unrelated integrations automatically |
| Profile already in use | Close the other WalletFreak session and verify isolated mode; do not delete lock files |
| Login/MFA/CAPTCHA | Pause for the user to complete it in the browser; never request a password or code in chat |
| Blocked provider | Stop bypass attempts; use user-supplied redacted results and label them unverified |

Successful setup requires actual host discovery of core, the selected provider, and a single functioning browser connection. A manifest validation pass alone does not establish it. Verify current installation syntax using each CLI’s help if its version differs.

## Updating

Codex: refresh the marketplace using `codex plugin marketplace upgrade walletfreak`, then use the host’s install/update UI or `codex plugin add <plugin>@walletfreak` to refresh the selected package. Claude: `claude plugin marketplace update walletfreak`, then `claude plugin update <plugin>@walletfreak`. For a local directory marketplace, edit the source and re-run `codex plugin add <plugin>@walletfreak`; `marketplace upgrade` requires a Git marketplace. Start a new session after changes. For the first coordinated release keep all catalog/manifest versions at 0.1.0; subsequent releases must update metadata consistently and repeat acceptance checks.

Sources: [OpenAI packaging](https://developers.openai.com/plugins/build/plugins), [Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference), [pinned Playwright MCP](https://github.com/microsoft/playwright-mcp/tree/v0.0.68).
