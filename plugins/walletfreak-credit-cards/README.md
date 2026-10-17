# WalletFreak · Credit cards

Lounge access tracker, Hilton Aspire/Surpass and other card benefits, plus four travel portals. Version 0.2.0. MIT licensed.

Requires `walletfreak@walletfreak` at runtime. Install core first, then `walletfreak-credit-cards@walletfreak` with `codex plugin add` or `claude plugin install`. Start a fresh session. This package shares the core’s one browser connection and stops research if core instructions or tools are missing.

## Included skills

- [Lounge access tracker](skills/lounge-access/SKILL.md) — `lounge-access`, airport options, guest fees and planned/used visit allowances

- [Existing card travel benefits](skills/card-travel-benefits/SKILL.md) — `card-travel-benefits`, including Hilton Aspire and Surpass
- [Capital One Travel](skills/capital-one-travel-research/SKILL.md) — `capital-one-travel-research`
- [Amex Travel](skills/amex-travel-research/SKILL.md) — `amex-travel-research`
- [Chase Travel](skills/chase-travel-research/SKILL.md) — `chase-travel-research`
- [Citi Travel](skills/citi-travel-research/SKILL.md) — `citi-travel-research`

Skills and references stay inside this package. Coordination with core and other categories uses host discovery, never neighboring-directory reads. Users sign in and book themselves. Provider search and account eligibility remain unverified until recorded evidence establishes otherwise.

See [installation and migration](https://github.com/colinjianingxie/walletfreak_marketplace/blob/main/docs/INSTALL.md) and [privacy](https://github.com/colinjianingxie/walletfreak_marketplace/blob/main/docs/PRIVACY.md).
