from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from fraudMCP.app.models.device import DeviceCheckResult, DeviceRecord


class DeviceRiskProvider(Protocol):
    async def check_device(self, customer_id: str, device_id: str) -> DeviceCheckResult: ...

    async def list_known_devices(self, customer_id: str) -> tuple[DeviceRecord, ...]: ...


class InMemoryDeviceRiskProvider(DeviceRiskProvider):
    def __init__(self, data_path: Path) -> None:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
        self._source = str(raw.get("source") or "synthetic_demo_data")
        self._records: dict[str, dict[str, DeviceRecord]] = {}
        for customer in raw.get("customers", []):
            customer_id = str(customer.get("customer_id", "")).strip()
            if not customer_id:
                continue
            devices: dict[str, DeviceRecord] = {}
            for entry in customer.get("devices", []):
                model = DeviceRecord.model_validate(entry)
                devices[model.device_id] = model
            self._records[customer_id] = devices

    async def check_device(self, customer_id: str, device_id: str) -> DeviceCheckResult:
        customer_devices = self._records.get(customer_id, {})
        device = customer_devices.get(device_id)
        if device is None:
            return DeviceCheckResult(customer_id=customer_id, device_id=device_id, known=False, evidence_source=self._source)
        return DeviceCheckResult(
            customer_id=customer_id,
            device_id=device_id,
            known=True,
            trusted=device.trusted,
            first_seen=device.first_seen,
            last_seen=device.last_seen,
            country=device.country,
            evidence_source=self._source,
        )

    async def list_known_devices(self, customer_id: str) -> tuple[DeviceRecord, ...]:
        devices = self._records.get(customer_id, {})
        return tuple(devices.values())
