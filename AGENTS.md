# AGENTS.md — myconso_ha

## Project Overview

Home Assistant custom integration (`myconso_ha`) that exposes energy consumption sensors from the [MyConso](https://play.google.com/store/apps/details?id=fr.proxiserve.myconso) app.

- **Domain**: `myconso_ha`
- **Type**: Service integration, cloud polling (`iot_class: cloud_polling`)
- **Setup**: Config flow (UI-based configuration, no YAML)
- **External dependency**: `myconso==0.0.13` (PyPI library)
- **HACS**: Distributed via HACS with zip releases

## Architecture

```
config_flow.py   → User sets up credentials via UI
coordinator.py   → Polls MyConso API periodically
sensor.py        → Exposes sensor entities from coordinator data
const.py         → Constants (domain, etc.)
__init__.py      → Integration setup & unload
```

## Development Environment

- **Package manager**: [uv](https://docs.astral.sh/uv/) — use it for everything.
- **Python**: `>=3.14.2`
- **Home Assistant core**: `>=2026.3.0`
- **Virtual env**: managed by uv (`.venv/`)

## Common Commands (all via uv)

```bash
# Install/sync dependencies
uv sync

# Run tests
uv run pytest

# Run tests
uv run pytest

# Lint & format
uv run ruff check .
uv run ruff format .

# Type check (strict, pydantic plugin)
uv run mypy

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Coding Style

- Follow **Home Assistant core conventions**.
- Strict `mypy` enabled with `pydantic.mypy` plugin.
- `ruff` rules: `ASYNC`, `E`, `F`, `UP`, `B`, `SIM`, `I`, `RUF`, `Q`, `PL`.
- Coordinator pattern for all data fetching.
- Config flow for all user-facing setup.
- Use `homeassistant` typing and helpers; avoid bypassing core abstractions.

## Testing Notes

- Framework: `pytest`, `pytest-asyncio`, `pytest-homeassistant-custom-component`
- Async mode is auto-enabled (`asyncio_mode = auto`).

## Release / HACS

- Version is declared in `manifest.json` and `hacs.json`.
- `hacs.json` has `zip_release: true` and `filename: myconso_ha.zip`.
- Do not forget to bump `version` in `manifest.json` and `pyproject.toml` on release.

## Files of Interest

| File | Purpose |
|------|---------|
| `custom_components/myconso_ha/manifest.json` | Integration metadata |
| `custom_components/myconso_ha/config_flow.py` | UI configuration wizard |
| `custom_components/myconso_ha/coordinator.py` | DataUpdateCoordinator |
| `custom_components/myconso_ha/sensor.py` | Sensor platform |
| `custom_components/myconso_ha/const.py` | Domain constants |
| `pyproject.toml` | uv project config, tool settings |
| `hacs.json` | HACS repository metadata |
