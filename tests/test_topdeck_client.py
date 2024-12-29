import pytest
from datetime import datetime, timezone
import json
from Client.TopDeckClient import *
###########################################################################################################################################
# RoundLoaderTests
@pytest.fixture(scope="module")
def rounds():
    client = TopdeckClient()
    rounds = client.get_rounds("iCMd298218qbEqeGt5d7")
    return rounds

def test_rounds_should_have_names(rounds):
    for round in rounds:
        assert round.name is not None and round.name != ""

def test_rounds_should_have_tables(rounds):
    for round in rounds:
        assert round.tables is not None

def test_round_tables_should_have_numbers(rounds):
    for round in rounds:
        for table in round.tables:
            assert table.name is not None and table.name != ""

def test_round_tables_should_have_players(rounds):
    for round in rounds:
        for table in round.tables:
            assert table.players is not None

def test_round_tables_should_have_winners(rounds):
    for round in rounds:
        for table in round.tables:
            assert table.winner is not None and table.winner != ""

def test_round_tables_should_have_winners_matching_one_of_the_players_or_draw(rounds):
    for round in rounds:
        for table in round.tables:
            assert table.winner in [player.name for player in table.players] + [Misc.DRAW_TEXT]

def test_round_tables_should_have_player_names(rounds):
    for round in rounds:
        for table in round.tables:
            for player in table.players:
                assert player.name is not None and player.name != ""

###########################################################################################################################################
# StandingLoaderTests
@pytest.fixture(scope="module")
def standings():
    client = TopdeckClient()
    standings = client.get_standings("SrJAEZ8vbglVge29fG7l")
    return standings 

def test_standings_should_have_player_name(standings):
    for standing in standings:
        assert standing.name is not None and standing.name != ""

def test_standings_should_have_some_decklists(standings):
    decklists = [s for s in standings if s.decklist]
    assert decklists is not None and len(decklists) > 0

def test_standings_should_have_only_valid_urls_for_decklists():
    client = TopdeckClient()
    standings = client.get_standings("SszR1p5QxRzPHPkLayP5")
    for standing in standings:
        if standing.decklist:
            assert standing.decklist.startswith("http://") or standing.decklist.startswith("https://")

def test_standings_should_have_points(standings):
    for standing in standings:
        assert standing.points is not None
    assert any(s.points > 0 for s in standings)

def test_standings_should_have_standing(standings):
    for standing in standings:
        assert standing.standing is not None
    assert any(s.standing > 0 for s in standings)

def test_standings_should_have_opponent_win_rate(standings):
    for standing in standings:
        assert standing.opponent_win_rate is not None
    assert any(s.opponent_win_rate > 0 for s in standings)

def test_standings_should_have_opponent_game_win_rate(standings):
    for standing in standings:
        assert standing.opponent_game_win_rate is not None
    assert any(s.opponent_game_win_rate > 0 for s in standings)

def test_standings_should_have_game_win_rate(standings):
    for standing in standings:
        assert standing.game_win_rate is not None
    assert any(s.game_win_rate > 0 for s in standings)

def test_standings_should_have_valid_data(standings):
    expected_standing = {
        "standing": 1,
        "points": 11,
        "game_win_rate": 0.7407407407407407,
        "opponent_game_win_rate": 0.68728956228956228,
        "opponent_win_rate": 0.6333333333333333,
        "name": "Kerry leamon",
        "decklist": None
    }
    # Vérification de l'équivalence des données pour le premier standing
    assert standings[0] == expected_standing
###########################################################################################################################################
# TournamentInfoLoaderTests
@pytest.fixture(scope="module")
def tournament_info():
    client = TopdeckClient()
    return client.get_tournament_info("SrJAEZ8vbglVge29fG7l")

def test_tournament_info_should_have_name(tournament_info):
    assert tournament_info.name is not None and tournament_info.name != ""

def test_tournament_info_should_have_game(tournament_info):
    assert tournament_info.game is not None

def test_tournament_info_should_have_format(tournament_info):
    assert tournament_info.format is not None

def test_tournament_info_should_have_start_date(tournament_info):
    assert tournament_info.start_date is not None

def test_tournament_info_should_have_valid_data(tournament_info):
    expected_info = {
        'name': 'CCS Summer Showdown Modern 2k',
        'start_date': 1717934400,
        'game': TopDeckConstants.Game.MagicTheGathering,
        'format': TopDeckConstants.Format
    }
    assert tournament_info.name == expected_info['name']
    assert tournament_info.start_date == expected_info['start_date']
    assert tournament_info.game == expected_info['game']
    assert tournament_info.format == expected_info['format']

###########################################################################################################################################
# TournamentListLoaderTests
@pytest.fixture(scope="module")
def tournaments():
    client = TopdeckClient()
    request = {
        'game': 'Magic: The Gathering',
        'format': 'Legacy',
        'start': int(datetime(2024, 3, 30, 0, 0, 0, tzinfo=timezone.utc).timestamp()),
        'end': int(datetime(2024, 3, 31, 0, 0, 0, tzinfo=timezone.utc).timestamp()),
        'columns': ['name', 'id', 'decklist', 'wins', 'losses', 'draws', 'deckSnapshot']
    }
    return client.get_tournament_list(request)


def test_should_load_tournaments(tournaments):
    assert tournaments is not None and len(tournaments) > 0


def test_should_load_expected_number_of_tournaments(tournaments):
    assert len(tournaments) == 2


def test_should_load_tournament_ids(tournaments):
    for tournament in tournaments:
        assert tournament.id is not None and tournament.id != ""


def test_should_load_tournament_names(tournaments):
    for tournament in tournaments:
        assert tournament.name is not None and tournament.name != ""


def test_should_load_tournament_dates(tournaments):
    for tournament in tournaments:
        assert tournament.start_date > 0


def test_should_load_tournament_standings(tournaments):
    for tournament in tournaments:
        assert tournament.standings is not None


def test_should_load_tournament_standings_wins(tournaments):
    for tournament in tournaments:
        assert any(standing.wins > 0 for standing in tournament.standings)


def test_should_load_tournament_standings_losses(tournaments):
    for tournament in tournaments:
        assert any(standing.losses > 0 for standing in tournament.standings)


def test_should_load_tournament_standings_draws(tournaments):
    for tournament in tournaments:
        assert any(standing.draws > 0 for standing in tournament.standings)


def test_should_load_tournament_deck_snapshot(tournaments):
    for tournament in tournaments:
        assert any(standing.deck_snapshot and standing.deck_snapshot.mainboard and len(standing.deck_snapshot.mainboard) > 0
                   for standing in tournament.standings)


def test_should_load_tournament_urls(tournaments):
    for tournament in tournaments:
        assert tournament.uri is not None
        assert "topdeck.gg" in str(tournament.uri)


def test_should_load_expected_data(tournaments):
    expected_tournament = {
        'id': 'HxSr6p4bZXYjUMTibl8i',
        'name': 'Spellbound Games Legacy Dual Land Tournament',
        'start_date': 1711803600,
        'uri': 'https://topdeck.gg/event/HxSr6p4bZXYjUMTibl8i'
    }
    first_tournament = tournaments[0]
    assert first_tournament.id == expected_tournament['id']
    assert first_tournament.name == expected_tournament['name']
    assert first_tournament.start_date == expected_tournament['start_date']
    assert str(first_tournament.uri) == expected_tournament['uri']
    
    # Vérification des standings
    assert len(first_tournament.standings) == 36
    first_standing = first_tournament.standings[0]
    assert first_standing.wins == 7
    assert first_standing.losses == 1
    assert first_standing.draws == 1
    assert first_standing.name == "Ryan Waligóra"
    
    # Vérification du deck snapshot pour le deuxième standing
    second_standing = first_tournament.standings[1]
    assert second_standing.deck_snapshot.mainboard == {
        "Island": 1, "Plains": 1, "Forest": 1, "Uro, Titan of Nature's Wrath": 3, "Brainstorm": 4, "Daze": 1, 
        "Swords to Plowshares": 4, "Life from the Loam": 1, "Savannah": 1, "Tundra": 3, "Tropical Island": 2, 
        "Flooded Strand": 4, "Force of Will": 4, "Wasteland": 2, "Misty Rainforest": 4, "Phyrexian Dreadnought": 4,
        "Batterskull": 1, "Stoneforge Mystic": 4, "Stifle": 3, "Ponder": 4, "Prismatic Ending": 1, "Dress Down": 3,
        "Kaldra Compleat": 1, "Lórien Revealed": 1, "Hedge Maze": 1, "Cryptic Coat": 2
    }
    assert second_standing.deck_snapshot.sideboard == {
        "Deafening Silence": 1, "Blue Elemental Blast": 1, "Carpet of Flowers": 1, "Containment Priest": 1,
        "Veil of Summer": 1, "Hydroblast": 1, "Surgical Extraction": 2, "Lavinia, Azorius Renegade": 1,
        "Flusterstorm": 1, "Force of Negation": 1, "Torpor Orb": 1, "Powder Keg": 1, "Hullbreacher": 1,
        "Boseiju, Who Endures": 1
    }


def test_empty_decklists_should_be_null(tournaments):
    for standing in (s for t in tournaments for s in t.standings if s.deck_snapshot):
        assert standing.deck_snapshot.mainboard is not None and len(standing.deck_snapshot.mainboard) > 0




###########################################################################################################################################
# TournamentLoaderTests
@pytest.fixture(scope="module")
def tournament():
    client = TopdeckClient()
    return client.get_tournament("SrJAEZ8vbglVge29fG7l")

def test_tournament_info_should_have_data(tournament):
    assert tournament.data is not None

def test_tournament_info_should_have_rounds(tournament):
    assert tournament.rounds is not None

def test_tournament_info_should_have_standings(tournament):
    assert tournament.standings is not None

def test_tournament_info_should_have_valid_data(tournament):
    expected_info = {
        'name': 'CCS Summer Showdown Modern 2k',
        'start_date': 1717934400,
        'game': TopDeckConstants.Game.MagicTheGathering,
        'format': TopDeckConstants.Format.Modern
    }
    assert tournament.data.name == expected_info['name']
    assert tournament.data.start_date == expected_info['start_date']
    assert tournament.data.game == expected_info['game']
    assert tournament.data.format == expected_info['format']

###########################################################################################################################################
# SerializationTests
def test_should_serialize_game_correctly( ):
    json_object = json.loads(TopdeckTournamentRequest(game=TopDeckConstants.Game.MagicTheGathering).to_json())
    game = json_object.get("game")
    assert game == TopDeckConstants.Game.MagicTheGathering

def test_should_serialize_format_correctly():
    json_object = json.loads(TopdeckTournamentRequest(format=TopDeckConstants.Format).to_json())
    format = json_object.get("format")
    assert format == TopDeckConstants.Format

def test_should_serialize_player_column_correctly():
    json_object = json.loads(TopdeckTournamentRequest(columns=[TopDeckConstants.PlayerColumn]).to_json())
    column = json_object.get("columns")[0]
    assert column == TopDeckConstants.PlayerColumn

def test_should_serialize_sample_tournament_request_correctly():
    request = TopdeckTournamentRequest(
        game=TopDeckConstants.Game.MagicTheGathering,
        start=10000,
        end=20000,
        columns=[TopDeckConstants.PlayerColumn.Name, TopDeckConstants.PlayerColumn.Wins]
    )
    json_object = json.loads(request.to_json())
    assert json_object["game"] == request.game
    assert json_object["start"] == request.start
    assert json_object["end"] == request.end
    assert json_object["columns"] == [column.value for column in request.columns]