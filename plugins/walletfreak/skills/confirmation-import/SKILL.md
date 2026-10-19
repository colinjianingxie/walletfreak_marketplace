---
name: confirmation-import
description: "Turn pasted flight or hotel confirmation text into a reviewed local itinerary, preserving booking status, dates and reported costs. Use when a traveler has booked travel and wants it added to WalletFreak."
---

# Import confirmations

Open the private WalletFreak Travel dashboard with walletfreak-setup. The user can paste confirmation text under **Paste confirmations**. Separate emails with a line of `---`. The local preview detects likely flight/hotel type, date, property or route, reported total and explicit booked wording. It does not store the original email. Ask the user to review every detected field, especially date, time zone, check-in/out, price currency and booked status, before clicking **Save reviewed itinerary**. Missing dates must be supplied before saving; ambiguous text stays proposed.

A saved import is a local trip with a visual timeline and potential costs. It can be enriched afterward with travel-plan, stay-route-map, card-travel-benefits and wallet-optimizer. The parser does not prove a reservation is active, extract every vendor format, or log in to check status. Never add raw confirmation codes, full ticket numbers, passwords or email bodies to public research, site templates, source links or exported trip details. If the traveler instead pastes text in the agent conversation, extract structured fields from that user-provided text, confirm uncertain facts, and publish through trip-board. Follow the host's model data handling for conversation content.
