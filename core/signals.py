# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.urls import reverse
from telegram import Bot, constants
from telegram.error import TelegramError, BadRequest
from telegram.helpers import escape_markdown
from django.contrib.sites.models import Site
import asyncio
import logging

logger = logging.getLogger(__name__)

from .models import Post

@receiver(post_save, sender=Post)
def auto_post_to_telegram(sender, instance, created, **kwargs):
    logger.critical("--- SIGNALS.PY VERSION: 2025-07-05T11:40 --- Loading now!") # Keep for now to confirm reload
    logger.info(f"Signal triggered for Post: '{instance.title}', Created: {created}, Published: {instance.is_published}")

    if created and instance.is_published:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        channel_ids = getattr(settings, 'TELEGRAM_CHANNEL_IDS', [])
        
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN is not defined in settings.py")
            return
        if not channel_ids:
            logger.warning("TELEGRAM_CHANNEL_IDS is empty or not defined in settings.py. No channels to post to.")
            return

        bot = Bot(token=bot_token)

        current_site = Site.objects.get_current()
        post_url = f"http://{current_site.domain}{instance.get_absolute_url()}" # Change to https if applicable

        escaped_title = escape_markdown(instance.title, version=2)
        
        raw_excerpt_or_content = getattr(instance, 'excerpt', None)
        content_for_message = ""

        if raw_excerpt_or_content:
            content_for_message = raw_excerpt_or_content
        else:
            # Only take a snippet if content is long
            if len(instance.content) > 200:
                content_for_message = instance.content[:200]
            else:
                content_for_message = instance.content
        
        # --- CRITICAL CHANGE HERE: Append '...' *before* escaping ---
        # Add the ellipsis directly to the content string, then escape the whole thing.
        # This ensures the dots in '...' are also escaped if necessary.
        if len(instance.content) > 200 or raw_excerpt_or_content: # Only add ellipsis if it's an excerpt or truncated content
             content_for_message += "..."

        escaped_excerpt_or_content = escape_markdown(content_for_message, version=2)

        escaped_read_more_text = escape_markdown("Read More Here", version=2)

        # Removed the emoji that might be corrupted in display due to encoding issues
        message_text = f"**New Post: {escaped_title}**\n\n"
        message_text += f"{escaped_excerpt_or_content}\n\n" # No need for '...' here anymore
        message_text += f"[{escaped_read_more_text}]({post_url})"

        async def send_telegram_message_async():
            for chat_id in channel_ids:
                try:
                    logger.info(f"Attempting to send '{instance.title}' to Telegram channel: {chat_id}")
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message_text,
                        parse_mode=constants.ParseMode.MARKDOWN_V2 # Back to MarkdownV2
                    )
                    logger.info(f"Successfully posted '{instance.title}' to Telegram channel: {chat_id}")
                except BadRequest as e:
                    logger.error(f"Telegram BadRequest Error for channel {chat_id} while posting '{instance.title}': {e}")
                except TelegramError as e:
                    logger.error(f"Telegram API Error for channel {chat_id} while posting '{instance.title}': {e}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred for channel {chat_id} while posting '{instance.title}' to Telegram: {e}")

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            loop.create_task(send_telegram_message_async())
        else:
            loop.run_until_complete(send_telegram_message_async())
    else:
        logger.info(f"Post '{instance.title}' not created or not published, skipping Telegram post.")