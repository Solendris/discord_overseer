from src.bot import ReminderBot
from unittest.mock import MagicMock
import pytest

@pytest.fixture
def mocked_bot(mocker):
    bot = ReminderBot(config=MagicMock(), notifier=MagicMock(), scraper=MagicMock())
    
    mocker.patch.object(bot, '_check_all_players', return_value={"Player1": {}})
    mocker.patch.object(bot, '_analyze_and_notify')
    
    return bot


def test_run_clears_scraper_cache_twice(mocked_bot):
    mocked_bot.run()
    assert mocked_bot.scraper.clear_cache.call_count == 2

def test_run_checks_all_players(mocked_bot):
    mocked_bot.run()
    mocked_bot._check_all_players.assert_called_once()

def test_run_analyzes_and_notifies(mocked_bot):
    mocked_bot.run()
    mocked_bot._analyze_and_notify.assert_called_once_with({"Player1": {}})

def test_check_all_players_loops_over_config_players(mocker):
    bot = ReminderBot(config=MagicMock(), notifier=MagicMock(), scraper=MagicMock())
    bot.config.active_players = ["Tester", "Pies"]

    mock_status = {'should_check': True, 'gm_post_date': None, 'last_seen': None}
    mocker.patch.object(bot, '_check_player_status', return_value=mock_status)
    wyniki = bot._check_all_players()

    assert bot._check_player_status.call_count == 2
    assert "Tester" in wyniki
    assert "Pies" in wyniki
    assert wyniki["Tester"] == mock_status
