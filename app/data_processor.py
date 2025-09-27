# This module will process the incoming data from the WebSocket.

import asyncio
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY, VOLATILITY_THRESHOLD
from .alerting import Alerter

class DataProcessor:
    """
    Processes and stores incoming ticker data from the WebSocket using Supabase.
    """
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.alerter = Alerter()

    async def process_message(self, message_data):
        """
        Processes a single message from the WebSocket.
        """
        usdt_pairs = [item for item in message_data if item['s'].endswith('USDT')]
        records_to_insert = []

        for item in usdt_pairs:
            records_to_insert.append({
                "symbol": item['s'],
                "price": float(item['c']),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # Batch insert the new price data
        if records_to_insert:
            try:
                await asyncio.to_thread(
                    self.supabase.table('price_history').insert(records_to_insert).execute
                )
            except Exception as e:
                print(f"Error inserting data into Supabase: {e}")

        # After inserting, check volatility for each updated pair
        for record in records_to_insert:
            await self.check_volatility(record['symbol'], record['price'])

    async def check_volatility(self, symbol, current_price):
        """
        Checks for significant price volatility over a 1-minute window using Supabase.
        """
        one_minute_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        try:
            # Get the oldest price from the last minute
            response = await asyncio.to_thread(
                self.supabase.table('price_history')
                .select('price')
                .eq('symbol', symbol)
                .gte('timestamp', one_minute_ago)
                .order('timestamp', desc=False)
                .limit(1)
                .execute
            )

            if response.data:
                old_price = response.data[0]['price']
                price_change = ((current_price - old_price) / old_price) * 100

                if abs(price_change) >= VOLATILITY_THRESHOLD:
                    await self.alerter.send_volatility_alert(symbol, price_change, current_price)
        except Exception as e:
            print(f"Error checking volatility for {symbol}: {e}")