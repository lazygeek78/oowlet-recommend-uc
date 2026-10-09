"""Process wiring: gRPC API, event-layer consumer / publisher, feature
service client, periodic training."""

from __future__ import annotations

import asyncio
import json
import logging
import signal
from pathlib import Path

import grpc

from .api.auth import TokenAuthenticator
from .api.servicers import add_all
from .app import App
from .config import Settings
from .events.broker import BrokerClient, BrokerEndpoint
from .events.consumer import EventConsumer, EventPublisher
from .intelligence.feature_client import FeatureServiceClient
from .training import trainer

log = logging.getLogger("ruc.server")


def _p(s: str) -> Path | None:
    return Path(s) if s else None


def build_broker(s: Settings) -> BrokerClient | None:
    b = s.broker
    if not b.address:
        return None
    return BrokerClient(BrokerEndpoint(address=b.address, token_file=_p(b.token_file), ca_file=_p(b.ca_file),
                                       cert_file=_p(b.cert_file), key_file=_p(b.key_file)),
                        source=f"oowlet-recommend-uc/{s.instance_id}")


class Server:
    def __init__(self, s: Settings) -> None:
        self.s = s
        fs = FeatureServiceClient(s.feature_service) if s.feature_service.address else None
        self.app = App(s, features=fs)
        self.auth = TokenAuthenticator(s.auth.tokens_file)
        self.broker = build_broker(s)
        self.consumer = EventConsumer(self.app, self.broker) if self.broker else None
        if self.broker:
            self.app.publish = EventPublisher(self.broker).publish
        self.grpc: grpc.aio.Server | None = None
        self.port = 0
        self._stop = asyncio.Event()
        self._train_task: asyncio.Task | None = None

    async def start(self) -> int:
        await self.app.start()
        sv = self.s.server
        opts = [("grpc.max_receive_message_length", sv.max_message_bytes),
                ("grpc.max_send_message_length", sv.max_message_bytes)]
        self.grpc = grpc.aio.server(options=opts)
        add_all(self.grpc, self.app, self.auth)
        addr = f"{sv.host}:{sv.port}"
        if sv.tls_enabled:
            creds = grpc.ssl_server_credentials(
                [(Path(sv.tls_key_file).read_bytes(), Path(sv.tls_cert_file).read_bytes())],
                root_certificates=Path(sv.tls_client_ca_file).read_bytes() if sv.tls_client_ca_file else None,
                require_client_auth=bool(sv.tls_client_ca_file))
            self.port = self.grpc.add_secure_port(addr, creds)
        else:
            self.port = self.grpc.add_insecure_port(addr)
        await self.grpc.start()
        if self.consumer:
            await self.consumer.start()
        if self.s.training.interval_minutes > 0:
            self._train_task = asyncio.create_task(self._train_loop())
        log.info("oowlet-recommend-uc listening on %s:%d (tls=%s, events=%s, feature service=%s)", sv.host,
                 self.port, sv.tls_enabled, bool(self.broker), bool(self.app.features))
        return self.port

    async def _train_loop(self) -> None:
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), self.s.training.interval_minutes * 60)
                return
            except asyncio.TimeoutError:
                pass
            try:
                report = await trainer.run(self.app)
                log.info("training: %s", json.dumps(report, default=str))
            except Exception:  # noqa: BLE001
                log.exception("training failed")

    async def stop(self) -> None:
        self._stop.set()
        if self._train_task:
            self._train_task.cancel()
            await asyncio.gather(self._train_task, return_exceptions=True)
        if self.consumer:
            await self.consumer.stop()
        if self.grpc:
            await self.grpc.stop(self.s.server.shutdown_grace_seconds)
        await self.app.close()
        if self.broker:
            await self.broker.close()

    async def run_forever(self) -> None:
        await self.start()
        loop = asyncio.get_running_loop()
        done = asyncio.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, done.set)
        await done.wait()
        log.info("shutting down")
        await self.stop()
