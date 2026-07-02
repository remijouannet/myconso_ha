"""Test the MyConso sensor platform."""

import pytest
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.myconso_ha.const import DOMAIN


@pytest.mark.usefixtures("init_integration")
async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the sensor entities."""
    device_entry = device_registry.async_get_device(identifiers={(DOMAIN, "housing_1")})
    assert device_entry
    assert device_entry.name == "My Home"
    assert device_entry.manufacturer == "proxiserve"
    assert device_entry.entry_type == dr.DeviceEntryType.SERVICE

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    for entity_entry in entity_entries:
        assert entity_entry.device_id == device_entry.id
    await hass.async_block_till_done()

    t1_entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, "housing_1_counter_1_heating"
    )
    assert t1_entity_id == "sensor.my_home_heating"

    t1_state = hass.states.get(t1_entity_id)
    assert t1_state is not None
    assert t1_state.state == "1500.5"
    assert t1_state.attributes.get("counter") == "counter_1"
    assert t1_state.attributes.get("location") == "Kitchen"
    assert t1_state.attributes.get("fluidtype") == "heating"
    assert t1_state.attributes.get("unit_of_measurement") == UnitOfEnergy.KILO_WATT_HOUR
    assert t1_state.attributes.get("device_class") == "energy"
