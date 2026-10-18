# Capital One activity

Reviewed 2026-10-18. Start at the user's signed-in [Capital One account](https://www.capitalone.com/) and look for activity download/export. CSV availability and columns must be checked in that specific card or bank account. No current US consumer export schema has been independently verified here; do not substitute commercial treasury instructions as consumer documentation.

Supported card-shaped CSV: Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit. Map transaction date/description and separate nonnegative Debit/Credit magnitudes. These columns override Amount sign selection. Card No. is not stored: give each account a stable alias. Exports containing multiple account/card currencies should be split or supplied with an explicit Currency column; never infer currency from a dollar sign alone.

For a single signed Amount column, choose direction from one known purchase and verify a payment/refund. Checking/savings layouts may differ; map their columns rather than treating them like card exports. Pending transactions and balance summaries do not belong in the ledger. PDFs may group cardholders and fees/interest separately; capture all applicable activity once and reconcile section totals before import. See [PDF/other formats](other-formats.md).
