# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.urls import reverse
from telegram import Bot, constants
from telegram.error import TelegramError, BadRequest
from telegram.helpers import escape_markdown # <--- THIS IMPORT IS CRUCIAL
from django.contrib.sites.models import Site
import asyncio
import logging

logger = logging.getLogger(__name__)

from .models import Post

@receiver(post_save, sender=Post)
def auto_post_to_telegram(sender, instance, created, **kwargs):
    logger.info(f"Signal triggered for Post: '{instance.title}', Created: {created}, Published: {instance.is_published}")

    if created and instance.is_published: # Ensure post is new and published
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
        # Ensure the URL is fully qualified with the domain
        # Adjust 'http' to 'https' if your production site uses HTTPS
        # Also, make sure current_site.domain is correctly configured (e.g., example.com, not localhost:8000)
        post_url = f"http://{current_site.domain}{instance.get_absolute_url()}" # Change to https if applicable

        # --- THIS IS THE CRITICAL PART: ESCAPING MARKDOWN SPECIAL CHARACTERS ---
        # Use escape_markdown() with version=2 for MARKDOWN_V2 parsing
        escaped_title = escape_markdown(instance.title, version=2)
        
        # Safely get excerpt or content, then escape it
        raw_excerpt_or_content = getattr(instance, 'excerpt', None)
        if raw_excerpt_or_content:
            escaped_excerpt_or_content = escape_markdown(raw_excerpt_or_content, version=2)
        else: # Fallback to content snippet if no excerpt
            content_snippet = instance.content[:200] if len(instance.content) > 200 else instance.content
            escaped_excerpt_or_content = escape_markdown(content_snippet, version=2)

        # The text for the "Read More Here" link itself might contain special characters if you customize it
        # It's good practice to escape all text parts of the message.
        escaped_read_more_text = escape_markdown("Read More Here", version=2)

        message_text = f"📢 **New Post: {escaped_title}**\n\n"
        message_text += f"{escaped_excerpt_or_content}...\n\n"
        message_text += f"[{escaped_read_more_text}]({post_url})" # The URL part doesn't need escaping

        async def send_telegram_message_async():
            for chat_id in channel_ids: # Iterate through the list of channel IDs
                try:
                    logger.info(f"Attempting to send '{instance.title}' to Telegram channel: {chat_id}")
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message_text,
                        parse_mode=constants.ParseMode.MARKDOWN_V2
                    )
                    logger.info(f"Successfully posted '{instance.title}' to Telegram channel: {chat_id}")
                except BadRequest as e: # Catches specific 400 errors from Telegram API
                    # Examples: "Chat not found", "Bot was blocked by the user", "Can't parse entities"
                    logger.error(f"Telegram BadRequest Error for channel {chat_id} while posting '{instance.title}': {e}")
                except TelegramError as e: # Catches other Telegram-specific errors
                    logger.error(f"Telegram API Error for channel {chat_id} while posting '{instance.title}': {e}")
                except Exception as e: # Catch any other unexpected errors
                    logger.error(f"An unexpected error occurred for channel {chat_id} while posting '{instance.title}' to Telegram: {e}")

        # Ensure event loop is handled correctly for Django's sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # If loop is already running (e.g., in async framework), create task
        # Otherwise, run until complete (for typical Django sync view/admin)
        if loop.is_running():
            loop.create_task(send_telegram_message_async())
        else:
            loop.run_until_complete(send_telegram_message_async())
    else:
        logger.info(f"Post '{instance.title}' not created or not published, skipping Telegram post.")