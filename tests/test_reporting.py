import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.reporting import Reporting
from datetime import datetime, timedelta, timezone

@pytest.fixture
def mock_supabase_client():
    """Fixture to create a mock Supabase client for the reporting tests."""
    mock_client = MagicMock()
    
    # Mock the response for getting recent symbols
    mock_client.table.return_value.select.return_value.gte.return_value.execute.return_value = MagicMock(
        data=[{'symbol': 'BTCUSDT'}, {'symbol': 'ETHUSDT'}]
    )
    
    # Mock the responses for getting current and old prices
    # This setup can be customized in each test
    mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{'price': 110.0}] # Default mock for current price
    )
    mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{'price': 100.0}] # Default mock for old price
    )
    return mock_client

@pytest.fixture
def reporting(mock_supabase_client):
    """Fixture to create a Reporting instance with a mocked Supabase client."""
    with patch('app.reporting.create_client', return_value=mock_supabase_client):
        reporter = Reporting()
        reporter.alerter = AsyncMock()
        return reporter

@pytest.mark.asyncio
async def test_generate_report_sends_email(reporting, mock_supabase_client):
    """Test that a report is generated and sent when there are gainers."""
    with patch('asyncio.to_thread', new_callable=AsyncMock):
        await reporting.generate_report("1m", timedelta(minutes=1))
        
        # Check that the alerter's send_gainer_report method was called
        reporting.alerter.send_gainer_report.assert_called_once()

@pytest.mark.asyncio
async def test_generate_report_no_gainers(reporting, mock_supabase_client):
    """Test that no report is sent when there are no price increases."""
    # Mock the price responses to show no change
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{'price': 100.0}]
    )
    
    with patch('asyncio.to_thread', new_callable=AsyncMock):
        await reporting.generate_report("1m", timedelta(minutes=1))
        
        # Check that the alerter's send_gainer_report method was not called
        reporting.alerter.send_gainer_report.assert_not_called()

@pytest.mark.asyncio
async def test_generate_report_handles_no_data(reporting, mock_supabase_client):
    """Test that the report generation handles cases where there is no historical data."""
    # Mock the response to return no recent symbols
    mock_supabase_client.table.return_value.select.return_value.gte.return_value.execute.return_value = MagicMock(data=[])
    
    with patch('asyncio.to_thread', new_callable=AsyncMock):
        await reporting.generate_report("1m", timedelta(minutes=1))
        
        reporting.alerter.send_gainer_report.assert_not_called()