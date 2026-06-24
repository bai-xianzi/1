from __future__ import annotations

import json
from pathlib import Path

from a_stock_quant.source_governance import (
    DatasetSourceBinding,
    SourceCapability,
    SourceDescriptor,
    SourceRole,
)


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    source_dir = ROOT / "configs" / "sources"
    sources = [
        SourceDescriptor.from_dict(
            load_json(path)
        )
        for path in sorted(source_dir.glob("*.json"))
    ]

    assert sources
    assert all(not item.enabled for item in sources)

    binding_payload = load_json(
        ROOT
        / "configs"
        / "source_bindings"
        / "a_stock_daily_bar.multi_source.template.json"
    )
    bindings = []
    for payload in binding_payload["bindings"]:
        bindings.append(
            DatasetSourceBinding(
                dataset_id=binding_payload["dataset_id"],
                source_id=payload["source_id"],
                role=SourceRole(payload["role"]),
                priority=payload["priority"],
                source_locator=payload["source_locator"],
                mapping_version=payload["mapping_version"],
                source_schema_version=payload[
                    "source_schema_version"
                ],
                required_capabilities=tuple(
                    SourceCapability(item)
                    for item in payload.get(
                        "required_capabilities",
                        [],
                    )
                ),
                enabled=payload["enabled"],
                notes=payload.get("notes", ""),
            )
        )

    assert len(bindings) == 3
    assert bindings[0].role is SourceRole.PRIMARY

    inventory = load_json(
        ROOT
        / "configs"
        / "inventory"
        / "seven_snapshot_inventory.template.json"
    )
    assert [
        item["dataset_id"]
        for item in inventory["datasets"]
    ] == [
        "hq",
        "hy",
        "gn",
        "kphq",
        "kphy",
        "kpgn",
        "zj",
    ]

    forbidden = (
        "D:\\Users\\Administrator",
        "C:\\Users\\Administrator",
    )
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {
            ".py",
            ".json",
            ".md",
        }:
            continue
        text = path.read_text(
            encoding="utf-8"
        )
        for marker in forbidden:
            assert marker not in text, (
                f"发现本机路径：{path}"
            )

    print(
        "TASK_015 source templates validation PASSED."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
