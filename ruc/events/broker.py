"""Client of the event layer's EventBrokerService (eventlayer/broker_service.proto).

Topics: the broker routes an event by its EventEnvelope.event_type, which is
set to the topic name (also copied to metadata["topic"]).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import grpc
from google.protobuf import any_pb2, timestamp_pb2
from google.protobuf.message import Message

from oowlet.gen.eventlayer.basepb import base_pb2
from oowlet.gen.eventlayer.brokerservicepb import broker_service_pb2, broker_service_pb2_grpc

log = logging.getLogger("ruc.broker")


@dataclass
class BrokerEndpoint:
    address: str
    token_file: Path | None = None      # bearer token for the broker, when it requires one
    ca_file: Path | None = None         # TLS when set
    cert_file: Path | None = None       # client certificate (mTLS)
    key_file: Path | None = None
    timeout_s: float = 10.0
    max_message_bytes: int = 16 << 20


class BrokerClient:
    def __init__(self, ep: BrokerEndpoint, source: str) -> None:
        self.ep = ep
        self.source = source
        token = ep.token_file.read_text(encoding="utf-8").strip() if ep.token_file else ""
        self._md: tuple[tuple[str, str], ...] = (("authorization", f"Bearer {token}"),) if token else ()
        opts = [("grpc.max_receive_message_length", ep.max_message_bytes),
                ("grpc.max_send_message_length", ep.max_message_bytes),
                ("grpc.keepalive_time_ms", 30_000)]
        if ep.ca_file:
            creds = grpc.ssl_channel_credentials(
                root_certificates=ep.ca_file.read_bytes(),
                private_key=ep.key_file.read_bytes() if ep.key_file else None,
                certificate_chain=ep.cert_file.read_bytes() if ep.cert_file else None)
            self._channel = grpc.aio.secure_channel(ep.address, creds, options=opts)
        else:
            self._channel = grpc.aio.insecure_channel(ep.address, options=opts)
        self._stub = broker_service_pb2_grpc.EventBrokerServiceStub(self._channel)

    async def close(self) -> None:
        await self._channel.close()

    def envelope(self, topic: str, payload: Message, correlation_id: str = "", event_id: str = "",
                 metadata: dict[str, str] | None = None, partition_key: str = "") -> base_pb2.EventEnvelope:
        anyp = any_pb2.Any()
        anyp.Pack(payload)
        ts = timestamp_pb2.Timestamp()
        ts.GetCurrentTime()
        md = dict(metadata or {})
        md.setdefault("topic", topic)
        return base_pb2.EventEnvelope(
            event_id=event_id or str(uuid.uuid4()), event_type=topic, source=self.source,
            correlation_id=correlation_id, timestamp=ts, version=1, payload=anyp, metadata=md,
            partition_key=partition_key or correlation_id)

    async def publish(self, env: base_pb2.EventEnvelope, wait_for_persistence: bool = True) -> None:
        req = broker_service_pb2.PublishEventRequest(event=env, wait_for_persistence=wait_for_persistence)
        await self._stub.PublishEvent(req, metadata=self._md, timeout=self.ep.timeout_s)

    async def subscribe(self, group: str, topics: list[str], stop: asyncio.Event,
                        from_offset: int = 0) -> AsyncIterator[base_pb2.EventEnvelope]:
        """Events of `topics` for consumer group `group`, reconnecting with
        backoff until `stop` is set. The broker commits offsets (auto_commit),
        so a reconnect continues where the group left off."""
        backoff = 0.5
        while not stop.is_set():
            call = self._stub.SubscribeEvents(
                broker_service_pb2.SubscribeRequest(consumer_group=group, topics=topics,
                                                    from_offset=from_offset, auto_commit=True),
                metadata=self._md)
            stopper = asyncio.ensure_future(stop.wait())
            try:
                it = call.__aiter__()
                while True:
                    nxt = asyncio.ensure_future(it.__anext__())
                    done, _ = await asyncio.wait({nxt, stopper}, return_when=asyncio.FIRST_COMPLETED)
                    if stopper in done:
                        nxt.cancel()
                        call.cancel()
                        return
                    try:
                        env = nxt.result()
                    except StopAsyncIteration:
                        break
                    backoff = 0.5
                    yield env
            except grpc.aio.AioRpcError as exc:
                if stop.is_set():
                    return
                log.warning("broker subscription %s ended: %s %s; reconnecting in %.1fs", topics,
                            exc.code().name, (exc.details() or "")[:200], backoff)
            finally:
                stopper.cancel()
                call.cancel()
            try:
                await asyncio.wait_for(stop.wait(), timeout=backoff)
                return
            except asyncio.TimeoutError:
                backoff = min(backoff * 2, 15.0)
