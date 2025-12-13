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
    CONF_HOST,
    CONF_PORT,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DEFAULT_PORT, DEFAULT_USE_HTTPS, DOMAIN, CONF_USE_HTTPS
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


def _module_value(data: HomevoltCoordinatorData, index: int, key: str) -> Any:
    modules = data.attributes.get("battery", {}).get("modules", [])
    if index < len(modules):
        return modules[index].get(key)
    return None


def _module_flags_as_text(data: HomevoltCoordinatorData, index: int, key: str) -> str | None:
    flags = _module_value(data, index, key) or []
    if not flags:
        return "OK"
    return ", ".join(str(flag) for flag in flags)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Homevolt sensor entities."""
    coordinator: HomevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    base_entities = [
        HomevoltSensor(
            coordinator=coordinator,
            entry=entry,
            entry_id=entry.entry_id,
            description=description,
        )
        for description in SENSOR_DESCRIPTIONS
    ]
    module_entities: list[HomevoltSensor] = []

    modules = []
    if coordinator.data:
        modules = coordinator.data.attributes.get("battery", {}).get("modules", [])

    for index, _ in enumerate(modules):
        number = index + 1
        module_descriptions = (
            HomevoltSensorEntityDescription(
                key=f"battery_module_{number}_soc",
                name=f"Homevolt Battery Module {number} State of Charge",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.BATTERY,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, i=index: _module_value(data, i, "soc"),
            ),
            HomevoltSensorEntityDescription(
                key=f"battery_module_{number}_temperature_min",
                name=f"Homevolt Battery Module {number} Min Cell Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, i=index: _module_value(data, i, "temperature_min"),
            ),
            HomevoltSensorEntityDescription(
                key=f"battery_module_{number}_temperature_max",
                name=f"Homevolt Battery Module {number} Max Cell Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, i=index: _module_value(data, i, "temperature_max"),
            ),
            HomevoltSensorEntityDescription(
                key=f"battery_module_{number}_cycle_count",
                name=f"Homevolt Battery Module {number} Cycle Count",
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, i=index: _module_value(data, i, "cycle_count"),
            ),
            HomevoltSensorEntityDescription(
                key=f"battery_module_{number}_energy_available",
                name=f"Homevolt Battery Module {number} Available Energy",
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, i=index: _module_value(data, i, "energy_available"),
            ),
            HomevoltSensorEntityDescription(
                key=f"battery_module_{number}_state",
                name=f"Homevolt Battery Module {number} State",
                value_fn=lambda data, i=index: _module_value(data, i, "state_str")
                or _module_value(data, i, "state"),
            ),
            HomevoltSensorEntityDescription(
                key=f"battery_module_{number}_alarms",
                name=f"Homevolt Battery Module {number} Alarms",
                value_fn=lambda data, i=index: _module_flags_as_text(data, i, "alarm_flags"),
            ),
        )
        module_entities.extend(
            HomevoltModuleSensor(
                module_index=index,
                coordinator=coordinator,
                entry=entry,
                entry_id=entry.entry_id,
                description=description,
            )
            for description in module_descriptions
        )

    async_add_entities([*base_entities, *module_entities])


class HomevoltSensor(CoordinatorEntity[HomevoltDataUpdateCoordinator], SensorEntity):
    """A Homevolt sensor backed by the shared coordinator."""

    entity_description: HomevoltSensorEntityDescription

    def __init__(
        self,
        *,
        coordinator: HomevoltDataUpdateCoordinator,
        entry: ConfigEntry,
        entry_id: str,
        description: HomevoltSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._entry = entry
        self._last_value: Any = None

    @property
    def native_value(self) -> Any:
        """Return the measurement for this sensor."""
        if not self.coordinator.data:
            if self._should_persist_value:
                return self._last_value
            return None
        value = self.entity_description.value_fn(self.coordinator.data)
        if value is None and self._should_persist_value:
            return self._last_value
        self._last_value = value
        return value

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

    @property
    def _should_persist_value(self) -> bool:
        """Keep the last known value for volatile schedule fields."""
        return self.entity_description.key in {"schedule_state", "schedule_setpoint"}

    @property
    def device_info(self) -> DeviceInfo:
        """Link all entities to a single Homevolt device."""
        host = self._entry.data.get(CONF_HOST)
        port = self._entry.data.get(CONF_PORT, DEFAULT_PORT)
        use_https = self._entry.data.get(CONF_USE_HTTPS, DEFAULT_USE_HTTPS)
        configuration_url = None
        if host:
            scheme = "https" if use_https else "http"
            configuration_url = f"{scheme}://{host}:{port}"

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id or self._entry.entry_id)},
            name=DEFAULT_NAME,
            manufacturer="Homevolt",
            model="Battery Gateway",
            configuration_url=configuration_url,
        )


class HomevoltModuleSensor(HomevoltSensor):
    """Module-level metrics such as per-pack SOC and temperature."""

    def __init__(
        self,
        *,
        module_index: int,
        coordinator: HomevoltDataUpdateCoordinator,
        entry: ConfigEntry,
        entry_id: str,
        description: HomevoltSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator=coordinator, entry=entry, entry_id=entry_id, description=description)
        self._module_index = module_index

    def _module_data(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        modules = self.coordinator.data.attributes.get("battery", {}).get("modules", [])
        if self._module_index < len(modules):
            return modules[self._module_index]
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return module-specific attributes (state, cycle count, alarms)."""
        attributes = super().extra_state_attributes or {}
        module = self._module_data()
        if module:
            attributes.update(module)
        return attributes or None
