---
name: dashboard-builder
description: "Compose a personal WalletFreak dashboard from versioned templates and components: wallet tables, spending metrics, references, findings and itineraries. Use for adding, removing, rearranging or styling dashboard sections."
---

# Dashboard builder

Resolve this plugin root from this skill's installed path. Start its local workspace with `python3 <plugin>/scripts/local.py start` if necessary. Dashboard is a configurable read-only overview; the existing wallet editor, statement uploads and itinerary controls stay in their respective tabs. Requests and analysis remain in the conversation.

1. Read `local.py catalog` and `local.py layout`. They return the bundled public component/template metadata and the current layout/revision, without private wallet values or statement contents.
2. Choose a template or edit the current layout to match the user's requested sections. Preserve unrelated sections for a narrow edit. Available themes are paper, sage and midnight; density is compact or comfortable. Explain missing capabilities instead of inventing component IDs.
3. Save a JSON request containing `expected_revision` from the read and `layout`, then run `local.py layout --input <request.json>` (or `--input -`). A bare layout file can instead be loaded through Dashboard → Choose a template or load a layout. The local viewer refreshes automatically.
4. If revision conflict occurs, reread the layout and reconcile the requested edit. Do not blindly overwrite newer user changes. Return the private workspace link, not a terminal dump of financial data.

The authoritative v1 contract is [layout schema](../../assets/components/v1/layout.schema.json); the [bundled catalog](../../assets/components/v1/catalog.json) includes complete templates. A layout contains only version, title, theme, density and blocks; every block contains a unique id, component, source and title. No URLs, scripts, custom HTML/CSS, filesystem paths, credentials or financial values belong in a layout. Sources are named local bindings such as wallet.programs or spending.metrics. Templates never upload or analyze source documents.

The public component gallery and catalog are published with the website at /components.html and /components/v1/catalog.json. A read-only catalog MCP service can expose list_components, get_component, list_templates, get_template and get_layout_schema when deployed. Its inputs are public component/template IDs only. Never send a user layout, wallet, statement or metric values to the public service. A newer catalog may contain components unsupported by this installation: validate against the local catalog and upgrade the plugin explicitly if needed. The bundled catalog and renderer work offline.

For empty spending metrics, use the installed spending-analysis workflow when the user asks for analysis; adding a metrics component alone does not authorize reading statements. Travel findings come from trip-board and wallet fields from traveler-profile. Keep separate currencies and reported dates intact. The overview shows at most 100 rows per component and directs users to the full views for more.
