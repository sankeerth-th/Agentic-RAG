import subprocess
import tempfile
from pathlib import Path

from export_openapi import TARGET, export

export(check=True)
with tempfile.TemporaryDirectory() as directory:
    generated = Path(directory) / "api.d.ts"
    subprocess.run(
        [
            "pnpm",
            "exec",
            "openapi-typescript",
            str(TARGET),
            "--default-non-nullable",
            "false",
            "--immutable",
            "-o",
            str(generated),
        ],
        check=True,
    )
    committed = TARGET.parent / "generated/api.d.ts"
    if not committed.exists() or committed.read_bytes() != generated.read_bytes():
        raise SystemExit("TypeScript contract drift: run pnpm contracts:generate")
