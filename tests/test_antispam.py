import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from handlers.moderation import check_message_violations


def _run(coro):
    return asyncio.run(coro)


@patch("handlers.moderation.delete_message", new_callable=AsyncMock)
@patch("handlers.moderation.send_message", new_callable=AsyncMock)
@patch("handlers.moderation.is_antilink_enabled", new_callable=AsyncMock, return_value=True)
@patch("handlers.moderation.get_filters", new_callable=AsyncMock, return_value=[])
def test_link_is_detected_and_deleted(mock_get_filters, mock_antilink, mock_send, mock_delete):
    fake_message = {
        "chat": {"id": 123},
        "message_id": 1,
        "from": {"id": 1, "first_name": "Test"},
        "text": "Hello visit https://google.com"
    }

    result = _run(check_message_violations(123, fake_message))

    assert result is True
    mock_delete.assert_awaited_once_with(123, 1)
    mock_send.assert_awaited_once()


@patch("handlers.moderation.delete_message", new_callable=AsyncMock)
@patch("handlers.moderation.send_message", new_callable=AsyncMock)
@patch("handlers.moderation.is_antilink_enabled", new_callable=AsyncMock, return_value=True)
@patch("handlers.moderation.get_filters", new_callable=AsyncMock, return_value=[])
def test_clean_message_is_not_flagged(mock_get_filters, mock_antilink, mock_send, mock_delete):
    fake_message = {
        "chat": {"id": 123},
        "message_id": 2,
        "from": {"id": 1, "first_name": "Test"},
        "text": "سلام به همه، امروز حالتون چطوره؟"
    }

    result = _run(check_message_violations(123, fake_message))

    assert result is False
    mock_delete.assert_not_awaited()
    mock_send.assert_not_awaited()


@patch("handlers.moderation.delete_message", new_callable=AsyncMock)
@patch("handlers.moderation.send_message", new_callable=AsyncMock)
@patch("handlers.moderation.is_antilink_enabled", new_callable=AsyncMock, return_value=True)
@patch("handlers.moderation.get_filters", new_callable=AsyncMock, return_value=["badword"])
def test_filtered_word_is_detected_and_deleted(mock_get_filters, mock_antilink, mock_send, mock_delete):
    fake_message = {
        "chat": {"id": 123},
        "message_id": 3,
        "from": {"id": 1, "first_name": "Test"},
        "text": "این یک badword تو جمله است"
    }

    result = _run(check_message_violations(123, fake_message))

    assert result is True
    mock_delete.assert_awaited_once_with(123, 3)
