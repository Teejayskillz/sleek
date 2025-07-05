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
    # Keep this for a while to confirm your code is reloading!
    logger.critical("--- SIGNALS.PY VERSION: 2025-07-06T00:55 --- Loading now!") 
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
        post_url = f"http://{current_site.domain}{instance.get_absolute_url()}" 

        # --- IMPORTANT NEW STEP: ESCAPE THE POST_URL ITSELF ---
        # When displaying a raw URL in MarkdownV2, its special characters must also be escaped.
        escaped_post_url = escape_markdown(post_url, version=2)
        logger.critical(f"DEBUG: Original URL: {post_url}, Escaped URL: {escaped_post_url}") # Helpful debug line

        # --- GET THUMBNAIL URL ---
        # IMPORTANT: Replace 'instance.image' with your actual ImageField name 
        photo_url = None
        if hasattr(instance, 'image') and instance.image and instance.image.url:
            photo_url = f"http://{current_site.domain}{instance.image.url}" # Adjust to https if applicable
        elif hasattr(instance, 'thumbnail') and instance.thumbnail and instance.thumbnail.url:
            photo_url = f"http://{current_site.domain}{instance.thumbnail.url}"
        
        if not photo_url:
            logger.warning(f"Post '{instance.title}' has no image/thumbnail. Will send a text-only message.")

        # --- ESCAPING MARKDOWN SPECIAL CHARACTERS FOR CAPTION ---
        escaped_title = escape_markdown(instance.title, version=2)
        
        content_for_message = ""
        if getattr(instance, 'excerpt', None):
            content_for_message = instance.excerpt
        else:
            content_for_message = instance.content

        if len(content_for_message) > 200:
            content_for_message = content_for_message[:200] + "..."
        elif getattr(instance, 'excerpt', None):
            content_for_message += "..."

        escaped_excerpt_or_content = escape_markdown(content_for_message, version=2)

        # --- CONSTRUCT CAPTION TEXT WITH DIRECT ESCAPED POST URL ---
        caption_text = f"📢 **{escaped_title}**\n\n"
        caption_text += f"{escaped_excerpt_or_content}\n\n"
        caption_text += f"🔗 {escaped_post_url}" # <--- NOW USING THE ESCAPED URL

        async def send_telegram_message_async():
            for chat_id in channel_ids:
                try:
                    logger.info(f"Attempting to send '{instance.title}' to Telegram channel: {chat_id}")
                    
                    if photo_url:
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=photo_url,
                            caption=caption_text,
                            parse_mode=constants.ParseMode.MARKDOWN_V2 # This should work now
                        )
                    else:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=caption_text,
                            parse_mode=constants.ParseMode.MARKDOWN_V2
                        )
                    logger.info(f"Successfully posted '{instance.title}' to Telegram channel: {chat_id}")
                except BadRequest as e:
                    logger.error(f"Telegram BadRequest Error for channel {chat_id} while posting '{instance.title}': {e}")
                except TelegramError as e:
                    logger.error(f"Telegram API Error for channel {chat_id} while posting '{instance.title}': {e}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred for channel {chat_id} while posting '{instance.title}' to Telegram: {e}")

        # Ensure event loop is handled correctly for Django's sync context
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