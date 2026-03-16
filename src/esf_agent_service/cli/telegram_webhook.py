from __future__ import annotations

import argparse
import asyncio

import httpx

from esf_agent_service.core.config import get_settings
from esf_agent_service.integrations.telegram.client import TelegramBotClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Telegram webhooks for the ESF service.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="Register the configured webhook URL.")
    set_parser.add_argument(
        "--drop-pending-updates",
        action="store_true",
        help="Drop pending updates when setting the webhook.",
    )

    delete_parser = subparsers.add_parser("delete", help="Delete the configured webhook.")
    delete_parser.add_argument(
        "--drop-pending-updates",
        action="store_true",
        help="Drop pending updates when deleting the webhook.",
    )

    return parser


async def run_async(args: argparse.Namespace) -> int:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=30.0)) as client:
        telegram_client = TelegramBotClient(settings=settings, http_client=client)

        if args.command == "set":
            if not settings.telegram_webhook_url:
                raise SystemExit("TELEGRAM_WEBHOOK_URL must be set to register the webhook.")
            result = await telegram_client.set_webhook(
                url=settings.telegram_webhook_url,
                secret_token=(
                    settings.telegram_webhook_secret.get_secret_value()
                    if settings.telegram_webhook_secret is not None
                    else None
                ),
                drop_pending_updates=args.drop_pending_updates,
            )
            print(f"webhook_set={result}")
            return 0

        result = await telegram_client.delete_webhook(
            drop_pending_updates=args.drop_pending_updates
        )
        print(f"webhook_deleted={result}")
        return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return asyncio.run(run_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
