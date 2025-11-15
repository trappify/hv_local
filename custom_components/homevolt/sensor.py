"""Sensor entities for Homevolt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HomevoltDataUpdateCoordinator
from .models import HomevoltCoordinatorData


@dataclass(frozen=True, kw_only=True)
class HomevoltSensorEntityDescription(SensorEntityDescription):
    """Describes Homevolt sensor entities."""

    value_fn: Callable[[HomevoltCoordinatorData], Any]
    attr_key: str | None = None


SENSOR_DESCRIPTIONS: tuple[HomevoltSensorEntityDescription, ...] = (
    HomevoltSensorEntityDescription(
        key="system_state",
        name="Homevolt System State",
        icon="mdi:battery-sync-outline",
        value_fn=lambda data: data.metrics.get("system_state"),
        attr_key="system",
    ),
    HomevoltSensorEntityDescription(
        key="battery_soc",
        name="Homevolt Battery State of Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("battery_soc"),
        attr_key="battery",
    ),
    HomevoltSensorEntityDescription(
        key="battery_temperature",
        name="Homevolt Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("battery_temperature"),
        attr_key="battery",
    ),
    HomevoltSensorEntityDescription(
        key="battery_power",
        name="Homevolt Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("battery_power"),
        attr_key="battery",
    ),
    HomevoltSensorEntityDescription(
        key="grid_power",
        name="Homevolt Grid Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("grid_power"),
        attr_key="grid",
    ),
    HomevoltSensorEntityDescription(
        key="solar_power",
        name="Homevolt Solar Production",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("solar_power"),
        attr_key="solar",
    ),
    HomevoltSensorEntityDescription(
        key="load_power",
        name="Homevolt Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("load_power"),
        attr_key="load",
    ),
    HomevoltSensorEntityDescription(
        key="frequency",
        name="Homevolt Grid Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("frequency"),
        attr_key="grid",
    ),
    HomevoltSensorEntityDescription(
        key="voltage_l1",
        name="Homevolt Voltage L1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("voltage_l1"),
        attr_key="grid",
    ),
    HomevoltSensorEntityDescription(
        key="voltage_l2",
        name="Homevolt Voltage L2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("voltage_l2"),
        attr_key="grid",
    ),
    HomevoltSensorEntityDescription(
        key="voltage_l3",
        name="Homevolt Voltage L3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.metrics.get("voltage_l3"),
        attr_key="grid",
    ),
    HomevoltSensorEntityDescription(
        key="schedule_state",
        name="Homevolt Schedule State",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.ENUM,
        options=["charge", "discharge", "idle", "grid_discharge", "grid_cycle"],
        value_fn=lambda data: data.metrics.get("schedule_state"),
        attr_key="schedule",
    ),
    HomevoltSensorEntityDescription(
        key="schedule_setpoint",
        name="Homevolt Schedule Setpoint",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        value_fn=lambda data: data.metrics.get("schedule_setpoint"),
        attr_key="schedule",
    ),
    HomevoltSensorEntityDescription(
        key="grid_energy_imported",
        name="Homevolt Grid Energy Imported",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.metrics.get("grid_energy_imported"),
        attr_key="grid",
    ),
    HomevoltSensorEntityDescription(
        key="grid_energy_exported",
        name="Homevolt Grid Energy Exported",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.metrics.get("grid_energy_exported"),
        attr_key="grid",
    ),
    HomevoltSensorEntityDescription(
        key="solar_energy_produced",
        name="Homevolt Solar Energy Produced",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.metrics.get("solar_energy_produced"),
        attr_key="solar",
    ),
    HomevoltSensorEntityDescription(
        key="solar_energy_consumed",
        name="Homevolt Solar Energy Consumed",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.metrics.get("solar_energy_consumed"),
        attr_key="solar",
    ),
    HomevoltSensorEntityDescription(
        key="battery_energy_imported",
        name="Homevolt Battery Charge Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.metrics.get("battery_energy_imported"),
        attr_key="battery",
    ),
    HomevoltSensorEntityDescription(
        key="battery_energy_exported",
        name="Homevolt Battery Discharge Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.metrics.get("battery_energy_exported"),
        attr_key="battery",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Homevolt sensor entities."""
    coordinator: HomevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        HomevoltSensor(coordinator=coordinator, entry_id=entry.entry_id, description=description)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class HomevoltSensor(CoordinatorEntity[HomevoltDataUpdateCoordinator], SensorEntity):
    """A Homevolt sensor backed by the shared coordinator."""

    entity_description: HomevoltSensorEntityDescription

    def __init__(
        self,
        *,
        coordinator: HomevoltDataUpdateCoordinator,
        entry_id: str,
        description: HomevoltSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name

    @property
    def native_value(self) -> Any:
        """Return the measurement for this sensor."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes scoped to the metric."""
        if not self.coordinator.data:
            return None

        attributes: dict[str, Any] = {}
        meta = self.coordinator.data.attributes.get("meta")
        if meta:
            attributes.update(meta)

        if self.entity_description.attr_key:
            scoped = self.coordinator.data.attributes.get(self.entity_description.attr_key)
            if scoped:
                attributes.update(scoped)

        return attributes or None
