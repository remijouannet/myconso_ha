# Core PR Readiness for `myconso_ha`

## Summary

This integration is not upstream-ready yet. The main gaps are:

1. Core manifest cleanup
2. External library readiness for core
3. Missing diagnostics and system health support
4. Separate docs and brands PRs
5. Coordinator/runtime issues likely to be flagged in review

## Main blockers

### 1. Convert the manifest from custom-integration format to core format

File: `custom_components/myconso_ha/manifest.json`

Issues:

- Remove `version` for core.
- Remove `issue_tracker` for core.
- Change `documentation` to `https://www.home-assistant.io/integrations/<domain>`.
- Remove empty `ssdp: []` and `zeroconf: []`.
- Add `quality_scale` only when that tier is actually met.
- Reconsider domain naming: `myconso_ha` may be too custom-integration specific for core.

### 2. Confirm the external dependency is acceptable for Home Assistant core

Files:

- `custom_components/myconso_ha/__init__.py`
- `custom_components/myconso_ha/config_flow.py`

Checks:

- `myconso` should be public, packaged on PyPI, open-source, and properly versioned/tagged.
- It should be async.
- It should ideally support injected Home Assistant `aiohttp` session.
- If it uses an unofficial/private API, expect extra scrutiny.

## Missing code expected upstream

### 3. Add diagnostics support

Missing:

- `custom_components/myconso_ha/diagnostics.py`

Needs:

- Redacted config entry data
- Safe coordinator/runtime data
- No token leakage

### 4. Add system health support

Missing:

- `custom_components/myconso_ha/system_health.py`

Needs:

- Basic API/service health information
- No secrets exposed

## Review risks in current code

### 5. Fix unavailable/back-online logging

File: `custom_components/myconso_ha/coordinator.py`

Issue:

- `_unavailable_logged` is reset but never set to `True`.
- “log once when unavailable, once when back online” is incomplete.

### 6. Review sequential API calls

File: `custom_components/myconso_ha/coordinator.py`

Issue:

- Per-counter API requests happen sequentially in setup and refresh.

Risk:

- Slow refreshes
- Higher latency
- Possible rate limiting

### 7. Re-check `TOTAL_INCREASING` sensor semantics

Files:

- `custom_components/myconso_ha/coordinator.py`
- `custom_components/myconso_ha/sensor.py`

Issue:

- Values are taken from the latest index found in a 7-day window.
- Confirm this is always valid for Home Assistant statistics and energy dashboards.

## Separate PRs required

### 8. Brands PR

Current local assets:

- `custom_components/myconso_ha/brand/icon.png`
- `custom_components/myconso_ha/brand/logo.png`

Upstream requirement:

- Submit branding separately to `home-assistant/brands`.

### 9. Documentation PR

Current docs:

- `README.md`

Upstream requirement:

- Submit user docs separately to `home-assistant.io`.

Docs should include:

- High-level description
- Installation/setup
- Created entities
- Data update behavior
- Known limitations
- Troubleshooting
- Removal instructions

## Testing

### 10. Prove 95%+ coverage

Current tests:

- `tests/test_init.py`
- `tests/test_config_flow.py`
- `tests/test_coordinator.py`
- `tests/test_sensor.py`

Need to verify:

- 95%+ coverage across integration modules
- Full config flow coverage by measurement

## What already looks good

Already present:

- UI config flow
- Unique ID / duplicate prevention
- Reauth flow
- Config entry unloading
- `ConfigEntry.runtime_data`
- Coordinator pattern
- Entity unique IDs
- `has_entity_name = True`
- Device creation
- Entity translations
- Broad test coverage structure

## Recommended order of work

1. Decide the final upstream domain/name.
2. Audit `myconso` for Home Assistant core compatibility.
3. Update manifest to core conventions.
4. Add `diagnostics.py`.
5. Add `system_health.py`.
6. Fix coordinator availability logging.
7. Improve or justify sequential API request behavior.
8. Validate `TOTAL_INCREASING` semantics.
9. Measure coverage and fill gaps.
10. Prepare separate `brands` and `home-assistant.io` PRs.
11. Open the `home-assistant/core` PR.

## Open questions

1. Do you want to keep the upstream domain as `myconso_ha`, or rename it now?
2. Does `myconso` already support injected `aiohttp` sessions?
3. Is the MyConso API official/public, or reverse-engineered?
4. Do you want the first submission to target bronze only, or silver immediately?
