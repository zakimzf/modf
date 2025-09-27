# This module handles sending alerts via Email (Supabase) and Telegram.

import httpx
import telegram
from .config import (
    SUPABASE_URL, SUPABASE_KEY, FROM_EMAIL, TO_EMAIL,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

class Alerter:
    """
    Handles the sending of alerts via configured notification channels.
    """
    def __init__(self):
        # Email (Supabase Edge Function) configuration
        self.email_enabled = all([SUPABASE_URL, SUPABASE_KEY, FROM_EMAIL, TO_EMAIL])
        if self.email_enabled:
            self.edge_function_url = f"{SUPABASE_URL}/functions/v1/send-email"
            self.headers = {"Authorization": f"Bearer {SUPABASE_KEY}"}

        # Telegram configuration
        self.telegram_enabled = all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID])
        if self.telegram_enabled:
            self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    async def _send_email(self, subject, html_content):
        """Invokes the Supabase Edge Function to send an email."""
        if not self.email_enabled:
            return

        payload = {
            "to": TO_EMAIL, "from": FROM_EMAIL,
            "subject": subject, "html_content": html_content
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.edge_function_url, headers=self.headers, json=payload)
                response.raise_for_status()
                print(f"Successfully sent email for subject: {subject}")
            except Exception as e:
                print(f"Error sending email: {e}")

    async def _send_telegram(self, message):
        """Sends a message to the configured Telegram chat."""
        if not self.telegram_enabled:
            return
        
        try:
            await self.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
            print("Successfully sent Telegram message.")
        except Exception as e:
            print(f"Error sending Telegram message: {e}")

    async def send_volatility_alert(self, symbol, price_change, current_price):
        """Sends a volatility alert to all configured channels."""
        direction = "increased" if price_change > 0 else "decreased"
        
        # Email content
        email_subject = f"Volatility Alert: {symbol} has {direction} by {price_change:.2f}%"
        email_html = f"""
        <strong>Volatility Alert</strong>
        <p>The price of {symbol} has {direction} by {price_change:.2f}% in the last minute.</p>
        <p>The current price is {current_price}.</p>
        """
        
        # Telegram content
        telegram_message = (
            f"<b>Volatility Alert</b>\n"
            f"Symbol: {symbol}\n"
            f"Change: {price_change:.2f}%\n"
            f"Price: {current_price}"
        )
        
        await self._send_email(email_subject, email_html)
        await self._send_telegram(telegram_message)

    async def send_gainer_report(self, report_data, interval):
        """Sends a gainer report to all configured channels."""
        # Email content
        email_subject = f"Top Gainers Report ({interval})"
        email_html = f"<strong>Top {len(report_data)} Gainers for the last {interval}</strong><br><br>"
        for item in report_data:
            email_html += f"Symbol: {item['symbol']}, Change: {item['change']:.2f}%, Price: {item['price']}<br>"
            
        # Telegram content
        telegram_message = f"<b>Top {len(report_data)} Gainers ({interval})</b>\n"
        for item in report_data:
            telegram_message += f"{item['symbol']}: {item['change']:.2f}% (Price: {item['price']})\n"
            
        await self._send_email(email_subject, email_html)
        await self._send_telegram(telegram_message)