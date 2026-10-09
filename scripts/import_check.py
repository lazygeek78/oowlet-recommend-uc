"""Import every module of the engine; exit 1 listing the ones that fail.

    python scripts/import_check.py
"""

import importlib
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGES = ("ruc", "oowlet")


def main() -> int:
    sys.path.insert(0, str(ROOT))
    mods = []
    for pkg in PACKAGES:
        for p in sorted((ROOT / pkg).rglob("*.py")):
            parts = list(p.relative_to(ROOT).with_suffix("").parts)
            if parts[-1] == "__init__":
                parts = parts[:-1]
            mods.append(".".join(parts))
    failed = {}
    for m in mods:
        try:
            importlib.import_module(m)
        except Exception as e:  # noqa: BLE001 - report every failure
            failed[m] = f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}"
    for m, err in failed.items():
        print(f"✗ {m}: {err}", file=sys.stderr)
    print(f"✓ import check: {len(mods) - len(failed)}/{len(mods)} modules import")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
