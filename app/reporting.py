# This module will handle the generation of scheduled reports using Supabase.

import asyncio
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY
from .alerting import Alerter

class Reporting:
    """
    Generates and sends reports of top gainers by querying Supabase.
    """
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.alerter = Alerter()
        self.intervals = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "10m": timedelta(minutes=10),
            "1h": timedelta(hours=1)
        }

    async def run_scheduler(self):
        """
        Runs the report scheduler indefinitely.
        """
        while True:
            # This is a simple scheduler. For production, APScheduler would be more robust.
            # This loop will run approximately every minute.
            now = datetime.now(timezone.utc)
            
            # We can add logic here to run reports at their precise intervals
            # For simplicity, we'll run all reports every minute for now.
            for interval_name, delta in self.intervals.items():
                await self.generate_report(interval_name, delta)
            
            await asyncio.sleep(60)

    async def generate_report(self, interval_name, delta):
        """
        Generates a report for the top 5 gainers over a given interval.
        """
        start_time = (datetime.now(timezone.utc) - delta).isoformat()
        
        try:
            # This is a simplified query. For better performance on large datasets,
            # a SQL function in Supabase would be more efficient.
            
            # Get all symbols that have appeared in the last hour to keep the query focused
            recent_symbols_response = await asyncio.to_thread(
                self.supabase.table('price_history')
                .select('symbol')
                .gte('timestamp', (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat())
                .execute
            )
            if not recent_symbols_response.data:
                return
            
            unique_symbols = {item['symbol'] for item in recent_symbols_response.data}
            report_data = []

            for symbol in unique_symbols:
                # Get the current price
                current_price_response = await asyncio.to_thread(
                    self.supabase.table('price_history')
                    .select('price')
                    .eq('symbol', symbol)
                    .order('timestamp', desc=True)
                    .limit(1)
                    .execute
                )
                if not current_price_response.data:
                    continue
                current_price = current_price_response.data[0]['price']

                # Get the price from the start of the interval
                old_price_response = await asyncio.to_thread(
                    self.supabase.table('price_history')
                    .select('price')
                    .eq('symbol', symbol)
                    .gte('timestamp', start_time)
                    .order('timestamp', desc=False)
                    .limit(1)
                    .execute
                )
                
                if old_price_response.data:
                    old_price = old_price_response.data[0]['price']
                    if old_price > 0:
                        price_change = ((current_price - old_price) / old_price) * 100
                        if price_change > 0:
                            report_data.append({
                                "symbol": symbol,
                                "change": price_change,
                                "price": current_price
                            })

            # Sort by the biggest gainers and take the top 5
            top_5_gainers = sorted(report_data, key=lambda x: x['change'], reverse=True)[:5]

            if top_5_gainers:
                await self.alerter.send_gainer_report(top_5_gainers, interval_name)
        except Exception as e:
            print(f"Error generating report for {interval_name}: {e}")