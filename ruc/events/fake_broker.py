"""An in-memory EventBrokerService for tests and local development.

    broker = FakeBroker()
    port = await broker.start("127.0.0.1:0")
    ...
    await broker.stop()

Publish delivers the envelope to every live subscription whose topics
include its event_type (no persistence, no offsets, no consumer-group
sharing: each subscription gets every event of its topics).
"""

from __future__ import annotations

import asyncio
import logging

import grpc

from oowlet.gen.eventlayer.brokerservicepb import broker_service_pb2 as bs
from oowlet.gen.eventlayer.brokerservicepb import broker_service_pb2_grpc as bsg

log = logging.getLogger("ruc.fake_broker")


class FakeBroker(bsg.EventBrokerServiceServicer):
    def __init__(self) -> None:
        self._subs: list[tuple[frozenset[str], asyncio.Queue]] = []
        self._server: grpc.aio.Server | None = None
        self.published: list = []

    async def start(self, address: str = "127.0.0.1:0") -> int:
        self._server = grpc.aio.server(options=[("grpc.max_receive_message_length", 16 << 20),
                                                ("grpc.max_send_message_length", 16 << 20)])
        bsg.add_EventBrokerServiceServicer_to_server(self, self._server)
        port = self._server.add_insecure_port(address)
        await self._server.start()
        return port

    async def stop(self) -> None:
        if self._server is not None:
            await self._server.stop(0.5)

    def subscribers(self, topic: str) -> int:
        return sum(1 for topics, _ in self._subs if topic in topics)

    async def PublishEvent(self, request, context):
        env = request.event
        self.published.append(env)
        for topics, q in list(self._subs):
            if env.event_type in topics:
                q.put_nowait(env)
        return bs.PublishEventResponse(event_id=env.event_id, persisted=True)

    async def SubscribeEvents(self, request, context):
        q: asyncio.Queue = asyncio.Queue()
        entry = (frozenset(request.topics), q)
        self._subs.append(entry)
        try:
            while True:
                yield await q.get()
        finally:
            self._subs.remove(entry)

    async def GetEventStatus(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "not in the fake broker")

    async def GetTopics(self, request, context):
        return bs.TopicsResponse()
