"""Generate the Python protobuf / gRPC code this module imports, in the same
layout as the repository's proto Makefile (gen/<dir>/<pkg>/<file>_pb2.py),
under ./oowlet/gen so imports read `from oowlet.gen.recommenduc.commonpb
import common_pb2`.

    python scripts/gen_protos.py <proto_root>

Two groups, compiled separately because they import differently:
  - recommenduc/, eventlayer/: full-path imports, -I<proto_root>
  - feature_service/: bare imports ("fs_common.proto"), -I<proto_root>/feature_service
    (the same flags as the repository proto Makefile uses for it)
Each file is moved into its *pb/ package and the generated imports and
descriptor module names are rewritten to oowlet.gen.<dir>.<pkg>.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOTED: dict[str, dict[str, str]] = {
    "recommenduc": {
        "common": "commonpb",
        "engagement": "engagementpb",
        "profile": "profilepb",
        "content": "contentpb",
        "graph": "graphpb",
        "recommendation": "recommendationpb",
        "history": "historypb",
        "events": "eventspb",
        "service": "servicepb",
    },
    "eventlayer": {
        "base": "basepb",
        "broker_service": "brokerservicepb",
        "post_events": "posteventspb",
        "behavior_events": "behavioreventspb",
    },
}
BARE: dict[str, dict[str, str]] = {
    "feature_service": {
        "fs_common": "fscommonpb",
        "feature": "featurepb",
    },
}

OUT = Path("oowlet/gen")
STAGE = Path("oowlet/.gen-stage")


def _protoc(includes: list[str], out: Path, files: list[str]) -> bool:
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "grpc_tools.protoc", *(f"-I{i}" for i in includes),
           f"--python_out={out}", f"--pyi_out={out}", f"--grpc_python_out={out}", *files]
    return subprocess.run(cmd).returncode == 0


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    missing = [f"{root}/{d}/{s}.proto" for g in (ROOTED, BARE) for d, ss in g.items() for s in ss
               if not (root / d / f"{s}.proto").is_file()]
    if missing:
        print("✗ not found (set PROTO_DIR):\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1
    shutil.rmtree(STAGE, ignore_errors=True)
    shutil.rmtree(OUT, ignore_errors=True)

    rooted_files = [f"{d}/{s}.proto" for d, ss in ROOTED.items() for s in ss]
    if not _protoc([str(root)], STAGE / "rooted", rooted_files):
        print("✗ protoc failed (recommenduc / eventlayer)", file=sys.stderr)
        return 1
    for d, ss in BARE.items():
        if not _protoc([str(root / d)], STAGE / "bare" / d, [f"{s}.proto" for s in ss]):
            print(f"✗ protoc failed ({d})", file=sys.stderr)
            return 1

    # (dir, module) -> dotted package
    target: dict[tuple[str, str], str] = {}
    for g in (ROOTED, BARE):
        for d, ss in g.items():
            for s, pkg in ss.items():
                target[(d, s)] = f"oowlet.gen.{d}.{pkg}"
                dst = OUT / d / pkg
                dst.mkdir(parents=True, exist_ok=True)
                src = STAGE / "rooted" / d if g is ROOTED else STAGE / "bare" / d
                for f in src.glob(f"{s}_pb2*.py*"):
                    f.rename(dst / f.name)

    dirs = "|".join(ROOTED)
    rooted_imp = re.compile(rf"^from ({dirs}) import (\w+?)(_pb2(?:_grpc)?)\b", re.M)
    rooted_desc = re.compile(rf"(BuildTopDescriptorsAndMessages\(DESCRIPTOR, )'({dirs})\.(\w+?)_pb2'")
    bare_mods = {s: d for d, ss in BARE.items() for s in ss}
    bare_re = "|".join(bare_mods)
    bare_imp = re.compile(rf"^import ({bare_re})(_pb2(?:_grpc)?) as ", re.M)
    bare_desc = re.compile(rf"(BuildTopDescriptorsAndMessages\(DESCRIPTOR, )'({bare_re})_pb2'")

    def fix(text: str) -> str:
        text = rooted_imp.sub(lambda m: f"from {target[(m.group(1), m.group(2))]} import {m.group(2)}{m.group(3)}", text)
        text = rooted_desc.sub(lambda m: f"{m.group(1)}'{target[(m.group(2), m.group(3))]}.{m.group(3)}_pb2'", text)
        text = bare_imp.sub(lambda m: f"from {target[(bare_mods[m.group(1)], m.group(1))]} import {m.group(1)}{m.group(2)} as ", text)
        text = bare_desc.sub(lambda m: f"{m.group(1)}'{target[(bare_mods[m.group(2)], m.group(2))]}.{m.group(2)}_pb2'", text)
        return text

    n = 0
    for f in list(OUT.rglob("*.py")) + list(OUT.rglob("*.pyi")):
        s = f.read_text(encoding="utf-8")
        t = fix(s)
        if t != s:
            f.write_text(t, encoding="utf-8")
            n += 1
    for p in [OUT.parent, OUT, *(q for q in OUT.rglob("*") if q.is_dir())]:
        (p / "__init__.py").touch()
    left = [str(p) for p in STAGE.rglob("*.py*")]
    shutil.rmtree(STAGE, ignore_errors=True)
    if left:
        print("✗ generated but not placed: " + ", ".join(left), file=sys.stderr)
        return 1
    total = sum(len(ss) for g in (ROOTED, BARE) for ss in g.values())
    print(f"✓ generated {total} protos into {OUT} ({n} files rewritten)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
