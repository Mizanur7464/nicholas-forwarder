"""
Telegram Channel Forwarder Bot
Forwards/copies posts from a master channel to one or more forward channels automatically.
"""
import logging
import asyncio
from typing import Dict, List

from telegram import Update, InputMediaPhoto, Message
from telegram.ext import Application, ContextTypes

from config import (
    BOT_TOKEN,
    SOURCE_CHANNEL_ID,
    DESTINATION_CHANNEL_IDS,
    COPY_WITHOUT_FORWARD_LABEL,
    validate_config,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Don't print every HTTP request from httpx/telegram
logging.getLogger("httpx").setLevel(logging.WARNING)

# Channel IDs can be string or int; @username is also supported for public channels
SOURCE_ID = str(SOURCE_CHANNEL_ID).strip()
DEST_IDS = [str(dest_id).strip() for dest_id in DESTINATION_CHANNEL_IDS]


def _normalize_channel_ref(channel_ref: str) -> str:
    ref = channel_ref.strip()
    return ref.lower() if ref.startswith("@") else ref


def _matches_source_channel(message: Message, source_ref: str) -> bool:
    """Match numeric channel ID or public @username against an incoming channel post."""
    normalized_source = _normalize_channel_ref(source_ref)
    chat_id = str(message.chat.id) if message.chat else None
    if chat_id == source_ref.strip():
        return True

    username = getattr(message.chat, "username", None)
    if username and f"@{username.lower()}" == normalized_source:
        return True

    return False

# In-memory buffer for media groups so albums are sent together
MEDIA_GROUP_BUFFER: Dict[str, List] = {}
MEDIA_GROUP_DELAY_SECONDS = 1.0


async def _copy_or_forward_message(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    dest_id: str,
) -> None:
    if COPY_WITHOUT_FORWARD_LABEL:
        await context.bot.copy_message(
            chat_id=dest_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        logger.info("Message copied (no forward label) -> %s", dest_id)
    else:
        await message.forward(chat_id=dest_id)
        logger.info("Message forwarded -> %s", dest_id)


async def _flush_media_group(media_group_id: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send all photos from a media group as a single album with one caption."""
    messages = MEDIA_GROUP_BUFFER.pop(media_group_id, [])
    if not messages:
        return

    # Sort by message_id to preserve order
    messages.sort(key=lambda m: m.message_id)

    media_items = []
    for idx, msg in enumerate(messages):
        if not msg.photo:
            continue
        file_id = msg.photo[-1].file_id
        caption = msg.caption if idx == 0 else None
        # Keep original entities (URLs, bold, etc.) for the first item
        if idx == 0 and msg.caption_entities:
            media_items.append(
                InputMediaPhoto(
                    media=file_id,
                    caption=caption,
                    caption_entities=msg.caption_entities,
                )
            )
        else:
            media_items.append(InputMediaPhoto(media=file_id, caption=caption))

    if not media_items:
        return

    for dest_id in DEST_IDS:
        try:
            await context.bot.send_media_group(chat_id=dest_id, media=media_items)
            logger.info(
                "Media group %s forwarded as album with %d items -> %s",
                media_group_id,
                len(media_items),
                dest_id,
            )
        except Exception as e:
            logger.exception("Error sending media group to %s: %s", dest_id, e)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a short welcome message when user sends /start."""
    await update.message.reply_text(
        "Hello!\n\n"
        "I am a channel forwarder bot. Posts from the master channel are automatically forwarded to other channels.\n\n"
        "Contact the admin if you have any questions."
    )


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Copies/forwards new or edited channel posts to all destination channels."""
    message = update.channel_post or update.edited_channel_post
    if not message:
        return
    chat_id = str(message.chat.id) if message.chat else None

    logger.info("Received channel post from chat_id: %s", chat_id)

    # Only process posts from the master (source) channel
    if not _matches_source_channel(message, SOURCE_ID):
        logger.warning(
            "Skipping - post from chat_id=%s, but SOURCE_CHANNEL_ID is %s. "
            "Check: (1) Add bot as ADMIN to master channel (2) Use this chat_id in .env if this is your master channel.",
            chat_id, SOURCE_ID,
        )
        return

    # If we copy without forward label and this is part of a media group (album),
    # buffer the whole group and send it as a single album so caption is preserved.
    if COPY_WITHOUT_FORWARD_LABEL and getattr(message, "media_group_id", None) and message.photo:
        mg_id = str(message.media_group_id)
        MEDIA_GROUP_BUFFER.setdefault(mg_id, []).append(message)

        # Start a one-time task that flushes this group after a short delay
        async def delayed_flush() -> None:
            await asyncio.sleep(MEDIA_GROUP_DELAY_SECONDS)
            # Only flush if still buffered (i.e. not already sent)
            if mg_id in MEDIA_GROUP_BUFFER:
                await _flush_media_group(mg_id, context)

        # Only schedule flush once per group (when first message arrives)
        if len(MEDIA_GROUP_BUFFER[mg_id]) == 1:
            context.application.create_task(delayed_flush())

        return

    for dest_id in DEST_IDS:
        try:
            await _copy_or_forward_message(message, context, dest_id)
        except Exception as e:
            logger.exception("Error copying/forwarding message to %s: %s", dest_id, e)


def main() -> None:
    validate_config()

    from telegram.ext import MessageHandler, CommandHandler, filters

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(
        MessageHandler(filters.UpdateType.CHANNEL_POSTS, handle_channel_post),
    )

    logger.info(
        "Bot running... Master channel: %s -> Forward channels: %s",
        SOURCE_ID,
        ", ".join(DEST_IDS),
    )
    app.run_polling(
        allowed_updates=[Update.MESSAGE, Update.CHANNEL_POST, Update.EDITED_CHANNEL_POST]
    )


if __name__ == "__main__":
    main()
