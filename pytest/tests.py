import pytest
from unittest.mock import patch, AsyncMock

from Bot.http_client import check_imei
from src.config import settings


@pytest.mark.asyncio
async def test_check_imei():
    # Создаем мок для асинхронной сессии
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.json.return_value = {"status": "success"}

    # Мокируем aiohttp.ClientSession
    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await check_imei("123456789012345", 1, settings.SANDBOX_API_KEY)
        assert result == {"status": "success"}