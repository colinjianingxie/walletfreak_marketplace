# WalletFreak

The complete travel toolkit: guided intake, 31 provider references, a personal wallet, current card/redemption optimization, card benefits, lounge tracking and a private local trip dashboard.

Use walletfreak-setup after installation. Python 3.10+, Node.js 18+ and Chrome are required. Start the dashboard with `python3 scripts/local.py start` from this plugin directory. Its private link works on this device only.

Planning stays in the Codex or Claude conversation. The browser displays published results and an editable personal wallet; it has no agent controls. Results can be downloaded or deleted without changing the wallet. Users sign in and book themselves. Temporary browser sessions are default; remembered sessions are opt-in. Profiles and trips stay outside this package.

See [planning](skills/travel-plan/SKILL.md), [dashboard](skills/trip-board/SKILL.md) and [browser/session guidance](skills/travel-plan/references/browser.md).

The shared MCP launch command accepts Claude's expanded plugin-root argument; Codex uses the plugin-relative working directory. The path is a separate process argument, never interpolated into shell or Python source. Both routes run the same browser wrapper.
