"""CLI для запуска основных операций zen-ref-agent."""

from __future__ import annotations

import argparse

from app.config import settings
from app.pipeline import create_draft_for_idea, run_research
from app.storage import Storage
from app.telegram_bot import TelegramSendError, send_markdown_message


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zen-ref-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("research", help="Загрузить RSS и сгенерировать идеи")
    subparsers.add_parser("list-ideas", help="Показать идеи")

    draft_parser = subparsers.add_parser("draft", help="Создать черновик по idea_id")
    draft_parser.add_argument("--idea-id", type=int, required=True)

    tg_parser = subparsers.add_parser("send-telegram", help="Отправить черновик в Telegram")
    tg_parser.add_argument("--draft-id", type=int, required=True)

    return parser


def _print_idea_row(idea: dict[str, object]) -> None:
    title = str(idea["title"])
    if len(title) > 90:
        title = title[:87] + "..."

    print(f"[{idea['id']}] risk={idea['risk_level']} | {title}")
    print(f"     source: {idea['source_title']}")
    print(f"     angle : {idea['angle']}")
    print(f"     link  : {idea['source_link']}")
    print("-")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    storage = Storage(settings.db_path)
    first_run = storage.init_db()
    if first_run:
        print(f"[OK] Создана новая БД: {settings.db_path}")

    if args.command == "research":
        print("[INFO] Старт research: читаю RSS и сохраняю данные...")

        try:
            stats = run_research(storage)
        except ModuleNotFoundError as exc:
            raise SystemExit(
                "Не хватает зависимости для RSS. Установите пакеты: pip install -r requirements.txt "
                f"(ошибка: {exc})"
            )

        print(f"[OK] Прочитано элементов из RSS: {stats['fetched']}")
        print(f"[OK] Сохранено source_items: {stats['source_saved']}")
        print(f"[OK] Создано ideas: {stats['ideas_saved']}")
        print(f"[INFO] Пропущено дублей: {stats['duplicates']}")

        if not settings.openai_api_key:
            print("[WARN] OPENAI_API_KEY не задан. Идеи созданы fallback-логикой.")
        return

    if args.command == "list-ideas":
        ideas = storage.list_ideas(limit=100)
        if not ideas:
            print("Идей пока нет. Сначала запустите: python -m app.cli research")
            return

        print(f"Найдено идей: {len(ideas)}")
        print("=" * 80)
        for idea in ideas:
            _print_idea_row(idea)
        return

    if args.command == "draft":
        try:
            draft_id = create_draft_for_idea(storage, idea_id=args.idea_id)
        except ValueError as exc:
            raise SystemExit(str(exc))

        draft = storage.get_draft(draft_id)
        risk = draft["risk_level"] if draft else "unknown"
        print(f"[OK] Черновик создан. draft_id={draft_id}, risk={risk}")
        return

    if args.command == "send-telegram":
        draft = storage.get_draft(args.draft_id)
        if not draft:
            raise SystemExit(f"Черновик с id={args.draft_id} не найден")

        text = (
            "Черновик для ручной проверки\n"
            f"draft_id: {draft['id']}\n"
            f"risk: {draft['risk_level']}\n\n"
            f"{draft['title']}\n\n"
            f"{draft['body_markdown']}\n\n"
            f"{draft['disclaimer']}"
        )

        try:
            send_markdown_message(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
                text=text,
            )
        except TelegramSendError as exc:
            raise SystemExit(f"Ошибка отправки в Telegram: {exc}")

        storage.mark_draft_sent(args.draft_id)
        print(f"[OK] Черновик {args.draft_id} отправлен в Telegram")


if __name__ == "__main__":
    main()
