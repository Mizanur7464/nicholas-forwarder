"""Bot configuration - loads variables from .env"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL_ID = os.getenv("SOURCE_CHANNEL_ID")
COPY_WITHOUT_FORWARD_LABEL = os.getenv("COPY_WITHOUT_FORWARD_LABEL", "true").lower() == "true"

# Placeholder value - bot will not work with this
PLACEHOLDER_CHANNEL_ID = "-100xxxxxxxxxx"


def _parse_channel_ids(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [channel_id.strip() for channel_id in raw.split(",") if channel_id.strip()]


def _load_destination_channel_ids() -> list[str]:
    """Supports multiple destinations via DESTINATION_CHANNEL_IDS, with single-ID fallback."""
    destinations = _parse_channel_ids(os.getenv("DESTINATION_CHANNEL_IDS"))
    if destinations:
        return destinations

    single_destination = os.getenv("DESTINATION_CHANNEL_ID")
    if single_destination:
        return [single_destination.strip()]

    return []


DESTINATION_CHANNEL_IDS = _load_destination_channel_ids()


def validate_config():
    """Validates config - raises if any required value is missing or still placeholder."""
    if not BOT_TOKEN:
        raise ValueError("Set BOT_TOKEN in .env (get it from @BotFather)")
    if not SOURCE_CHANNEL_ID:
        raise ValueError("Set SOURCE_CHANNEL_ID in .env (master channel ID or @username)")
    if not DESTINATION_CHANNEL_IDS:
        raise ValueError(
            "Set DESTINATION_CHANNEL_IDS in .env (comma-separated list of forward channel IDs or @usernames)"
        )
    if SOURCE_CHANNEL_ID.strip() == PLACEHOLDER_CHANNEL_ID:
        raise ValueError(
            "SOURCE_CHANNEL_ID is still the placeholder (-100xxxxxxxxxx). "
            "Set your master channel's real ID or @username."
        )
    for dest_id in DESTINATION_CHANNEL_IDS:
        if dest_id == PLACEHOLDER_CHANNEL_ID:
            raise ValueError(
                "A destination channel ID is still the placeholder (-100xxxxxxxxxx). "
                "Set the real IDs or @usernames of all forward channels."
            )
    return True
