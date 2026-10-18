---
name: walletfreak-setup
description: "Set up the unified WalletFreak plugin, open its private local dashboard, choose temporary or remembered sign-ins, and diagnose browser/session conflicts in Codex or Claude Code."
---

# Setup

This plugin contains every provider guide, profiles, card benefits, lounges and the trip board. No category plugins are required. Check Python 3.10+, Node.js 18+ and Chrome. Use only the bundled walletfreak-browser connection. Its scripts/browser.py wrapper controls the pinned Playwright server and a dedicated browser profile.

Read [browser/session guidance](../travel-plan/references/browser.md). Open the dashboard by running `python3 <this-plugin>/scripts/local.py start`, resolving the plugin root from this skill's installed path. Return the printed private localhost link to the user; the fragment is a local access key, so never include it in public artifacts. Opening setup alone does not trigger financial intake or provider sign-in.

Show the compact Wallet, Itineraries, Spending, Sign-ins and Plugins & skills tabs. Wallet opens first with searchable editable tables. Itineraries displays researched plans, alternatives, per-purchase payment cards and benefit usage, sources and comparisons. Users can download a standalone trip file or delete results independently of their wallet. Personal wallet lets them enter their cards, points/miles, status, credits and certificates. Planning and requests remain in the conversation; there are no agent controls in the viewer.

Temporary sign-ins are default. If the user explicitly opts into remembering sign-ins, run `local.py settings --input -` with `{"remember":true}`. To forget saved sessions when requested, run `local.py forget --input -` with `{"confirm":"forget-all-local-sessions"}`. These preferences apply on first browser use after restarting the host's WalletFreak MCP connection. Temporary mode does not erase previously remembered sessions. Never describe the current browser as remembered until its actual mode changes. Sign-ins optionally stores usernames/passwords in a separate encrypted local vault. Users enter the master password and provider credentials directly in the private browser, never in chat. Saving does not automatically log in; provider sign-in/MFA remains user-operated. No SMS reader is installed. The vault requires the optional cryptography package from the plugin’s requirements-vault.txt. Check import availability before suggesting installation; wallet/results work without it. Never ask for or read the master password, raw credentials, vault payload or filled sign-in forms.

For browser-lock errors, close the other WalletFreak connection; never delete lock files or use a personal profile. For port conflicts, local.py start selects an available port and reuses a healthy existing service. For data errors, preserve files, report the exact error and do not reset or overwrite the private directory. `local.py stop` stops the dashboard while retaining trips.

When upgrading from 0.2, install the unified walletfreak package first, verify its eight skills, then have the user remove walletfreak-hotels, walletfreak-flights, walletfreak-credit-cards and walletfreak-trip-board using the host's plugin removal command. Existing local profiles and trip files must be retained. Old provider skill names map to provider-research plus the matching provider reference.

If the wallet appears empty, check whether the default saved traveler-profile.md exists. Offer Load existing wallet: it imports supported tables into an empty wallet while retaining dates, approximate values, ownership notes and the original file. Import is explicit; do not overwrite an existing wallet. The Plugins & skills tab shows only enabled WalletFreak packages from the WalletFreak marketplace in local Codex metadata; it never invokes a skill.

WalletFreak Spending is an optional second plugin with the spending-analysis skill and bank-specific import guides. Its local ledger uses this same core server. Open Spending to drop PDFs/CSVs, copy local references and view agent-published metrics. CSV previews and categories remain in an optional spreadsheet section. Direct import does not send statement content to the agent; do not inspect the private sheet unless requested.
