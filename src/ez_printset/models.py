from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LabelPreset:
    name: str
    width_mm: float
    height_mm: float
    orientation: str = "portrait"

    @property
    def form_name(self) -> str:
        name = re.sub(r"\s+", " ", self.name.strip())
        name = re.sub(r'[\\/:*?"<>|,;=]', "-", name)
        if name:
            return name[:31]

        width = _clean_number(self.width_mm)
        height = _clean_number(self.height_mm)
        return f"EZ_LABEL_{width}x{height}_MM"


def _clean_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value).replace(".", "_")


def validate_label_size(width_mm: float, height_mm: float) -> None:
    if width_mm <= 0 or height_mm <= 0:
        raise ValueError("Kich thuoc phai lon hon 0 mm.")
    if width_mm > 1000 or height_mm > 1000:
        raise ValueError("Kich thuoc toi da duoc gioi han 1000 mm.")
