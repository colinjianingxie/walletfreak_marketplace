---
name: deal-research
description: "Research current merchant prices, cash back, coupons and card value for a shopping request, then publish sourced offers to the local WalletFreak Shopping board."
---

# Deal research

Ask for the exact product or purchase category, region, budget and any required retailer. Research current offers using official merchant, issuer and cash-back portal pages. Verify product variant, shipping/tax assumptions, coupon eligibility, expiry, exclusions and whether cash back needs activation. Use `wallet-optimizer` from WalletFreak Credit Cards if installed to compare cards already in the person's wallet. Do not add unverified stacking, targeted offers or benefits to a net price. Never place an order, activate an offer or enroll a card without the user's separate request.

Resolve core with `walletfreak-setup`, then start the shared private local dashboard with `python3 <core>/scripts/local.py start --view shopping`. Run `python3 <core>/scripts/local.py shopping` for the current revision. Publish JSON via `python3 <core>/scripts/local.py shopping-publish --input <file.json>` with `expected_revision` and `deals` (at most 50). Each deal has stable `id`, `merchant`, `product`, numeric `price` string, three-letter `currency`, public HTTPS `source_url`, time-zone-aware `observed_at`, `terms` and `status` (`available`, `unverified` or `expired`). Optional fields are `cashback`, `card` and ISO `expires_on`. Keep reported price separate from conditional cash back and card value. On a revision conflict, reread and reconcile. Return the local Shopping view link and key tradeoffs; the board shows the source and observation time for every deal.
