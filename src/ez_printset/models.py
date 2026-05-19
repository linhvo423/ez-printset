from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LabelPreset:
    name: str
    width_mm: float
    height_mm: float
    orientation: str = "portrait"
    liner_left_mm: float = 0
    liner_right_mm: float = 0

    @property
    def effective_width_mm(self) -> float:
        return self.width_mm + self.liner_left_mm + self.liner_right_mm

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


def validate_liner_width(left_mm: float, right_mm: float) -> None:
    if left_mm < 0 or right_mm < 0:
        raise ValueError("Liner trai/phai khong duoc nho hon 0 mm.")
    if left_mm > 100 or right_mm > 100:
        raise ValueError("Liner trai/phai toi da duoc gioi han 100 mm.")
