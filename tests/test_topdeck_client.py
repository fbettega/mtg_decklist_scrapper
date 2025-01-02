import pytest
from datetime import datetime, timezone
import json
from Client.TopDeckClient import *
from models.Topdeck_model import *
from comon_tools.tools import *

###########################################################################################################################################


###########################################################################################################################################
# RoundLoaderTests
@pytest.fixture(scope="module")
def rounds():
    client = TopdeckClient()
    rounds = client.get_rounds("iCMd298218qbEqeGt5d7")
    # rounds = client.get_rounds("z97Wwe0sadHGT2ymc5Ss")
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
            assert table.winner in [player.name for player in table.players] + [TopDeckConstants.Misc.DRAW_TEXT]

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
    # standings = client.get_standings("3rcztzBRihhE6z0io74b")
    return standings 

def test_standings_should_have_player_name(standings):
    for standing in standings:
        assert standing.name is not None and standing.name != ""

def test_standings_should_have_some_decklists(standings):
    decklists = [s for s in standings if s.decklist]
    assert decklists is not None and len(decklists) > 0


def test_standings_should_have_only_valid_urls_for_decklists():
    client = TopdeckClient()
    standings_test_url = client.get_standings("SszR1p5QxRzPHPkLayP5")
    # standings_test_url = client.get_standings("z97Wwe0sadHGT2ymc5Ss")
    for standing in standings_test_url:
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
    expected_standing = TopdeckStanding(
        standing = 1,
        points = 11,
        game_win_rate = 0.7407407407407407,
        opponent_game_win_rate = 0.68728956228956228,
        opponent_win_rate = 0.6333333333333333,
        name = "Kerry leamon",
        decklist = None)
    # Vérification de l'équivalence des données pour le premier standing
    assert standings[0] == expected_standing


###########################################################################################################################################
# TournamentInfoLoaderTests
@pytest.fixture(scope="module")
def tournament_info():
    client = TopdeckClient()
    tournament_info = client.get_tournament_info("SrJAEZ8vbglVge29fG7l")
    return tournament_info

def test_tournament_info_should_have_name(tournament_info):
    assert tournament_info.name is not None and tournament_info.name != ""

def test_tournament_info_should_have_game(tournament_info):
    assert tournament_info.game is not None

def test_tournament_info_should_have_format(tournament_info):
    assert tournament_info.format is not None

def test_tournament_info_should_have_start_date(tournament_info):
    assert tournament_info.start_date is not None

def test_tournament_info_should_have_valid_data(tournament_info):
    expected_info = TopdeckTournamentInfo(
        name= 'CCS Summer Showdown Modern 2k',
        start_date= 1717934400,
        game= TopDeckConstants.Game.MagicTheGathering,
        format= TopDeckConstants.Format.Modern.value
        )
    assert tournament_info.name == expected_info.name
    assert tournament_info.start_date == expected_info.start_date
    assert tournament_info.game == expected_info.game
    assert tournament_info.format == expected_info.format


###########################################################################################################################################
# TournamentListLoaderTests
@pytest.fixture(scope="module")
def tournamentsLoader():
    client = TopdeckClient()
    request = TopdeckTournamentRequest(
    game='Magic: The Gathering',
    format='Legacy',
    start=int(datetime(2024, 3, 30, 0, 0, 0, tzinfo=timezone.utc).timestamp()),
    end=int(datetime(2024, 3, 31, 0, 0, 0, tzinfo=timezone.utc).timestamp()),
    columns=['name', 'id', 'decklist', 'wins', 'losses', 'draws', 'deckSnapshot']
    )
    tournamentsLoader = client.get_tournament_list(request)
    return tournamentsLoader

# client = TopdeckClient()
# request = TopdeckTournamentRequest(
# game='Magic: The Gathering',
# format='Legacy',
# start=int(datetime(2024, 12, 6, 0, 0, 0, tzinfo=timezone.utc).timestamp()),
# end=int(datetime(2024, 12, 8, 0, 0, 0, tzinfo=timezone.utc).timestamp()),
# columns=['name', 'id', 'decklist', 'wins', 'losses', 'draws', 'deckSnapshot']
# )
# tournamentsLoader = client.get_tournament_list(request)


def test_should_load_tournaments(tournamentsLoader):
    assert tournamentsLoader is not None and len(tournamentsLoader) > 0


def test_should_load_expected_number_of_tournaments(tournamentsLoader):
    assert len(tournamentsLoader) == 2


def test_should_load_tournament_ids(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert tournament.id is not None and tournament.id != ""


def test_should_load_tournament_names(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert tournament.name is not None and tournament.name != ""


def test_should_load_tournament_dates(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert tournament.start_date > 0


def test_should_load_tournament_standings(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert tournament.standings is not None


def test_should_load_tournament_standings_wins(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert any(standing.wins > 0 for standing in tournament.standings)


def test_should_load_tournament_standings_losses(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert any(standing.losses > 0 for standing in tournament.standings)


def test_should_load_tournament_standings_draws(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert any(standing.draws > 0 for standing in tournament.standings)


def test_should_load_tournament_deck_snapshot(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert any(standing.deckSnapshot and standing.deckSnapshot.mainboard and len(standing.deckSnapshot.mainboard) > 0
                   for standing in tournament.standings)


def test_should_load_tournament_urls(tournamentsLoader):
    for tournament in tournamentsLoader:
        assert tournament.uri is not None
        assert "topdeck.gg" in str(tournament.uri)


def test_should_load_expected_data(tournamentsLoader):
    expected_tournament = TopdeckListTournament(
    id='HxSr6p4bZXYjUMTibl8i',
    name='Spellbound Games Legacy Dual Land Tournament',
    start_date=1711803600,
    uri='https://topdeck.gg/event/HxSr6p4bZXYjUMTibl8i'
    )
    first_tournament = tournamentsLoader[0]
    assert first_tournament.id == expected_tournament.id
    assert first_tournament.name == expected_tournament.name
    assert first_tournament.start_date == expected_tournament.start_date
    assert str(first_tournament.uri) == expected_tournament.uri
    
    # Vérification des standings
    assert len(first_tournament.standings) == 36
    first_standing = first_tournament.standings[0]
    assert first_standing.wins == 7
    assert first_standing.losses == 1
    assert first_standing.draws == 1
    assert first_standing.name == "Ryan Waligóra"
    
    # Vérification du deck snapshot pour le deuxième standing
    second_standing = first_tournament.standings[1]
    assert second_standing.deckSnapshot.mainboard == {
        "Island": 1, "Plains": 1, "Forest": 1, "Uro, Titan of Nature's Wrath": 3, "Brainstorm": 4, "Daze": 1, 
        "Swords to Plowshares": 4, "Life from the Loam": 1, "Savannah": 1, "Tundra": 3, "Tropical Island": 2, 
        "Flooded Strand": 4, "Force of Will": 4, "Wasteland": 2, "Misty Rainforest": 4, "Phyrexian Dreadnought": 4,
        "Batterskull": 1, "Stoneforge Mystic": 4, "Stifle": 3, "Ponder": 4, "Prismatic Ending": 1, "Dress Down": 3,
        "Kaldra Compleat": 1, "Lórien Revealed": 1, "Hedge Maze": 1, "Cryptic Coat": 2
    }
    assert second_standing.deckSnapshot.sideboard == {
        "Deafening Silence": 1, "Blue Elemental Blast": 1, "Carpet of Flowers": 1, "Containment Priest": 1,
        "Veil of Summer": 1, "Hydroblast": 1, "Surgical Extraction": 2, "Lavinia, Azorius Renegade": 1,
        "Flusterstorm": 1, "Force of Negation": 1, "Torpor Orb": 1, "Powder Keg": 1, "Hullbreacher": 1,
        "Boseiju, Who Endures": 1
    }

def test_empty_decklists_should_be_null(tournamentsLoader):
    for standing in (s for t in tournamentsLoader for s in t.standings if s.deckSnapshot):
        assert standing.deckSnapshot.mainboard is not None and len(standing.deckSnapshot.mainboard) > 0

###########################################################################################################################################
# TournamentLoaderTests
@pytest.fixture(scope="module")
def TournamentLoader():
    client = TopdeckClient()
    TournamentLoader = client.get_tournament("SrJAEZ8vbglVge29fG7l")
    return TournamentLoader

def test_tournament_info_should_have_data(TournamentLoader):
    assert TournamentLoader.data is not None

def test_tournament_info_should_have_rounds(TournamentLoader):
    assert TournamentLoader.rounds is not None

def test_tournament_info_should_have_standings(TournamentLoader):
    assert TournamentLoader.standings is not None

def test_tournament_info_should_have_valid_data(TournamentLoader):
    expected_info = TopdeckTournamentInfo(
        name= 'CCS Summer Showdown Modern 2k',
        start_date= 1717934400,
        game= TopDeckConstants.Game.MagicTheGathering,
        format= TopDeckConstants.Format.Modern.value
    )
    assert TournamentLoader.data.name == expected_info.name
    assert TournamentLoader.data.start_date == expected_info.start_date
    assert TournamentLoader.data.game == expected_info.game
    assert TournamentLoader.data.format == expected_info.format

