import pytest
# from  MTGmelee.MtgMeleeClient import *
# import importlib
from datetime import datetime
# import Client.MtgMeleeClient
# # Recharger le module
# importlib.reload(Client.MtgMeleeClient)
# pytest .\tests\MtgMelee.py 
# pytest .\tests\
# Réimporter tous les objets exportés par le module
from Client.ManatraderClient import *


@pytest.fixture
def mana_trader_get_tournament_details_data():
    tournament = Tournament(uri="https://www.manatraders.com/tournaments/30/", date=datetime(2022, 8, 31))
    mana_trader_get_tournament_details_data = TournamentList().get_tournament_details(tournament)
    return mana_trader_get_tournament_details_data

#######################################################################################################
# StandingsLoaderTests
@pytest.fixture
def standings_data(mana_trader_get_tournament_details_data):
    standings_data = mana_trader_get_tournament_details_data.standings
    return standings_data


# Test functions
def test_standings_count_is_correct(standings_data):
    assert len(standings_data) == 195

def test_standings_have_players(standings_data):
    for standing in standings_data:
        assert standing.player is not None and standing.player.strip() != ''

def test_standings_have_rank(standings_data):
    for standing in standings_data:
        assert standing.rank is not None and standing.rank > 0

def test_standings_have_points(standings_data):
    for standing in standings_data[:32]:
        assert standing.points is not None and standing.points > 0

def test_standings_have_omwp(standings_data):
    for standing in standings_data[:32]:
        assert standing.omwp is not None and standing.omwp > 0

def test_standings_have_gwp(standings_data):
    for standing in standings_data[:32]:
        assert standing.gwp is not None and standing.gwp > 0

def test_standings_have_ogwp(standings_data):
    for standing in standings_data[:32]:
        assert standing.ogwp is not None and standing.ogwp > 0

def test_standing_data_is_correct(standings_data):
    test_standing = standings_data[0]
    expected_standing = Standing(
        rank=1, 
        player="Fink64", 
        points=21, 
        wins=7, 
        losses=1, 
        draws=0, 
        omwp=0.659, 
        gwp=0.75, 
        ogwp=0.584
    )
    assert test_standing == expected_standing
#######################################################################################################
# BracketWithExtraMatchesLoaderTests
# Données de test
@pytest.fixture
def rounds_ExtraMatches_data():
    rounds_ExtraMatches_data = [
    round_ for round_ in  mana_trader_get_tournament_details_data.rounds
    if not round_.round_name.startswith("Round")
    ]
    return rounds_ExtraMatches_data

# Tests
def test_bracket_item_count_is_correct(rounds_ExtraMatches_data):
    assert len(next(r for r in rounds_ExtraMatches_data if r.round_name == "Quarterfinals").matches) == 4
    assert len(next(r for r in rounds_ExtraMatches_data if r.round_name == "Semifinals").matches) == 2
    assert len(next(r for r in rounds_ExtraMatches_data if r.round_name == "Finals").matches) == 1

def test_bracket_items_have_winning_player(rounds_ExtraMatches_data):
    for round_data in rounds_ExtraMatches_data:
        for match in round_data.matches:
            assert match.player1 is not None
            assert match.player1 != ""

def test_bracket_items_have_losing_player(rounds_ExtraMatches_data):
    for round_data in rounds_ExtraMatches_data:
        for match in round_data.matches:
            assert match.player2 is not None
            assert match.player2 != ""

def test_bracket_items_have_result(rounds_ExtraMatches_data):
    for round_data in rounds_ExtraMatches_data:
        for match in round_data.matches:
            assert match.result is not None
            assert match.result != ""

def test_bracket_rounds_should_be_in_correct_order(rounds_ExtraMatches_data):
    expected_round_names = [
    "Quarterfinals",
    "Loser Semifinals",
    "Semifinals",
    "Match for 7th and 8th places",
    "Match for 5th and 6th places",
    "Match for 3rd and 4th places",
    "Finals"
    ]
    actual_round_names = [round_data.round_name for round_data in rounds_ExtraMatches_data]
    assert actual_round_names == expected_round_names

def test_should_contain_extra_brackets(rounds_ExtraMatches_data):
    assert len(rounds_ExtraMatches_data) == 7  

def test_bracket_items_data_is_correct(rounds_ExtraMatches_data):
    expected = [
        Round(
            round_name="Quarterfinals",
            matches=[
                RoundItem(player1="zuri1988", player2="Fink64", result="2-1-0"),
                RoundItem(player1="kvza", player2="Harry13", result="2-0-0"),
                RoundItem(player1="ModiSapiras", player2="Daking3603", result="2-0-0"),
                RoundItem(player1="Cinciu", player2="ScouterTF2", result="2-0-0"),
            ],
        ),
        Round(
            round_name="Loser Semifinals",
            matches=[
                RoundItem(player1="Harry13", player2="Fink64", result="2-0-0"),
                RoundItem(player1="Daking3603", player2="ScouterTF2", result="2-0-0"),
            ],
        ),
        Round(
            round_name="Semifinals",
            matches=[
                RoundItem(player1="kvza", player2="zuri1988", result="2-1-0"),
                RoundItem(player1="ModiSapiras", player2="Cinciu", result="2-0-0"),
            ],
        ),
        Round(
            round_name="Match for 7th and 8th places",
            matches=[
                RoundItem(player1="ScouterTF2", player2="Fink64", result="2-0-0"),
            ],
        ),
        Round(
            round_name="Match for 5th and 6th places",
            matches=[
                RoundItem(player1="Daking3603", player2="Harry13", result="2-0-0"),
            ],
        ),
        Round(
            round_name="Match for 3rd and 4th places",
            matches=[
                RoundItem(player1="Cinciu", player2="zuri1988", result="2-0-0"),
            ],
        ),
        Round(
            round_name="Finals",
            matches=[
                RoundItem(player1="ModiSapiras", player2="kvza", result="2-0-0"),
            ],
        ),
        ]

    for round_data, expected_round in zip(rounds_ExtraMatches_data, expected):
        assert round_data.round_name == expected_round.round_name
        for match, expected_match in zip(round_data.matches, expected_round.matches):
            assert match.player1 == expected_match.player1
            assert match.player2 == expected_match.player2
            assert match.result == expected_match.result


#######################################################################################################
# BracketWithoutExtraMatchesLoaderTests
# Fixture pour fournir les données de test
@pytest.fixture
def test_bracketwithoutextramatches_data():
    tournament = Tournament(uri="https://www.manatraders.com/tournaments/15/", date=datetime(2021, 4, 30))
    rounds_total = TournamentList().get_tournament_details(tournament).rounds
    test_bracketwithoutextramatches_data = [
        round_ for round_ in  rounds_total
        if not round_.round_name.startswith("Round")
        ]

    return test_bracketwithoutextramatches_data



# Tests
def test_bracket_item_count_is_correct(test_bracketwithoutextramatches_data):
    assert len(test_bracketwithoutextramatches_data[0].matches) == 4  # Quarterfinals
    assert len(test_bracketwithoutextramatches_data[1].matches) == 2  # Semifinals
    assert len(test_bracketwithoutextramatches_data[2].matches) == 1  # Finals

def test_bracket_items_have_winning_player(test_bracketwithoutextramatches_data):
    for round_data in test_bracketwithoutextramatches_data:
        for match in round_data.matches:
            assert match.player1 is not None
            assert match.player1 != ""

def test_bracket_items_have_losing_player(test_bracketwithoutextramatches_data):
    for round_data in test_bracketwithoutextramatches_data:
        for match in round_data.matches:
            assert match.player2 is not None
            assert match.player2 != ""

def test_bracket_items_have_result(test_bracketwithoutextramatches_data):
    for round_data in test_bracketwithoutextramatches_data:
        for match in round_data.matches:
            assert match.result is not None
            assert match.result != ""

def test_bracket_rounds_should_be_in_correct_order(test_bracketwithoutextramatches_data):
    expected_round_names = ["Quarterfinals", "Semifinals", "Finals"]
    actual_round_names = [round_data.round_name for round_data in test_bracketwithoutextramatches_data]
    assert actual_round_names == expected_round_names

def test_should_not_contain_extra_brackets(test_bracketwithoutextramatches_data):
    assert len(test_bracketwithoutextramatches_data) == 3  # Expected 3 rounds: Quarterfinals, Semifinals, Finals

def test_bracket_items_data_is_correct(test_bracketwithoutextramatches_data):
    expected = [
        Round("Quarterfinals", [
            RoundItem("sandoiche", "MentalMisstep", "2-0-0"),
            RoundItem("stefanogs", "Paradise_lost", "2-0-0"),
            RoundItem("Darthkid", "Promidnightz", "2-0-0"),
            RoundItem("lynnchalice", "joaofelipen72", "2-0-0"),
        ]),
        Round("Semifinals", [
            RoundItem("sandoiche", "stefanogs", "2-1-0"),
            RoundItem("lynnchalice", "Darthkid", "2-0-0"),
        ]),
        Round("Finals", [
            RoundItem("sandoiche", "lynnchalice", "2-0-0"),
        ]),
    ]
    for round_data, expected_round in zip(test_bracketwithoutextramatches_data, expected):
        assert round_data.round_name == expected_round.round_name
        for match, expected_match in zip(round_data.matches, expected_round.matches):
            assert match.player1 == expected_match.player1
            assert match.player2 == expected_match.player2
            assert match.result == expected_match.result


#######################################################################################################
# DeckLoaderTests
# Fixture pour fournir les données de test
@pytest.fixture
def test_decks_data(mana_trader_get_tournament_details_data):
    # Mock de la source des données
    test_decks_data = mana_trader_get_tournament_details_data.decks
    return test_decks_data

# Tests
def test_deck_count_is_correct(test_decks_data):
    assert len(test_decks_data) == 194  # Attendu : 194 decks

def test_decks_dont_have_date(test_decks_data):
    for deck in test_decks_data:
        assert deck.date is None

def test_decks_have_players(test_decks_data):
    for deck in test_decks_data:
        assert deck.player is not None
        assert deck.player != ""

def test_decks_have_mainboards(test_decks_data):
    for deck in test_decks_data:
        assert len(deck.mainboard) > 0

def test_decks_have_sideboards(test_decks_data):
    for deck in test_decks_data:
        assert len(deck.sideboard) > 0

def test_decks_have_valid_mainboards(test_decks_data):
    for deck in test_decks_data:
        assert sum(item.count for item in deck.mainboard) >= 60

def test_decks_have_valid_sideboards(test_decks_data):
    for deck in test_decks_data:
        assert sum(item.count for item in deck.sideboard) <= 15

def test_deck_data_is_correct(test_decks_data):
    test_deck = test_decks_data[7]  # L'exemple de test
    assert test_deck.player == "Fink64"
    assert test_deck.anchor_uri == "https://www.manatraders.com/webshop/personal/874208"
    assert test_deck.date is None
    assert test_deck.result == "8th Place"
    assert len(test_deck.mainboard) == 22
    assert len(test_deck.sideboard) == 6
    assert any(item.card_name == "Mausoleum Wanderer" and item.count == 4 for item in test_deck.mainboard)

def test_should_apply_top8_ordering_to_decks(test_decks_data):
    top8 = ["ModiSapiras", "kvza", "Cinciu", "zuri1988", "Daking3603", "Harry13", "ScouterTF2", "Fink64"]
    actual_top8 = [deck.player for deck in test_decks_data[:8]]
    assert actual_top8 == top8

# ici 
#######################################################################################################
# RoundsLoaderTests
@pytest.fixture
def test_RoundsLoader_data(mana_trader_get_tournament_details_data):
    test_RoundsLoader_data = mana_trader_get_tournament_details_data.rounds
    return test_RoundsLoader_data

def test_round_count_is_correct(test_RoundsLoader_data):
    assert len(test_RoundsLoader_data) == 15


def test_rounds_have_number(test_RoundsLoader_data):
    for round in test_RoundsLoader_data:
        assert round['RoundName'] is not None and round['RoundName'] != ''


def test_rounds_have_matches(test_RoundsLoader_data):
    for round in test_RoundsLoader_data:
        assert len(round['Matches']) > 0


# problem
def test_round_data_is_correct(test_RoundsLoader_data):
    test_round = test_RoundsLoader_data[0]
    assert test_round.round_name == "Round 1"
    assert test_round.matches[0] == RoundItem("SuperCow12653", "Demrakh", "2-0-0")


#######################################################################################################
# RoundsWithNoBracketLoaderTests
@pytest.fixture
def test_data_no_bracket():
    tournament_no_bracket = Tournament(uri="https://www.manatraders.com/tournaments/34/", date=datetime(2022, 12, 31))
    test_data_no_bracket = TournamentList().get_tournament_details(tournament_no_bracket).rounds
    return test_data_no_bracket


def test_round_count_is_correct_no_bracket(test_data_no_bracket):
    assert len(test_data_no_bracket) == 9


def test_rounds_have_number_no_bracket(test_data_no_bracket):
    for round in test_data_no_bracket:
        assert round.round_name is not None and round.round_name != ''


def test_rounds_have_matches_no_bracket(test_data_no_bracket):
    for round in test_data_no_bracket:
        assert len(round.matches) > 0


def test_round_data_is_correct_no_bracket(test_data_no_bracket):
    test_round = test_data_no_bracket[0]
    assert test_round.round_name == "Round 1"
    assert test_round.matches[0] == RoundItem("sneakymisato", "Mogged", "0-2-0")



#######################################################################################################
# TournamentLoaderTests
@pytest.fixture
def TournamentLoaderTests_data():
    TournamentLoaderTests_data = TournamentList().DL_tournaments(datetime(2022, 12, 31))
    return TournamentLoaderTests_data


def test_tournament_count_is_correct(tournament_data):
    assert len(tournament_data) > 0


def test_tournament_data_is_correct(tournament_data):
    valid_years = [str(i) for i in range(2020, datetime.now().year + 1)]

    for tournament in tournament_data:
        assert "https://www.manatraders.com/tournaments/" in tournament.Uri
        assert any(league in tournament.Name for league in ["Standard", "Modern", "Pioneer", "Vintage", "Pauper", "Legacy"])
        assert any(month in tournament.Name for month in list(datetime.now().strftime('%B')))
        assert any(year in tournament.Name for year in valid_years)
        assert os.path.basename(tournament.JsonFile).endswith(tournament.Date.strftime("%Y-%m-%d"))
        assert tournament.JsonFile.endswith(".json")