import json
from pathlib import Path

from .models import LabelPreset, validate_label_size


def load_presets(path: Path) -> list[LabelPreset]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        raw_items = json.load(file)

    presets: list[LabelPreset] = []
    for item in raw_items:
        preset = LabelPreset(
            name=str(item["name"]),
            width_mm=float(item["width_mm"]),
            height_mm=float(item["height_mm"]),
            orientation=str(item.get("orientation", "portrait")),
        )
        validate_label_size(preset.width_mm, preset.height_mm)
        presets.append(preset)
    return presets


def save_presets(path: Path, presets: list[LabelPreset]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "name": preset.name,
            "width_mm": preset.width_mm,
            "height_mm": preset.height_mm,
            "orientation": preset.orientation,
        }
        for preset in presets
    ]
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def upsert_preset(presets: list[LabelPreset], preset: LabelPreset) -> list[LabelPreset]:
    next_presets = [item for item in presets if item.name != preset.name]
    next_presets.append(preset)
    return sorted(next_presets, key=lambda item: item.name.lower())
