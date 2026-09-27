import json
import sys
from pathlib import Path

from app.main import create_app

TARGET = Path(__file__).resolve().parents[1] / "packages/contracts/openapi.json"


def export(check: bool = False) -> None:
    content = (
        json.dumps(create_app().openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    if check:
        if not TARGET.exists() or TARGET.read_text() != content:
            raise SystemExit("OpenAPI drift: run pnpm contracts:generate")
    else:
        TARGET.write_text(content)


if __name__ == "__main__":
    export(check="--check" in sys.argv)
