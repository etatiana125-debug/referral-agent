import argparse

from app.services.pin_import_service import PinImportService


def main() -> None:
    """CLI-скрипт для ручного импорта CSV с Pinterest-пинами."""
    parser = argparse.ArgumentParser(description="Импорт Pinterest-пинов из CSV в JSON")
    parser.add_argument(
        "--csv",
        default="data/pinterest_pins_example.csv",
        help="Путь к CSV-файлу (по умолчанию: data/pinterest_pins_example.csv)",
    )
    args = parser.parse_args()

    service = PinImportService(output_file_path="data/pins.json")
    imported_count = service.import_from_csv(csv_file_path=args.csv)

    print(f"Импорт завершен. Загружено пинов: {imported_count}")
    print("Результат сохранен в data/pins.json")


if __name__ == "__main__":
    main()
