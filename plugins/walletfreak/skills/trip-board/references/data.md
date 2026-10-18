# Dashboard findings contract

Use the existing example fields: title, summary, generated_at (ISO with zone), optional illustrative boolean, options, research, itinerary and gaps. Keep failed searches. Every available option needs an observation timestamp and a public HTTPS source.

Options have unique stable id, title, kind (flight/hotel/lounge/transport/other), status (available/unavailable/waitlisted/blocked/unverified), provider, program, quoted price text, observed_at, sources and optional search/product/terms/benefits/uncertainty/reproduce text. Do not reuse an ID for a different product.

For selected itinerary subtotals, add choice_group (e.g. outbound-flight, return-flight, tokyo-hotel) to mutually exclusive alternatives, and optional cost: {"cash":"500.00","currency":"USD","points":100000,"program":"ANA Mileage Club","complete":true}. Cash is a nonnegative decimal string covering the whole party/stay, including mandatory award charges. Points are nonnegative integers with their own program. Never parse price text to invent these fields. Unknown fees require complete:false. Conditional statement credits do not reduce cash due. One option per choice_group can be selected. Only available, complete costs enter subtotals, separated by currency and program; other selected items stay explicitly unpriced.

Research entries contain title, detail, optional observed_at and url. Itinerary entries contain when (local time with named zone), title, detail and optional option_id. Gaps are unresolved checks and unpriced components. Dates remain in the user's supplied order; don't infer local time zones from UTC alone.

Publish a new result with `local.py publish --input -` and {"findings":{...}}. Update with {"id":"<result-id>","expected_revision":<current revision>,"findings":{...}}. Read current revisions with `local.py status`. There are no request IDs, claims, heartbeats or task queues. A deleted result rejects updates; do not recreate it without a new user request.

The viewer renders itinerary entries immediately, using the linked option kind/provider for flight, stay, transport and lounge components. It preserves the research itinerary independently of local comparison selections. Include schedule/time-zone text and known restrictions; leave unknown timing explicit. Personal wallet data is never part of this display contract.

## Card and benefit plan per purchase

Each newly generated purchase option should include `payment`: `{"card":"Exact existing card product, To confirm, or Not required","reason":"Why this card/channel applies","benefits":[{"name":"Benefit name","status":"planned","detail":"Amount or count allocated, eligibility, shared allowance and conditions"}]}`. The viewer and standalone export show it on the option and linked itinerary entry, plus the comparison table in the viewer.

Statuses: `planned` (proposed, not spent), `used` (already consumed, with evidence described in detail and required `recorded_at` ISO timestamp with zone), `not-used` (not allocated to this purchase), `conditional` (depends on unconfirmed eligibility/availability), `unavailable` (expired, exhausted or ineligible). Never mark a planned benefit used because a user shortlisted or selected an option. No saved-wallet deduction occurs. Unknown card/benefit information stays explicit; an absent payment object in an older result displays To confirm.

Use exact existing card products without account numbers or private owner identifiers. Different cards can fund the points and pay the remaining cash. Check payment/portal requirements and allocate shared credits once across the trip. The benefit detail states whether a credit is a future reimbursement; it does not change gross cost fields. An empty benefits list means no usage documented, not proof that no benefits exist.
