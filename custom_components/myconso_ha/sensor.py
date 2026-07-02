import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    DeviceEntry,
    DeviceEntryType,
    DeviceInfo,
)
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_conversion import EnergyConverter, VolumeConverter
from myconso.models.counter import CounterItem

from .const import DOMAIN
from .coordinator import MyConsoConfigEntry, MyConsoCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


class MyConsoFluidType(StrEnum):
    """Enumeration of supported fluid types in MyConso."""

    CLIM = "clim"
    HEATING = "heating"
    HOT_WATER = "waterHot"
    WATER = "waterCold"


@dataclass(kw_only=True, frozen=True)
class MyConsoSensorEntityDescription(SensorEntityDescription):
    """Defines the structure and metadata for MyConso sensor entities."""

    fluid_type: MyConsoFluidType
    unit_class: str


class MyConsoSensorEntity(StrEnum):
    """Enumeration of MyConso sensor entity keys."""

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
        suggested_display_precision=3,
        unit_class=VolumeConverter.UNIT_CLASS,
    ),
    MyConsoSensorEntityDescription(
        key=MyConsoSensorEntity.WATER,
        translation_key=MyConsoSensorEntity.WATER,
        fluid_type=MyConsoFluidType.WATER,
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        unit_class=VolumeConverter.UNIT_CLASS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConsoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = config_entry.runtime_data

    sensors = []
    for counter in coordinator.counters:
        for description in SENSOR_DESCRIPTIONS:
            if counter.fluidType == description.fluid_type:
                sensors.append(MyConsoSensor(coordinator, description, counter))
    async_add_entities(sensors)


class MyConsoSensor(CoordinatorEntity[MyConsoCoordinator], SensorEntity):
    """Sensor entity for displaying MyConso counter data."""

    entity_description: MyConsoSensorEntityDescription
    device_entry: DeviceEntry | None
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MyConsoCoordinator,
        entity_description: MyConsoSensorEntityDescription,
        counter: CounterItem,
    ) -> None:
        """Initialize sensor with coordinator, entity description, and counter info."""
        super().__init__(coordinator)
        _LOGGER.debug("MyConsoSensor counter %s", counter)

        self.counter = counter.counter
        self.housing = counter.housing
        self.fluid_type = counter.fluidType
        self.entity_description = entity_description
        self._attr_unique_id = f"{self.housing}_{self.counter}_{entity_description.key}"
        location = coordinator.counter_locations.get(f"{self.housing}_{self.counter}")

        #if location:
        #    self._attr_name = f"{entity_description.fluid_type} {location}"
        #else:
        #    self._attr_name = f"{entity_description.fluid_type} {self.counter}"

        self._attr_extra_state_attributes = {
            "counter": counter.counter,
            "location": location,
            "fluidtype": counter.fluidType,
        }

        housing_name = "No housing name"
        for housing in coordinator.info_housings.member:
            if self.housing == housing.housingId and housing.name:
                housing_name = housing.name
                break

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="proxiserve",
            name=housing_name,
            serial_number=counter.housing,
            identifiers={(DOMAIN, counter.housing)},
        )

    @property
    @override
    def native_value(self) -> StateType:
        """Return the current counter reading value from coordinator data."""
        for counter in self.coordinator.data:
            if (
                counter.housing == self.housing
                and counter.counter == self.counter
                and counter.fluid_type == self.fluid_type
            ):
                return counter.last_index
        return None
