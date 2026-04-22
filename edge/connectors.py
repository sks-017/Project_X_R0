"""
Connector interfaces for GE Pulse edge gateways.

The demo uses SimulatorConnector. Real plants can enable the protocol-specific
connectors by installing the matching library and providing a tag map.
"""
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ConnectorConfig:
    name: str
    protocol: str
    endpoint: str
    tag_map: Dict[str, Any]


class BaseConnector:
    def __init__(self, config: ConnectorConfig):
        self.config = config

    def read_tags(self) -> Dict[str, Any]:
        raise NotImplementedError


class SimulatorConnector(BaseConnector):
    def read_tags(self) -> Dict[str, Any]:
        return {}


class MitsubishiMCConnector(BaseConnector):
    def read_tags(self) -> Dict[str, Any]:
        try:
            import pymcprotocol
        except ImportError as exc:
            raise RuntimeError("Install pymcprotocol to use Mitsubishi MC Protocol") from exc
        host, _, port = self.config.endpoint.partition(":")
        plc = pymcprotocol.Type3E()
        plc.connect(host, int(port or 5007))
        try:
            return {
                metric: plc.batchread_wordunits(address, 1)[0]
                for metric, address in self.config.tag_map.items()
            }
        finally:
            plc.close()


class ModbusTCPConnector(BaseConnector):
    def read_tags(self) -> Dict[str, Any]:
        try:
            from pymodbus.client import ModbusTcpClient
        except ImportError as exc:
            raise RuntimeError("Install pymodbus to use Modbus TCP") from exc
        host, _, port = self.config.endpoint.partition(":")
        client = ModbusTcpClient(host, port=int(port or 502))
        client.connect()
        try:
            values = {}
            for metric, register in self.config.tag_map.items():
                result = client.read_holding_registers(int(register), 1)
                values[metric] = result.registers[0] if not result.isError() else None
            return values
        finally:
            client.close()


class OpcUaConnector(BaseConnector):
    async def read_tags_async(self) -> Dict[str, Any]:
        try:
            from asyncua import Client
        except ImportError as exc:
            raise RuntimeError("Install asyncua to use OPC UA") from exc
        async with Client(self.config.endpoint) as client:
            values = {}
            for metric, node_id in self.config.tag_map.items():
                values[metric] = await client.get_node(node_id).read_value()
            return values

    def read_tags(self) -> Dict[str, Any]:
        raise RuntimeError("Use read_tags_async for OPC UA")


class MqttConnector(BaseConnector):
    def read_tags(self) -> Dict[str, Any]:
        raise RuntimeError("MQTT connector is event-driven; subscribe and forward messages to telemetry ingestion")


def connector_for(config: ConnectorConfig) -> BaseConnector:
    protocol = config.protocol.lower()
    if protocol in {"simulator", "demo"}:
        return SimulatorConnector(config)
    if protocol == "mitsubishi_mc":
        return MitsubishiMCConnector(config)
    if protocol == "modbus_tcp":
        return ModbusTCPConnector(config)
    if protocol == "opc_ua":
        return OpcUaConnector(config)
    if protocol == "mqtt":
        return MqttConnector(config)
    raise ValueError(f"Unsupported connector protocol: {config.protocol}")
