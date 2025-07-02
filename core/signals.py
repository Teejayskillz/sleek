# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.urls import reverse
from telegram import Bot, constants
from telegram.error import TelegramError # <--- ADD THIS IMPORT for specific error handling
from django.contrib.sites.models import Site
import asyncio

from .models import Post

@receiver(post_save, sender=Post)
def auto_post_to_telegram(sender, instance, created, **kwargs):
    if created and instance.is_published:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        current_site = Site.objects.get_current()
        # Ensure the URL is fully qualified with the domain
        # If you are serving on HTTPS in production, make sure current_site.domain reflects that
        post_url = f"https://{current_site.domain}{instance.get_absolute_url()}"

        message_text = f"📢 **New Post: {instance.title}**\n\n"
        message_text += f"{instance.excerpt or instance.content[:200]}...\n\n"
        message_text += f"[Read More Here]({post_url})"

        try:
            async def send_telegram_message_async():
                # Add a timeout here for the send_message call
                await bot.send_message(
                    chat_id=settings.TELEGRAM_CHANNEL_ID,
                    text=message_text,
                    parse_mode=constants.ParseMode.MARKDOWN,
                    timeout=20 # <--- ADD A TIMEOUT (in seconds). Default is often 5-10s.
                )

            asyncio.run(send_telegram_message_async())

            print(f"Successfully posted '{instance.title}' to Telegram.")

        except TelegramError as e: # <--- CATCH SPECIFIC TELEGRAM ERRORS
            print(f"Telegram API Error posting '{instance.title}': {e}")
        except Exception as e: # Catch any other unexpected errors
            print(f"An unexpected error occurred while posting '{instance.title}' to Telegram: {e}")