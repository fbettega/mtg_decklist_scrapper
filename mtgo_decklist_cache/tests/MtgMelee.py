import pytest
# from  MTGmelee.MtgMeleeClient import *
import pdb
import importlib

import MTGmelee.MtgMeleeClient

# Recharger le module
importlib.reload(MTGmelee.MtgMeleeClient)
# pytest .\tests\MtgMelee.py 
# Réimporter tous les objets exportés par le module
from MTGmelee.MtgMeleeClient import *

# try:
#     client = MtgMeleeClient()
#     players = client.get_players("https://melee.gg/Tournament/View/16429")
#     deck = client.get_deck("https://melee.gg/Decklist/View/315233", players)
#     deck_no_rounds = client.get_deck("https://melee.gg/Decklist/View/315233", players, skip_round_data=True)
# except Exception as e:
#     print(f"An error occurred: {e}")
#     pdb.post_mortem()  # Lance le débogueur en mode post-mortem

# FAILED tests/MtgMelee.py::test_should_not_break_on_double_forfeit_message - ValueError: Cannot parse round data for player Tomoya Kobayashi and opponent Masashiro Kuroda


##############################################################################################################################################################################################################################################
# MtgMeleeClient test
## Deckloader test
@pytest.fixture(scope="module")
def client():
    client = MtgMeleeClient()
    return client

@pytest.fixture(scope="module")
def setup_decks(client):
    players = client.get_players("https://melee.gg/Tournament/View/16429")
    deck = client.get_deck("https://melee.gg/Decklist/View/315233", players)
    deck_no_rounds = client.get_deck("https://melee.gg/Decklist/View/315233", players, skip_round_data=True)
    return deck, deck_no_rounds


def test_should_load_rounds(setup_decks):
    deck, _ = setup_decks
    expected_rounds = [
        MtgMeleeRoundInfo("Round 1", RoundItem("CHENG YU CHANG", "Javier Dominguez", "2-0-0")),
        MtgMeleeRoundInfo("Round 2", RoundItem("Javier Dominguez", "Guillaume Wafo-Tapa", "2-0-0")),
        MtgMeleeRoundInfo("Round 3", RoundItem("Javier Dominguez", "Kelvin Hoon", "2-1-0")),
        MtgMeleeRoundInfo("Round 4", RoundItem("Marco Del Pivo", "Javier Dominguez", "2-1-0")),
        MtgMeleeRoundInfo("Round 5", RoundItem("Javier Dominguez", "Lorenzo Terlizzi", "2-0-0")),
        MtgMeleeRoundInfo("Round 6", RoundItem("Javier Dominguez", "Anthony Lee", "2-1-0")),
        MtgMeleeRoundInfo("Round 7", RoundItem("Javier Dominguez", "Edgar Magalhaes", "2-0-0")),
        MtgMeleeRoundInfo("Round 8", RoundItem("Javier Dominguez", "David Olsen", "2-0-0")),
        MtgMeleeRoundInfo("Round 9", RoundItem("Javier Dominguez", "Matthew Anderson", "2-0-0")),
        MtgMeleeRoundInfo("Round 10", RoundItem("Javier Dominguez", "Ben Jones", "2-0-0")),
        MtgMeleeRoundInfo("Round 11", RoundItem("Javier Dominguez", "Yiren Jiang", "2-1-0")),
        MtgMeleeRoundInfo("Round 12", RoundItem("Javier Dominguez", "Marei Okamura", "2-0-0")),
        MtgMeleeRoundInfo("Round 13", RoundItem("Javier Dominguez", "Simon Nielsen", "2-0-0")),
        MtgMeleeRoundInfo("Round 14", RoundItem("Javier Dominguez", "Kazune Kosaka", "2-1-0")),
        MtgMeleeRoundInfo("Round 15", RoundItem("Javier Dominguez", "Christian Calcano", "2-1-0")),
        MtgMeleeRoundInfo("Round 16", RoundItem("Javier Dominguez", "-", "2-0-0")),
        MtgMeleeRoundInfo("Round 17", RoundItem("Dominic Harvey", "Javier Dominguez", "3-1-0")),
    ]
    assert deck.rounds == expected_rounds

def test_should_load_mainboard_cards(setup_decks):
    deck, _ = setup_decks
    expected_mainboard = [
        DeckItem(4, "Ancient Stirrings"),
        DeckItem(4, "Chromatic Sphere"),
        DeckItem(1, "Chromatic Star"),
        DeckItem(4, "Expedition Map"),
        DeckItem(3, "Relic of Progenitus"),
        DeckItem(3, "Dismember"),
        DeckItem(1, "Talisman of Resilience"),
        DeckItem(3, "Sylvan Scrying"),
        DeckItem(4, "Oblivion Stone"),
        DeckItem(4, "Karn, the Great Creator"),
        DeckItem(4, "The One Ring"),
        DeckItem(2, "Wurmcoil Engine"),
        DeckItem(1, "Karn Liberated"),
        DeckItem(2, "Ulamog, the Ceaseless Hunger"),
        DeckItem(1, "Warping Wail"),
        DeckItem(1, "Boseiju, Who Endures"),
        DeckItem(3, "Forest"),
        DeckItem(4, "Urza's Mine"),
        DeckItem(4, "Urza's Power Plant"),
        DeckItem(4, "Urza's Tower"),
        DeckItem(2, "Urza's Saga"),
        DeckItem(1, "Walking Ballista")
    ]
    assert deck.mainboard == expected_mainboard
    
def test_should_load_sideboard_cards(setup_decks):
    deck, _ = setup_decks
    expected_sideboard = [
        DeckItem(2, "Haywire Mite"),
        DeckItem(1, "Cityscape Leveler"),
        DeckItem(1, "Tormod's Crypt"),
        DeckItem(1, "Pithing Needle"),
        DeckItem(1, "Liquimetal Coating"),
        DeckItem(1, "The Stone Brain"),
        DeckItem(1, "Ensnaring Bridge"),
        DeckItem(1, "Sundering Titan"),
        DeckItem(1, "Engineered Explosives"),
        DeckItem(1, "Walking Ballista"),
        DeckItem(1, "Wurmcoil Engine"),
        DeckItem(1, "Chalice of the Void"),
        DeckItem(1, "Grafdigger's Cage"),
        DeckItem(1, "Phyrexian Metamorph")
    ]
    assert deck.sideboard == expected_sideboard 


def test_should_include_uri(setup_decks):
    deck, _ = setup_decks
    assert deck.deck_uri == "https://melee.gg/Decklist/View/315233"


def test_should_include_format(setup_decks):
    deck, _ = setup_decks
    assert deck.format == "Modern"


def test_should_respect_flag_to_skip_rounds(setup_decks):
    _, deck_no_rounds = setup_decks
    assert deck_no_rounds.rounds == []


def test_should_not_break_on_decks_missing_rounds( client):
    players = client.get_players("https://melee.gg/Tournament/View/21")
    deck = client.get_deck("https://melee.gg/Decklist/View/96", players)
    assert deck.rounds == []


def test_should_not_break_on_player_names_with_brackets( client):
    players = client.get_players("https://melee.gg/Tournament/View/7891")
    deck = client.get_deck("https://melee.gg/Decklist/View/170318", players)
    assert deck.rounds is not None


def test_should_not_break_on_player_names_with_brackets_getting_a_bye( client):
    players = client.get_players("https://melee.gg/Tournament/View/14720")
    deck = client.get_deck("https://melee.gg/Decklist/View/284652", players)
    assert deck.rounds is not None


def test_should_not_break_on_format_exception_errors():
    client = MtgMeleeClient()
    players = client.get_players("https://melee.gg/Tournament/View/15300")
    deck = client.get_deck("https://melee.gg/Decklist/View/292670", players)
    assert deck.rounds is not None


def test_should_not_break_on_double_forfeit_message( client):
    players = client.get_players("https://melee.gg/Tournament/View/65803")
    deck = client.get_deck("https://melee.gg/Decklist/View/399414", players)
    assert deck.rounds is not None 

# MtgMeleeClient test
## NameError Tests 
def test_should_fix_name_for_magnifying_glass_enthusiast(client):
    players = client.get_players("https://melee.gg/Tournament/View/8248")
    deck = client.get_deck("https://melee.gg/Decklist/View/182814", players)
    assert any(c.card_name == "Jacob Hauken, Inspector" for c in deck.mainboard)

def test_should_fix_voltaic_visionary(  client):
    players = client.get_players("https://melee.gg/Tournament/View/8248")
    deck = client.get_deck("https://melee.gg/Decklist/View/182336", players)
    assert any(c.card_name == "Voltaic Visionary" for c in deck.mainboard)


def test_should_fix_name_sticker_goblin(  client):
    players = client.get_players("https://melee.gg/Tournament/View/17900")
    deck = client.get_deck("https://melee.gg/Decklist/View/329567", players)
    assert any(c.card_name == "_____ Goblin" for c in deck.mainboard)

# MtgMeleeClient test
## PlayerLoader Tests 
@pytest.fixture(scope="module")
def players(  client):
    players = client.get_players("https://melee.gg/Tournament/View/72980")
    return players

def test_should_load_number_of_players(  players):
    assert len(players) == 207

def test_should_include_user_names(  players):
    for player in players:
        assert player.username is not None and player.username != ""

def test_should_include_player_names(  players):
    for player in players:
        assert player.player_name is not None and player.player_name != ""

def test_should_include_results(  players):
    for player in players:
        assert player.result is not None and player.result != ""

def test_should_include_correct_result_data(  players):
    assert players[0].result == "18-1-0"

def test_should_load_standings(  players):
    for player in players:
        assert player.standing is not None

def test_should_include_correct_standings_data(  players):
    expected = Standing("Yoshihiko Ikawa", 1, 54, 0.62502867, 0.75, 0.57640079, 18, 1, 0)
    assert players[0].standing == expected

def test_should_include_correct_standings_data_with_draws(  players):
    expected = Standing("Yuta Takahashi", 2, 41, 0.59543296, 0.68027211, 0.55188929, 13, 4, 2)
    assert players[1].standing == expected

def test_should_load_deck_uris(  players):
    for player in players:
        for deck in player.decks:
            assert deck.uri is not None

def test_should_load_deck_format(  players):
    for player in players:
        for deck in player.decks:
            assert deck.format is not None


def test_should_load_correct_deck_uris(  players):
    assert players[7].decks[0].uri == "https://melee.gg/Decklist/View/391605"

# @pytest.mark.skip("Not implemented")
# def test_should_load_correct_deck_uris_when_multiple_present(  players):
#     players[0].decks = [
#         MagicMock(uri="https://melee.gg/Decklist/View/391788"),
#         MagicMock(uri="https://melee.gg/Decklist/View/393380")
#     ]
#     assert [deck.uri for deck in players[0].decks] == [
#         "https://melee.gg/Decklist/View/391788",
#         "https://melee.gg/Decklist/View/393380"
#     ]

def test_should_support_limiting_players(  client):
    players_25 = client.get_players("https://melee.gg/Tournament/View/16429", max_players=25)
    assert len(players_25) == 25

def test_should_correctly_map_player_name_to_user_name(  client):
    players_name_user_name = client.get_players("https://melee.gg/Tournament/View/16429")
    assert next(p.username for p in players_name_user_name if p.player_name == "koki hara") == "BlooMooNight"

def test_should_not_break_on_empty_tournaments(  client):
    players_empty_tournament = client.get_players("https://melee.gg/Tournament/View/31590")
    assert players_empty_tournament is None

def test_should_load_players_for_tournaments_with_empty_last_phase(  client):
    players_empty_last_phase = client.get_players("https://melee.gg/Tournament/View/52904")
    assert players_empty_last_phase is not None and len(players_empty_last_phase) > 0

# @pytest.mark.skip("Not implemented")
# def test_should_ensure_decks_for_the_same_format_are_in_the_same_position(  client):
#     players = [
#         MagicMock(decks=[MagicMock(format="Standard"), MagicMock(format="Standard"), MagicMock(format="Standard")])
#     ]
#     formats = [deck.format for deck in players[0].decks]
#     assert len(set(formats)) == 1


# MtgMeleeClient test
## TournamentListLoaderTests
@pytest.fixture(scope="module")
def tournament_results(  client):
    tournament_results = client.get_tournaments(
        datetime(2023, 9, 1), datetime(2023, 9, 7)
        )
    return tournament_results

def test_should_have_correct_count(  tournament_results):

    assert len(tournament_results) == 23


def test_should_have_correct_results(tournament_results):
    expected = MtgMeleeTournamentInfo(
        tournament_id=25360,
        date=datetime(2023, 9, 7, 19, 0, 0),
        name="Legacy League Pavia 23/24 - Tappa 12",
        organizer="Legacy Pavia",
        formats=["Legacy"],
        uri="https://melee.gg/Tournament/View/25360",
        decklists=13
    )
    assert tournament_results[0] == expected

def test_should_have_correct_count_for_multi_page_request(  client):
    tournament_results_many_pages = client.get_tournaments(
        datetime(2023, 9, 1), datetime(2023, 9, 12)
        )
    assert len(tournament_results_many_pages) == 41

# end of  MtgMeleeClient test
##############################################################################################################################################################################################################################################
# MtgMeleeUpdater test
## Deckloader test
@pytest.fixture
def test_data(  client):
    # je pense que cette appel est pété
    tournament = MtgMeleeTournament(
        uri="https://melee.gg/Tournament/View/12867",
        date=datetime(2022, 11, 19, 0, 0, 0)
    )

    test_data = client.get_tournament_details(tournament).decks

    return test_data




def test_deck_count_is_correct(test_data):
    assert len(test_data) == 6  

# def test_decks_dont_have_date(test_data):
#     for deck in test_data:
#         deck.date is None
#         assert deck.date is None

def test_decks_have_players(test_data):
    for deck in test_data:
        assert deck.player is not None and deck.player != ""

def test_decks_have_mainboards(test_data):
    for deck in test_data:
        assert len(deck.mainboard) > 0

def test_decks_have_sideboards(test_data):
    for deck in test_data:
        assert len(deck.sideboard) > 0

def test_decks_have_valid_mainboards(test_data):
    for deck in test_data:
        assert sum(item.count for item in deck.mainboard) >= 60

def test_decks_have_valid_sideboards(test_data):
    for deck in test_data:
        assert sum(item.count for item in deck.sideboard) <= 15

def test_deck_data_is_correct(test_data):
    expected_deck = MtgMeleeDeckInfo(
        deck_uri= "https://melee.gg/Decklist/View/257079",
        player="SB36",
        format='Explorer',
        mainboard = [
            DeckItem(4, "The Mightstone and Weakstone"),
            DeckItem(3, "Urza, Lord Protector"),
            DeckItem(4, "Bonecrusher Giant"),
            DeckItem(4, "Omnath, Locus of Creation"),
            DeckItem(4, "Fable of the Mirror-Breaker"),
            DeckItem(1, "Temporary Lockdown"),
            DeckItem(4, "Leyline Binding"),
            DeckItem(4, "Fires of Invention"),
            DeckItem(1, "Snow-Covered Forest"),
            DeckItem(1, "Stomping Ground"),
            DeckItem(1, "Snow-Covered Mountain"),
            DeckItem(1, "Boseiju, Who Endures"),
            DeckItem(1, "Temple Garden"),
            DeckItem(1, "Breeding Pool"),
            DeckItem(1, "Steam Vents"),
            DeckItem(2, "Ketria Triome"),
            DeckItem(1, "Snow-Covered Island"),
            DeckItem(1, "Snow-Covered Plains"),
            DeckItem(2, "Hallowed Fountain"),
            DeckItem(1, "Spara's Headquarters"),
            DeckItem(1, "Ziatora's Proving Ground"),
            DeckItem(1, "Indatha Triome"),
            DeckItem(2, "Sacred Foundry"),
            DeckItem(2, "Jetmir's Garden"),
            DeckItem(3, "Raugrin Triome"),
            DeckItem(4, "Fabled Passage"),
            DeckItem(1, "Colossal Skyturtle"),
            DeckItem(1, "Otawara, Soaring City"),
            DeckItem(1, "Touch the Spirit Realm"),
            DeckItem(2, "Supreme Verdict")
        ],

        sideboard = [
            DeckItem(1, "Keruga, the Macrosage"),
            DeckItem(1, "Chandra, Awakened Inferno"),
            DeckItem(4, "Leyline of the Void"),
            DeckItem(3, "Mystical Dispute"),
            DeckItem(1, "Supreme Verdict"),
            DeckItem(3, "Knight of Autumn"),
            DeckItem(1, "Temporary Lockdown"),
            DeckItem(1, "Twinshot Sniper")
        ],
        result="4th Place"
    )
    test_data_no_rounds = MtgMeleeDeckInfo(
        deck_uri=test_data[3].deck_uri,
        player=test_data[3].player,
        format=test_data[3].format,
        result=test_data[3].result,
        mainboard=test_data[3].mainboard,
        sideboard=test_data[3].sideboard,
        rounds=[]  
    )

    assert test_data_no_rounds == expected_deck





