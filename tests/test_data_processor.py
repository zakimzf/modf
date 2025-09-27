import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.data_processor import DataProcessor

@pytest.fixture
def mock_supabase_client():
    """Fixture to create a mock Supabase client."""
    mock_client = MagicMock()
    # Mock the chainable methods for Supabase queries
    mock_client.table.return_value.insert.return_value.execute = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute = MagicMock(
        return_value=MagicMock(data=[{'price': 100.0}])
    )
    return mock_client

@pytest.fixture
def data_processor(mock_supabase_client):
    """Fixture to create a DataProcessor with a mocked Supabase client."""
    with patch('app.data_processor.create_client', return_value=mock_supabase_client):
        processor = DataProcessor()
        # Replace the alerter with an async mock
        processor.alerter = AsyncMock()
        return processor

@pytest.mark.asyncio
async def test_process_message_inserts_data(data_processor, mock_supabase_client):
    """Test that process_message correctly calls the insert method on the Supabase client."""
    sample_message = [
        {'s': 'BTCUSDT', 'c': '50000.0'},
        {'s': 'ETHUSDT', 'c': '4000.0'}
    ]
    
    # We need to mock asyncio.to_thread to run the synchronous Supabase client calls
    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        await data_processor.process_message(sample_message)
        
        # Check that the insert method was called
        assert mock_to_thread.call_count > 0
        # Further checks could be added here to inspect the data passed to insert

@pytest.mark.asyncio
async def test_check_volatility_sends_alert(data_processor, mock_supabase_client):
    """Test that a volatility alert is sent when the price change exceeds the threshold."""
    symbol = 'BTCUSDT'
    current_price = 105.0  # This is a > 3% change from the mocked old price of 100.0
    
    # Configure the mock to return an old price that triggers the alert
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{'price': 100.0}]
    )

    with patch('asyncio.to_thread', new_callable=AsyncMock):
        await data_processor.check_volatility(symbol, current_price)
        
        # Check that the alerter's send_volatility_alert method was called
        data_processor.alerter.send_volatility_alert.assert_called_once()

@pytest.mark.asyncio
async def test_check_volatility_no_alert(data_processor, mock_supabase_client):
    """Test that no alert is sent when the price change is within the threshold."""
    symbol = 'BTCUSDT'
    current_price = 101.0  # This is a < 3% change from the mocked old price of 100.0
    
    with patch('asyncio.to_thread', new_callable=AsyncMock):
        await data_processor.check_volatility(symbol, current_price)
        
        # Check that the alerter's send_volatility_alert method was not called
        data_processor.alerter.send_volatility_alert.assert_not_called()