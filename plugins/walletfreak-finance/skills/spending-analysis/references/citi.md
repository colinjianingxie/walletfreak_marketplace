# Citi activity

Reviewed 2026-10-18. [Citi's statements tutorial](https://www.citi.com/CRD/PDF/Transactions_Statements_Tutorial_Final.pdf) covers statement downloads. This is historical documentation; verify current controls in the user's account. Citi consumer cards, banking and CitiManager have different exports; corporate or international documentation is not proof of US consumer CSV availability.

Supported shape: Status, Date, Description, Debit, Credit. Map Date and Description plus Debit/Credit. The parser expects separate columns as nonnegative magnitudes; inspect signs. Some exports instead use Amount or different headers: use explicit column mapping and choose the correct purchase sign. Negative entries in separate Debit/Credit columns are rejected, not silently converted. Normalize to signed Amount only after checking transaction direction against the source. Import posted transactions, not pending authorizations.

Payments, merchant refunds, rewards statement credits and reversals need separate classifications. In a PDF, separate payments/credits from purchases, cash advances, fees and interest. A payment is not a negative purchase. Do not count summary totals or rewards summaries as transactions. Verify account, period, currency, row count and section totals using the [PDF/other-format workflow](other-formats.md).
