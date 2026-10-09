"""oowlet-recommend-uc [serve|check|version|selftest]

  serve     start the gRPC API and the event consumer (default)
  check     validate the configuration and reach the event layer and the
            feature service; exit 1 if anything is wrong
  version   version, commit and build time
  selftest  import every module (used by `make build` on the executable)
Configuration: RUC_* environment variables (see .env.example).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

PACKAGES = ("ruc", "oowlet")


def _build_info() -> dict[str, str]:
    try:
        from . import _build_info  # type: ignore[attr-defined]
    except ImportError:
        return {"version": "dev", "commit": "unknown", "built": "unknown"}
    return {"version": _build_info.VERSION, "commit": _build_info.COMMIT, "built": _build_info.BUILT}


def _setup_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _serve() -> int:
    from .config import ConfigError, Settings
    from .server import Server
    try:
        s = Settings.load()
    except ConfigError as exc:
        print(f"✗ not starting: {exc}", file=sys.stderr)
        return 2
    _setup_logging(s.log_level)

    async def run() -> int:
        # grpc.aio channels and servers belong to the loop they are created
        # on: build everything inside the running loop
        try:
            server = Server(s)
        except (ValueError, OSError) as exc:
            print(f"✗ not starting: {exc}", file=sys.stderr)
            return 2
        await server.run_forever()
        return 0
    return asyncio.run(run())


async def _reach(target: str, what: str, ca: str = "") -> str | None:
    import grpc
    from pathlib import Path
    ch = (grpc.aio.secure_channel(target, grpc.ssl_channel_credentials(Path(ca).read_bytes())) if ca
          else grpc.aio.insecure_channel(target))
    try:
        await asyncio.wait_for(ch.channel_ready(), 5)
        return None
    except asyncio.TimeoutError:
        return f"{what} at {target} not reachable within 5 s"
    finally:
        await ch.close()


def _check() -> int:
    from .api.auth import TokenAuthenticator
    from .config import ConfigError, Settings
    try:
        s = Settings.load()
        TokenAuthenticator(s.auth.tokens_file)
    except (ConfigError, ValueError, OSError) as exc:
        print(f"✗ {exc}")
        return 1
    problems = []
    if s.broker.address:
        problems.append(asyncio.run(_reach(s.broker.address, "event layer", s.broker.ca_file)))
    else:
        print("  ⚠ RUC_BROKER__ADDRESS not set: no event-layer consumer (API only)")
    if s.feature_service.address:
        problems.append(asyncio.run(_reach(s.feature_service.address, "feature service", s.feature_service.ca_file)))
    else:
        print("  ⚠ RUC_FEATURE_SERVICE__ADDRESS not set: no feature-service enrichment or write-back")
    problems = [p for p in problems if p]
    for p in problems:
        print(f"✗ {p}")
    if not problems:
        print("✓ configuration valid")
    return 1 if problems else 0


def _version() -> int:
    i = _build_info()
    print(f"oowlet-recommend-uc {i['version']} (commit {i['commit']}, built {i['built']})")
    return 0


def _selftest() -> int:
    import importlib
    import pkgutil
    count, failed = 0, []
    for name in PACKAGES:
        pkg = importlib.import_module(name)
        for info in pkgutil.walk_packages(pkg.__path__, prefix=name + "."):
            try:
                importlib.import_module(info.name)
                count += 1
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{info.name}: {type(exc).__name__}: {exc}")
    for f in failed:
        print(f"  ✗ {f}", file=sys.stderr)
    if failed or not count:
        print(f"✗ selftest: {len(failed)} module(s) failed", file=sys.stderr)
        return 1
    print(f"✓ selftest: {count} modules import")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="oowlet-recommend-uc", description=__doc__.split("\n")[0])
    ap.add_argument("command", nargs="?", default="serve", choices=("serve", "check", "version", "selftest"))
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    return {"serve": _serve, "check": _check, "version": _version, "selftest": _selftest}[a.command]()


if __name__ == "__main__":
    sys.exit(main())
