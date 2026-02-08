import logging


from dataclasses import dataclass
from enum import StrEnum

from homeassistant.const import Platform
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfEnergy, UnitOfVolume
from homeassistant.helpers.device_registry import (
    DeviceEntry,
    DeviceEntryType,
    DeviceInfo,
)
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_conversion import EnergyConverter, VolumeConverter

from .const import DOMAIN
from .coordinator import MyConsoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


class MyConsoFluidType(StrEnum):
    CLIM = "clim"
    HEATING = "heating"
    HOT_WATER = "waterHot"
    WATER = "waterCold"


@dataclass(kw_only=True, frozen=True)
class MyConsoSensorEntityDescription(SensorEntityDescription):
    fluid_type: MyConsoFluidType
    unit_class: str


class MyConsoSensorEntity(StrEnum):
    CLIM = "clim"
    HEATING = "heating"
    HOT_WATER = "hot_water"
    WATER = "water"


SENSOR_DESCRIPTIONS: tuple[MyConsoSensorEntityDescription, ...] = (
    MyConsoSensorEntityDescription(
        key=MyConsoSensorEntity.CLIM,
        translation_key=MyConsoSensorEntity.CLIM,
        fluid_type=MyConsoFluidType.CLIM,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        unit_class=EnergyConverter.UNIT_CLASS,
    ),
    MyConsoSensorEntityDescription(
        key=MyConsoSensorEntity.HEATING,
        translation_key=MyConsoSensorEntity.HEATING,
        fluid_type=MyConsoFluidType.HEATING,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        unit_class=EnergyConverter.UNIT_CLASS,
    ),
    MyConsoSensorEntityDescription(
        key=MyConsoSensorEntity.HOT_WATER,
        translation_key=MyConsoSensorEntity.HOT_WATER,
        fluid_type=MyConsoFluidType.HOT_WATER,
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        unit_class=VolumeConverter.UNIT_CLASS,
    ),
    MyConsoSensorEntityDescription(
        key=MyConsoSensorEntity.WATER,
        translation_key=MyConsoSensorEntity.WATER,
        fluid_type=MyConsoFluidType.WATER,
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        unit_class=VolumeConverter.UNIT_CLASS,
    ),
)


async def async_setup_entry(
    hass,
    config_entry,
    async_add_entities,
) -> None:
    _LOGGER.debug("async_setup_entry 1 %s", config_entry.data)
    _LOGGER.debug("async_setup_entry 2 %s", config_entry.runtime_data)

    coordinator = config_entry.runtime_data

    _LOGGER.debug("async_setup_entry 3 %s", coordinator.data)
    _LOGGER.debug("async_setup_entry 4 %s", coordinator.counters)

    sensors = []
    for counter in coordinator.counters:
        for description in SENSOR_DESCRIPTIONS:
            if counter["fluidType"] == description.fluid_type:
                sensors.append(MyConsoSensor(coordinator, description, counter))
    async_add_entities(sensors)


class MyConsoSensor(CoordinatorEntity[MyConsoCoordinator], SensorEntity):
    entity_description: MyConsoSensorEntityDescription
    #_attr_has_entity_name = True
    device_entry: DeviceEntry

    def __init__(
        self,
        coordinator: MyConsoCoordinator,
        entity_description: MyConsoSensorEntityDescription,
        counter,
    ) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)
        _LOGGER.debug("MyConsoSensor init 1 %s", counter)
        _LOGGER.debug("MyConsoSensor init 2 %s", counter['counter'])
        _LOGGER.debug("MyConsoSensor init 3 %s", entity_description.key)
        _LOGGER.debug("MyConsoSensor init 4 %s", coordinator.housing)

        self.counter = counter["counter"]
        self.fluid_type = counter["fluidType"]
        self.entity_description = entity_description
        self._attr_unique_id = f"{self.counter}_{entity_description.key}"
        self._attr_name = f"{entity_description.fluid_type} {counter['location']} {self.counter}"
        self._attr_extra_state_attributes = {
                "counter": counter["counter"],
                "location": counter["location"],
                "fluidtype": counter["fluidType"]
        }
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="proxiserve",
            model="proxiserve",
            name=coordinator.info_housing['name'],
            model_id=coordinator.housing,
            serial_number=coordinator.housing,
            identifiers={(DOMAIN, coordinator.housing)},
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        for counter in self.coordinator.data:
            if (
                counter["counter"] == self.counter
                and counter["fluidType"] == self.fluid_type
            ):
                return counter["last_index"]
        return None
