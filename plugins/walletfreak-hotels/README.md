# WalletFreak · Hotels

Cash stays, award nights and hotel terms across eight hotel groups. Version 0.2.0. MIT licensed.

Requires `walletfreak@walletfreak` at runtime. Install core first, then `walletfreak-hotels@walletfreak` with `codex plugin add` or `claude plugin install`. Start a fresh session. This package shares the core’s one browser connection and stops research if core instructions or tools are missing.

## Included skills

- [Marriott](skills/marriott-research/SKILL.md) — `marriott-research`
- [Hilton](skills/hilton-research/SKILL.md) — `hilton-research`
- [Hyatt](skills/hyatt-research/SKILL.md) — `hyatt-research`
- [IHG](skills/ihg-research/SKILL.md) — `ihg-research`
- [Accor](skills/accor-research/SKILL.md) — `accor-research`
- [Wyndham](skills/wyndham-research/SKILL.md) — `wyndham-research`
- [Choice](skills/choice-research/SKILL.md) — `choice-research`
- [Best Western](skills/best-western-research/SKILL.md) — `best-western-research`

Skills and references stay inside this package. Coordination with core and other categories uses host discovery, never neighboring-directory reads. Users sign in and book themselves. Provider search and account eligibility remain unverified until recorded evidence establishes otherwise.

See [installation and migration](https://github.com/colinjianingxie/walletfreak_marketplace/blob/main/docs/INSTALL.md) and [privacy](https://github.com/colinjianingxie/walletfreak_marketplace/blob/main/docs/PRIVACY.md).
