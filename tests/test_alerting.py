import pytest
import respx
import json
from httpx import Response
from unittest.mock import patch, AsyncMock
from app.alerting import Alerter

@pytest.fixture
def email_alerter():
    """Fixture for an Alerter with only email configured."""
    with patch('app.alerting.SUPABASE_URL', 'http://test.supabase.co'), \
         patch('app.alerting.SUPABASE_KEY', 'test-key'), \
         patch('app.alerting.FROM_EMAIL', 'test@example.com'), \
         patch('app.alerting.TO_EMAIL', 'recipient@example.com'), \
         patch('app.alerting.TELEGRAM_BOT_TOKEN', None), \
         patch('app.alerting.TELEGRAM_CHAT_ID', None):
        return Alerter()

@pytest.fixture
def telegram_alerter():
    """Fixture for an Alerter with only Telegram configured."""
    with patch('app.alerting.SUPABASE_URL', None), \
         patch('app.alerting.TELEGRAM_BOT_TOKEN', 'test-token'), \
         patch('app.alerting.TELEGRAM_CHAT_ID', '12345'):
        alerter = Alerter()
        # Mock the bot object
        alerter.bot = AsyncMock()
        return alerter

@pytest.mark.asyncio
@respx.mock
async def test_send_email_alert(email_alerter):
    """Test that an email alert is sent correctly."""
    edge_function_url = email_alerter.edge_function_url
    mock_route = respx.post(edge_function_url).mock(return_value=Response(200))
    
    await email_alerter.send_volatility_alert('BTCUSDT', 5.0, 50000.0)
    
    assert mock_route.called
    request = mock_route.calls.last.request
    payload = json.loads(request.content)
    assert payload['subject'] == "Volatility Alert: BTCUSDT has increased by 5.00%"

@pytest.mark.asyncio
async def test_send_telegram_alert(telegram_alerter):
    """Test that a Telegram alert is sent correctly."""
    await telegram_alerter.send_volatility_alert('ETHUSDT', -4.0, 3000.0)
    
    telegram_alerter.bot.send_message.assert_called_once()
    # You can also inspect the message content
    call_args = telegram_alerter.bot.send_message.call_args
    assert "<b>Volatility Alert</b>" in call_args.kwargs['text']
    assert "ETHUSDT" in call_args.kwargs['text']

@pytest.mark.asyncio
async def test_no_alerts_if_disabled(telegram_alerter):
    """Test that no email is sent if email is disabled."""
    # This alerter has email disabled
    with respx.mock as mock_router:
        await telegram_alerter.send_volatility_alert('BTCUSDT', 5.0, 50000.0)
        # No routes should have been called
        assert len(mock_router.calls) == 0