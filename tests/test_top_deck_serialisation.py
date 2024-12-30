import pytest
import json
from Client.TopDeckClient import *

###########################################################################################################################################
# SerializationTests
@pytest.mark.parametrize("game_type, expected", [
    (TopDeckConstants.Game.MagicTheGathering, "Magic: The Gathering")
])
def test_should_serialize_game_correctly(game_type, expected):
    json_str  = TopdeckTournamentRequest(game= game_type
                                           ).to_json()
    json_object = json.loads(json_str)
    game = json_object.get('game')
    assert game == expected


@pytest.mark.parametrize("format_type, expected", [
    (TopDeckConstants.Format.EDH, "EDH"),
    (TopDeckConstants.Format.PauperEDH, "Pauper EDH"),
    (TopDeckConstants.Format.Standard, "Standard"),
    (TopDeckConstants.Format.Pioneer, "Pioneer"),
    (TopDeckConstants.Format.Modern, "Modern"),
    (TopDeckConstants.Format.Legacy, "Legacy"),
    (TopDeckConstants.Format.Pauper, "Pauper"),
    (TopDeckConstants.Format.Vintage, "Vintage"),
    (TopDeckConstants.Format.Premodern, "Premodern"),
    (TopDeckConstants.Format.Limited, "Limited"),
    (TopDeckConstants.Format.Timeless, "Timeless"),
    (TopDeckConstants.Format.Historic, "Historic"),
    (TopDeckConstants.Format.Explorer, "Explorer"),
    (TopDeckConstants.Format.Oathbreaker, "Oathbreaker")
])
def test_should_serialize_format_correctly(format_type, expected):
    json_str = TopdeckTournamentRequest(format= format_type.value
                                           ).to_json()
    json_object = json.loads(json_str)
    format_value = json_object.get('format')
    assert format_value == expected

@pytest.mark.parametrize("column_type, expected", [
    (TopDeckConstants.PlayerColumn.Name, "name"),
    (TopDeckConstants.PlayerColumn.Decklist, "decklist"),
    (TopDeckConstants.PlayerColumn.DeckSnapshot, "deckSnapshot"),
    (TopDeckConstants.PlayerColumn.Commanders, "commanders"),
    (TopDeckConstants.PlayerColumn.Wins, "wins"),
    (TopDeckConstants.PlayerColumn.WinsSwiss, "winsSwiss"),
    (TopDeckConstants.PlayerColumn.WinsBracket, "winsBracket"),
    (TopDeckConstants.PlayerColumn.WinRate, "winRate"),
    (TopDeckConstants.PlayerColumn.WinRateSwiss, "winRateSwiss"),
    (TopDeckConstants.PlayerColumn.WinRateBracket, "winRateBracket"),
    (TopDeckConstants.PlayerColumn.Draws, "draws"),
    (TopDeckConstants.PlayerColumn.Losses, "losses"),
    (TopDeckConstants.PlayerColumn.LossesSwiss, "lossesSwiss"),
    (TopDeckConstants.PlayerColumn.LossesBracket, "lossesBracket"),
    (TopDeckConstants.PlayerColumn.ID, "id")
])
def test_should_serialize_player_column_correctly(column_type, expected):
    json_str = TopdeckTournamentRequest(columns=[column_type.value]).to_json()
    json_object = json.loads(json_str)
    column = json_object.get('columns')[0]
    assert column == expected

def test_should_serialize_sample_tournament_request_correctly():
    request = TopdeckTournamentRequest(
        game=TopDeckConstants.Game.MagicTheGathering,
        start=10000,
        end=20000,
        columns=[TopDeckConstants.PlayerColumn.Name.value, TopDeckConstants.PlayerColumn.Wins.value]
    )
    json_object = json.loads(request.to_json())
    assert json_object["game"] == request.game
    assert json_object["start"] == request.start
    assert json_object["end"] == request.end
    assert json_object["columns"] == [column for column in request.columns]
