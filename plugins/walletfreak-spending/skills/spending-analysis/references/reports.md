# Publish spending metrics

Resolve the installed WalletFreak core from walletfreak-setup. Run `python3 <core-plugin>/scripts/local.py references` to get the latest revision and available file IDs/paths. Read only the files the user asks to analyze. No model call or analysis is started by uploading.

Write a JSON object locally, outside repositories, then run `python3 <core-plugin>/scripts/local.py insights --input <report.json>`:

```json
{
  "expected_revision": "revision from references",
  "report": {
    "title": "October spending",
    "generated_at": "2026-10-18T12:00:00-04:00",
    "metrics": [{
      "label": "Net spending",
      "value": "USD 1,240.00",
      "detail": "Illustrative only. Posted purchases minus refunds; payments excluded. State the exact covered dates and page evidence in a real report.",
      "source_ids": ["an available reference ID"]
    }],
    "findings": [{
      "label": "Review recurring charges",
      "detail": "Illustrative only. Explain evidence and uncertainty; one charge alone does not establish a recurring subscription.",
      "source_ids": ["an available reference ID"]
    }]
  }
}
```

Replace all example values with computed evidence. Maximum 12 metrics and 30 findings; every item needs at least one available reference ID. Labels/values are plain text up to 200 characters; details up to 2,000. Dates require a timezone. Keep currencies separate, include period and scope, distinguish estimates, and never treat missing data as zero. The server checks shape, available sources and revision, not the truth of the calculation. Verify arithmetic and reconcile against statement sections before publishing.

If references changed, read them again and reconcile before retrying. Never blindly overwrite a newer report. Removing a referenced file clears reports that depend on it. A new upload does not expand an existing report’s scope automatically. Report source links download the private stored copy. Users can remove references without deleting originals, wallet or CSV ledger.
