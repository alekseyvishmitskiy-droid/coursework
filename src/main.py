import sys

from dotenv import load_dotenv

import utils
from aeroplane import Aeroplane
from aeroplanes_api import AeroplanesAPI
from json_saver import JSONSaver


def user_interaction() -> None:
    """Интерактивная функция для взаимодействия с пользователем."""
    api = AeroplanesAPI()
    json_saver = JSONSaver()

    print("=" * 65)
    print(" СИСТЕМА МОНИТОРИНГА ГРАЖДАНСКОЙ АВИАЦИИ (OpenSky & OSM)")
    print("=" * 65)

    msg_1 = "1. Введите название страны на английском для сканирования (например, Spain): "
    country = input(msg_1).strip()
    if not country:
        print("[-] Название страны не может быть пустым. Программа завершена.")
        return

    print(f"[...] Выполняется запрос к API для страны '{country}'...")
    raw_aeroplanes = api.get_aeroplanes(country)

    aeroplanes = Aeroplane.cast_to_object_list(raw_aeroplanes)
    print(f"[+] Успешно получено active-самолетов из API: {len(aeroplanes)}")

    if not aeroplanes:
        print("[-] Нет данных для обработки. Выход.")
        return

    for plane in aeroplanes:
        json_saver.add_aeroplane(plane)
    print("[+] Все новые данные зафиксированы в файле 'data/aeroplanes.json'.")

    try:
        msg_2 = "\n2. Введите количество самолетов для вывода в ТОП по высоте (N): "
        top_n_input = input(msg_2).strip()
        top_n = int(top_n_input) if top_n_input else 5
    except ValueError:
        print("[*] Некорректный ввод. Установлено дефолтное значение: 5")
        top_n = 5

    msg_3 = "3. Введите страны регистрации для фильтрации (через пробел, или Enter): "
    filter_words = input(msg_3).strip().split()

    msg_4 = "4. Введите диапазон высот полета (например, 4000-11000, или Enter): "
    altitude_range = input(msg_4).strip()

    print("\n[...] Извлечение накопленных данных из файла и применение фильтров...")
    cached_planes = json_saver.get_aeroplanes()

    filtered_aeroplanes = utils.filter_aeroplanes(cached_planes, filter_words)
    ranged_aeroplanes = utils.get_aeroplanes_by_altitude(filtered_aeroplanes, altitude_range)

    top_aeroplanes = utils.get_top_aeroplanes(ranged_aeroplanes, top_n)
    final_aeroplanes = utils.sort_aeroplanes(top_aeroplanes)

    print(f"\n[+] РЕЗУЛЬТАТ ОБРАБОТКИ (Выведено ТОП-{top_n} по высоте, отсортировано по скорости):")
    utils.print_aeroplanes(final_aeroplanes)


if __name__ == "__main__":
    load_dotenv()
    try:
        user_interaction()
    except KeyboardInterrupt:
        print("\n\n[-] Программа экстренно завершена пользователем.")
        sys.exit(0)
