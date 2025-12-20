"""Sensor entities for Homevolt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    RestoreSensor,
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

from .capacity import (
    calculate_soh,
    sample_total_when_full,
    sample_when_full,
    select_baseline,
    update_auto_max_baseline,
)
from .const import (
    CONF_FULL_CAPACITY_SOC_THRESHOLD,
    CONF_SOH_BASELINE_KWH,
    CONF_SOH_BASELINE_STRATEGY,
    CONF_USE_HTTPS,
    DEFAULT_FULL_CAPACITY_SOC_THRESHOLD,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SOH_BASELINE_STRATEGY,
    DEFAULT_USE_HTTPS,
    DOMAIN,
)
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
        key="health_state",
        name="Homevolt Health",
        device_class=SensorDeviceClass.ENUM,
        options=["ok", "warning", "error", "unknown"],
        value_fn=lambda data: data.metrics.get("health_state"),
        attr_key="errors",
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
        suggested_display_precision=2,
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
        key="next_charge_start",
        name="Homevolt Next Charge Start",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:battery-charging",
        value_fn=lambda data: data.metrics.get("next_charge_start"),
        attr_key="schedule",
    ),
    HomevoltSensorEntityDescription(
        key="next_discharge_start",
        name="Homevolt Next Discharge Start",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:battery-minus",
        value_fn=lambda data: data.metrics.get("next_discharge_start"),
        attr_key="schedule",
    ),
    HomevoltSensorEntityDescription(
        key="next_non_idle_start",
        name="Homevolt Next Schedule Event Start",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:calendar-clock",
        value_fn=lambda data: data.metrics.get("next_non_idle_start"),
        attr_key="schedule",
    ),
    HomevoltSensorEntityDescription(
        key="next_non_idle_state",
        name="Homevolt Next Schedule Event Type",
        device_class=SensorDeviceClass.ENUM,
        options=["charge", "discharge", "grid_discharge", "grid_cycle", "idle", "unknown"],
        icon="mdi:calendar",
        value_fn=lambda data: data.metrics.get("next_non_idle_state") or "unknown",
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


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
    module_entities: list[SensorEntity] = []

    modules = []
    if coordinator.data:
        modules = coordinator.data.attributes.get("battery", {}).get("modules", [])

    full_threshold = entry.options.get(
        CONF_FULL_CAPACITY_SOC_THRESHOLD, DEFAULT_FULL_CAPACITY_SOC_THRESHOLD
    )

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
                key=f"battery_module_{number}_full_energy_available",
                name=f"Homevolt Battery Module {number} Full Available Energy",
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=2,
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
            HomevoltSensorEntityDescription(
                key=f"battery_module_{number}_state_of_health",
                name=f"Homevolt Battery Module {number} State of Health",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.BATTERY,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=1,
                value_fn=lambda data: None,
            ),
        )
        for description in module_descriptions:
            if description.key.endswith("_full_energy_available"):
                module_entities.append(
                    HomevoltFullEnergyModuleSensor(
                        module_index=index,
                        full_threshold=full_threshold,
                        coordinator=coordinator,
                        entry=entry,
                        entry_id=entry.entry_id,
                        description=description,
                    )
                )
                continue
            if description.key.endswith("_state_of_health"):
                module_entities.append(
                    HomevoltSohModuleSensor(
                        module_index=index,
                        full_threshold=full_threshold,
                        coordinator=coordinator,
                        entry=entry,
                        entry_id=entry.entry_id,
                        description=description,
                    )
                )
                continue
            module_entities.append(
                HomevoltModuleSensor(
                    module_index=index,
                    coordinator=coordinator,
                    entry=entry,
                    entry_id=entry.entry_id,
                    description=description,
                )
            )

    total_entities: list[SensorEntity] = []
    if modules:
        total_entities.append(
            HomevoltFullEnergyTotalSensor(
                coordinator=coordinator,
                entry=entry,
                entry_id=entry.entry_id,
                full_threshold=full_threshold,
            )
        )
        total_entities.append(
            HomevoltSohTotalSensor(
                coordinator=coordinator,
                entry=entry,
                entry_id=entry.entry_id,
                full_threshold=full_threshold,
            )
        )

    async_add_entities([*base_entities, *module_entities, *total_entities])


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
        return self.entity_description.key in {
            "schedule_state",
            "schedule_setpoint",
            "next_charge_start",
            "next_discharge_start",
            "next_non_idle_start",
            "next_non_idle_state",
        }

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


class HomevoltFullEnergyModuleSensor(
    CoordinatorEntity[HomevoltDataUpdateCoordinator],
    RestoreSensor,
):
    """Sample module available energy only when the module is full."""

    entity_description: HomevoltSensorEntityDescription

    def __init__(
        self,
        *,
        module_index: int,
        full_threshold: float,
        coordinator: HomevoltDataUpdateCoordinator,
        entry: ConfigEntry,
        entry_id: str,
        description: HomevoltSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._module_index = module_index
        self._full_threshold = float(full_threshold)
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._entry = entry
        self._last_sample: float | None = None
        self._was_full = False

    async def async_added_to_hass(self) -> None:
        """Restore the last stored value after restarts."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if not last_state:
            return
        try:
            self._last_sample = float(last_state.state)
        except (TypeError, ValueError):
            self._last_sample = None

    def _module_data(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        modules = self.coordinator.data.attributes.get("battery", {}).get("modules", [])
        if self._module_index < len(modules):
            return modules[self._module_index]
        return None

    @property
    def native_value(self) -> float | None:
        """Return the last sampled full energy value."""
        module = self._module_data()
        if not module:
            return self._last_sample

        self._last_sample, self._was_full = sample_when_full(
            current_value=module.get("energy_available"),
            soc=module.get("soc"),
            threshold=self._full_threshold,
            previous_value=self._last_sample,
            was_full=self._was_full,
        )
        return self._last_sample

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        module = self._module_data() or {}
        attributes = {
            "soc_threshold": self._full_threshold,
            "current_soc": module.get("soc"),
            "current_energy_available": module.get("energy_available"),
            "sampled_energy_available": self._last_sample,
        }
        return attributes

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


class HomevoltFullEnergyTotalSensor(
    CoordinatorEntity[HomevoltDataUpdateCoordinator],
    RestoreSensor,
):
    """Sample total available energy only when all modules are full."""

    def __init__(
        self,
        *,
        coordinator: HomevoltDataUpdateCoordinator,
        entry: ConfigEntry,
        entry_id: str,
        full_threshold: float,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._full_threshold = float(full_threshold)
        self._attr_unique_id = f"{entry_id}_battery_full_energy_available"
        self._attr_name = "Homevolt Battery Full Available Energy"
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 2
        self._last_sample: float | None = None
        self._was_full = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if not last_state:
            return
        try:
            self._last_sample = float(last_state.state)
        except (TypeError, ValueError):
            self._last_sample = None

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return self._last_sample

        modules = self.coordinator.data.attributes.get("battery", {}).get("modules", [])
        self._last_sample, self._was_full = sample_total_when_full(
            modules=modules,
            threshold=self._full_threshold,
            previous_value=self._last_sample,
            was_full=self._was_full,
        )
        return self._last_sample

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        modules = []
        if self.coordinator.data:
            modules = self.coordinator.data.attributes.get("battery", {}).get("modules", [])
        return {
            "soc_threshold": self._full_threshold,
            "module_count": len(modules),
        }

    @property
    def device_info(self) -> DeviceInfo:
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


class HomevoltSohModuleSensor(
    CoordinatorEntity[HomevoltDataUpdateCoordinator],
    RestoreSensor,
):
    """Estimate module state-of-health using configurable baseline strategy."""

    entity_description: HomevoltSensorEntityDescription

    def __init__(
        self,
        *,
        module_index: int,
        full_threshold: float,
        coordinator: HomevoltDataUpdateCoordinator,
        entry: ConfigEntry,
        entry_id: str,
        description: HomevoltSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._module_index = module_index
        self._full_threshold = float(full_threshold)
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 1
        self._entry = entry
        self._last_sample: float | None = None
        self._auto_baseline: float | None = None
        self._baseline: float | None = None
        self._last_soh: float | None = None
        self._was_full = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if not last_state:
            return
        self._last_soh = _safe_float(last_state.state)
        if last_state.attributes.get("baseline_strategy") in {"auto", "auto_max"}:
            self._auto_baseline = _safe_float(last_state.attributes.get("baseline_full_available_energy"))
        self._baseline = _safe_float(last_state.attributes.get("baseline_full_available_energy"))
        self._last_sample = _safe_float(last_state.attributes.get("last_sampled_full_available_energy"))

    def _module_data(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        modules = self.coordinator.data.attributes.get("battery", {}).get("modules", [])
        if self._module_index < len(modules):
            return modules[self._module_index]
        return None

    @property
    def native_value(self) -> float | None:
        module = self._module_data()
        if not module:
            return self._last_soh

        strategy = self._entry.options.get(
            CONF_SOH_BASELINE_STRATEGY,
            DEFAULT_SOH_BASELINE_STRATEGY,
        )
        manual_baseline = self._entry.options.get(CONF_SOH_BASELINE_KWH)
        manual_baseline = _safe_float(manual_baseline)
        module_count = 0
        if self.coordinator.data:
            module_count = len(self.coordinator.data.attributes.get("battery", {}).get("modules", []))

        self._last_sample, self._was_full = sample_when_full(
            current_value=module.get("energy_available"),
            soc=module.get("soc"),
            threshold=self._full_threshold,
            previous_value=self._last_sample,
            was_full=self._was_full,
        )
        if strategy == "auto":
            self._auto_baseline = update_auto_max_baseline(
                current_sample=self._last_sample,
                previous_baseline=self._auto_baseline,
            )
        self._baseline = select_baseline(
            strategy=strategy,
            manual_baseline=manual_baseline,
            auto_baseline=self._auto_baseline,
            module_count=module_count,
        )
        self._last_soh = calculate_soh(current_sample=self._last_sample, baseline=self._baseline)
        return self._last_soh

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        module = self._module_data() or {}
        strategy = self._entry.options.get(
            CONF_SOH_BASELINE_STRATEGY,
            DEFAULT_SOH_BASELINE_STRATEGY,
        )
        manual_baseline = _safe_float(self._entry.options.get(CONF_SOH_BASELINE_KWH))
        attributes = {
            "baseline_strategy": strategy,
            "baseline_full_available_energy": self._baseline,
            "last_sampled_full_available_energy": self._last_sample,
            "soc_threshold": self._full_threshold,
            "current_soc": module.get("soc"),
            "current_energy_available": module.get("energy_available"),
        }
        if strategy == "manual":
            attributes["manual_baseline_kwh"] = manual_baseline
        return attributes

    @property
    def device_info(self) -> DeviceInfo:
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


class HomevoltSohTotalSensor(
    CoordinatorEntity[HomevoltDataUpdateCoordinator],
    RestoreSensor,
):
    """Estimate total state-of-health using configurable baseline strategy."""

    def __init__(
        self,
        *,
        coordinator: HomevoltDataUpdateCoordinator,
        entry: ConfigEntry,
        entry_id: str,
        full_threshold: float,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._full_threshold = float(full_threshold)
        self._attr_unique_id = f"{entry_id}_battery_state_of_health"
        self._attr_name = "Homevolt Battery State of Health"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 1
        self._last_sample: float | None = None
        self._auto_baseline: float | None = None
        self._baseline: float | None = None
        self._last_soh: float | None = None
        self._was_full = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if not last_state:
            return
        self._last_soh = _safe_float(last_state.state)
        if last_state.attributes.get("baseline_strategy") in {"auto", "auto_max"}:
            self._auto_baseline = _safe_float(last_state.attributes.get("baseline_full_available_energy"))
        self._baseline = _safe_float(last_state.attributes.get("baseline_full_available_energy"))
        self._last_sample = _safe_float(last_state.attributes.get("last_sampled_full_available_energy"))

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return self._last_soh

        strategy = self._entry.options.get(
            CONF_SOH_BASELINE_STRATEGY,
            DEFAULT_SOH_BASELINE_STRATEGY,
        )
        manual_baseline = _safe_float(self._entry.options.get(CONF_SOH_BASELINE_KWH))

        modules = self.coordinator.data.attributes.get("battery", {}).get("modules", [])
        self._last_sample, self._was_full = sample_total_when_full(
            modules=modules,
            threshold=self._full_threshold,
            previous_value=self._last_sample,
            was_full=self._was_full,
        )
        if strategy == "auto":
            self._auto_baseline = update_auto_max_baseline(
                current_sample=self._last_sample,
                previous_baseline=self._auto_baseline,
            )
        self._baseline = select_baseline(
            strategy=strategy,
            manual_baseline=manual_baseline,
            auto_baseline=self._auto_baseline,
        )
        self._last_soh = calculate_soh(current_sample=self._last_sample, baseline=self._baseline)
        return self._last_soh

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        modules = []
        if self.coordinator.data:
            modules = self.coordinator.data.attributes.get("battery", {}).get("modules", [])
        strategy = self._entry.options.get(
            CONF_SOH_BASELINE_STRATEGY,
            DEFAULT_SOH_BASELINE_STRATEGY,
        )
        manual_baseline = _safe_float(self._entry.options.get(CONF_SOH_BASELINE_KWH))
        attributes = {
            "baseline_strategy": strategy,
            "baseline_full_available_energy": self._baseline,
            "last_sampled_full_available_energy": self._last_sample,
            "soc_threshold": self._full_threshold,
            "module_count": len(modules),
        }
        if strategy == "manual":
            attributes["manual_baseline_kwh"] = manual_baseline
        return attributes

    @property
    def device_info(self) -> DeviceInfo:
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
