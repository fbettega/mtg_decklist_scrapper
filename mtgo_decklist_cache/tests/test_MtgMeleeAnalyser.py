import pytest
from datetime import datetime
import pdb
import importlib
import Client.MtgMeleeClient
from Client.MtgMeleeClient import *

# pytest .\tests\MtgMeleeAnalyser.py    
@pytest.fixture(scope="module")
def client():
    client = MtgMeleeClient()
    return client
@pytest.fixture(scope="module")
def analyzer():
    analyzer = MtgMeleeAnalyzer()
    return analyzer


def test_should_detect_simple_tournaments(client,analyzer):
    tournament = next(
    (t for t in client.get_tournaments(datetime(2023, 10, 14, 0, 0, 0, tzinfo=timezone.utc),datetime(2023, 10, 14, 0, 0, 0, tzinfo=timezone.utc)) if t.id == 17461),
    None
    )
    result = analyzer.get_scraper_tournaments(tournament)[0]

    assert result.name == "MXP Portland Oct 14 Legacy 5k"
    assert result.date == datetime(2023, 10, 14, 19, 0)
    assert result.uri == "https://melee.gg/Tournament/View/17461"

def test_should_add_format_to_json_file_if_missing(client,analyzer):
    tournament = next(
    (t for t in client.get_tournaments(datetime(2023, 10, 15, 0, 0), datetime(2023, 10, 15, 0, 0)) if t.id == 17469),
    None
    )
    result = analyzer.get_scraper_tournaments(tournament)[0]

    assert result.name == "MXP Portland Oct 15 ReCQ"
    assert result.date == datetime(2023, 10, 15, 21, 0)
    assert result.uri == "https://melee.gg/Tournament/View/17469"
    assert "modern" in result.json_file

def test_should_not_include_other_format_names_in_json_file(client,analyzer):
    tournament = next(
    (t for t in client.get_tournaments(datetime(2022, 11, 19, 0, 0),datetime(2022, 11, 19, 0, 0)) if t.id == 12521),
    None
    )
    result = analyzer.get_scraper_tournaments(tournament)[0]
    assert "pioneer" in result.json_file
    assert "legacy" not in result.json_file

def test_should_ignore_tournaments_with_phases_but_no_decklists(client,analyzer):
    tournament = next(
    (t for t in client.get_tournaments(datetime(2023, 10, 15, 0, 0),datetime(2023, 10, 15, 0, 0)) if t.id == 31590),
    None
    )
    result = analyzer.get_scraper_tournaments(tournament)

    assert result is None

def test_should_handle_pro_tours_correctly(client,analyzer):
    tournament = next(
    (t for t in client.get_tournaments(datetime(2023, 7, 28, 0, 0),datetime(2023, 7, 28, 0, 0)) if t.id == 16429),
    None
    )
    result = analyzer.get_scraper_tournaments(tournament)[0]

    assert result.name == "Pro Tour The Lord of the Rings"
    assert result.date == datetime(2023, 7, 28, 7, 0)
    assert result.uri == "https://melee.gg/Tournament/View/16429"
    assert result.expected_decks == 3
    assert result.deck_offset == 0
    assert result.fix_behavior == "UseFirst" #MtgMeleeMissingDeckBehavior.UseFirst
    assert result.excluded_rounds == ["Round 1", "Round 2", "Round 3", "Round 9", "Round 10", "Round 11"]
    assert "modern" in result.json_file

def test_should_handle_worlds_correctly(client,analyzer):
    tournament = next(t for t in client.get_tournaments(datetime(2024, 10, 23), datetime(2024, 10, 26)) if t.id == 146430)
    result = analyzer.get_scraper_tournaments(tournament)[0]

    assert result.name == "World Championship 30 in Las Vegas"
    assert result.date == datetime(2024, 10, 24, 16, 0, 0)
    assert result.uri == "https://melee.gg/Tournament/View/146430"
    assert result.expected_decks == 3
    assert result.deck_offset == 0
    assert result.fix_behavior == "UseFirst"
    assert result.excluded_rounds == ["Round 1", "Round 2", "Round 3", "Round 9", "Round 10", "Round 11"]
    assert "standard" in result.json_file

def test_should_not_consider_wizards_qualifiers_as_pro_tour(client,analyzer):
    tournament = next(t for t in client.get_tournaments(datetime(2024, 4, 27), datetime(2024, 4, 27)) if t.id == 87465)
    result = analyzer.get_scraper_tournaments(tournament)[0]

    assert result.name == "SATURDAY 2nd Chance Pro Tour Qualifier"
    assert result.date == datetime(2024, 4, 27, 16, 30, 0)
    assert result.uri == "https://melee.gg/Tournament/View/87465"
    assert result.expected_decks is None
    assert result.deck_offset is None
    assert result.fix_behavior is None
    assert result.excluded_rounds is None
    assert "standard" in result.json_file

def test_should_skip_team_tournaments_for_now(client,analyzer):
    tournament = next(t for t in client.get_tournaments(datetime(2023, 7, 8), datetime(2023, 7, 8)) if t.id == 15645)
    result = analyzer.get_scraper_tournaments(tournament)
    assert result is None

#####################################################################################################################################################################################################################################################
# MtgMeleeUpdater test
## TournamentLoaderTests
@pytest.fixture(scope="module")
def tournament_loader_data():
    tournament_loader_data = TournamentList.DL_tournaments(
    start_date = datetime(2023, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
    end_date = datetime(2023, 9, 7, 0, 0, 0, tzinfo=timezone.utc)
    )
    return tournament_loader_data

def test_tournament_count_is_correct(tournament_loader_data):
    assert len(tournament_loader_data) == 12


def test_tournament_data_is_correct(tournament_loader_data):
    test_tournament = tournament_loader_data[0]  
    expected_tournament = MtgMeleeTournament(
        name="Berlin Double Up Legacy VIII im Brettspielplatz 07.09.23",
        date= datetime(2023, 9, 7, 17, 15, 0),
        uri="https://melee.gg/Tournament/View/18285",
        formats="Legacy",
        json_file="berlin-double-up-legacy-viii-im-brettspielplatz-07.09.23-18285-2023-09-07.json"
        )
    assert test_tournament == expected_tournament


############# a faire tester le commander

###################### test commander
# test reject commander multi quand tu aurra trouvé un tournoi sur melee
@pytest.fixture(scope="module")
def DC_test_data(client):
    tournament_data_dc = next(t for t in client.get_tournaments(datetime(2024, 12, 8, 0, 0, 0), datetime(2024, 12,8, 0, 0, 0)) if t.id == 193242)
    DC_test_tournaments_info = analyzer.get_scraper_tournaments(tournament_data_dc)[0]
    DC_test_data = TournamentList().get_tournament_details(DC_test_tournaments_info)
    return  DC_test_data

@pytest.fixture(scope="module")
def DC_reference_deck(DC_test_data):
    DC_reference_deck = DC_test_data.decks[0]
    return  DC_reference_deck


def should_not_load_not_enougth_player_tournament(client):
    tournament_data = next(t for t in client.get_tournaments(datetime(2024, 9, 7), datetime(2024, 9, 7)) if t.uri == "https://melee.gg/Tournament/View/145443")
    not_enoughth_player = analyzer.get_scraper_tournaments(tournament_data)
    assert  not_enoughth_player is None

def should_100_cards_sideboard_between_1to3_duel_commander(DC_reference_deck):
    assert 1 == sum(item.count for item in DC_reference_deck.sideboard) 
    assert sum(item.count for item in DC_reference_deck.mainboard) + sum(item.count for item in DC_reference_deck.sideboard) == 100

def should_have_singleton_duel_commander(DC_reference_deck):
        BASIC_LANDS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}
        non_basic_mainboard = [item for item in DC_reference_deck.mainboard if item.card_name not in BASIC_LANDS]
        non_basic_sideboard = [item for item in DC_reference_deck.sideboard if item.card_name not in BASIC_LANDS]
        # Vérifier que toutes les cartes non-basics ont un count de 1
        assert all(item.count == 1 for item in non_basic_mainboard)
        assert all(item.count == 1 for item in non_basic_sideboard)
        # Vérifier qu'il n'y a pas de doublons de noms de cartes non-basics
        all_card_names = [item.card_name for item in non_basic_mainboard + non_basic_sideboard]
        assert len(all_card_names) == len(set(all_card_names))



# REcherche une liste avec companion 
# Une avec partener 
# Une avec les 2
# quand trouvé une dl legale mettre ce test avec partner et companion
            # (sum(item.count for item in deck.sideboard) == 3 and 
            #  sum(item.count for item in deck.mainboard) + sum(item.count for item in deck.sideboard) == 101)
# Decklist commander with companion mais illegale
def should_correctly_put_companion_in_side_in_DC(DC_test_data):
    DC_companion_deck = DC_test_data.decks[-2]
    assert len(DC_companion_deck.sideboard) == 2
    assert any(item.card_name == "Keruga, the Macrosage" for item in DC_companion_deck.sideboard)

def should_parse_format_duel_commander(DC_test_data):
    assert len(DC_test_data.decks) == 29
    assert DC_test_data.tournament.formats == "Commander"





# https://melee.gg/Decklist/View/461269

# def should_pool_commander_from_free_form():
# duel_commander_tournament = MtgMeleeTournament(
#         uri="https://melee.gg/Tournament/View/15509",
#         date=datetime(2022, 4, 29, 0, 0, 0)
#     )
# test_DC = TournamentList().get_tournament_details(duel_commander_tournament)
