from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from aeroplane import Aeroplane


def filter_aeroplanes(planes: List[Aeroplane], countries: List[str]) -> List[Aeroplane]:
    """Фильтрует список самолетов по списку стран регистрации."""
    if not countries:
        return planes
    lower_countries = [c.lower().strip() for c in countries if c.strip()]
    if not lower_countries:
        return planes
    return [p for p in planes if p.origin_country.lower() in lower_countries]


def get_aeroplanes_by_altitude(planes: List[Aeroplane], altitude_range: str) -> List[Aeroplane]:
    """Фильтрует самолеты, оставляя только те, что попадают в диапазон."""
    if not altitude_range:
        return planes
    try:
        if "," in altitude_range:
            parts = [p.strip() for p in altitude_range.split(",") if p.strip()]
            if len(parts) < 2:
                raise ValueError
            min_alt = float(parts[0])
            max_alt = float(parts[1])
        elif "-" in altitude_range and not altitude_range.startswith("-"):
            start_str, end_str = altitude_range.split("-", 1)
            min_alt = float(start_str.strip())
            max_alt = float(end_str.strip())
        else:
            raise ValueError

        return [p for p in planes if p.geo_altitude is not None and min_alt <= p.geo_altitude <= max_alt]
    except ValueError:
        print("[-] Предупреждение: Неверный формат диапазона высот. Фильтр пропущен.")
        return planes


def sort_aeroplanes(planes: List[Aeroplane]) -> List[Aeroplane]:
    """Сортирует самолеты по скорости на основе метода __lt__ класса."""
    return sorted(planes)


def get_top_aeroplanes(planes: List[Aeroplane], top_n: int) -> List[Aeroplane]:
    """Сортирует самолеты по высоте полета и возвращает ТОП N элементов."""
    sorted_by_alt = sorted(
        planes,
        key=lambda p: p.geo_altitude if p.geo_altitude is not None else -9999.0,
        reverse=True,
    )
    return sorted_by_alt[:top_n]


def print_aeroplanes(planes: List[Aeroplane]) -> None:
    """Выводит список объектов Aeroplane в виде консольной ASCII-таблицы."""
    if not planes:
        print("\nНет данных для отображения по выбранным критериям.")
        return

    col1, col2, col3, col4 = (
        "Позывной (Callsign)",
        "Страна регистрации",
        "Скорость (м/с)",
        "Высота (м)",
    )
    header = f"{col1:<20} | {col2:<25} | {col3:<15} | {col4:<12}"
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))

    for p in planes:
        v = f"{p.velocity:.1f}" if p.velocity is not None else "N/A"
        alt = f"{p.geo_altitude:.1f}" if p.geo_altitude is not None else "N/A"
        print(f"{p.callsign:<20} | {p.origin_country:<25} | {v:<15} | {alt:<12}")
    print("=" * len(header) + "\n")
