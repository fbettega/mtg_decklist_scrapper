import pytest
from  MTGmelee.MtgMeleeClient import *
import pdb


# try:
#     client = MtgMeleeClient.MtgMeleeClient()
#     players = client.get_players("https://melee.gg/Tournament/View/16429")
#     deck = client.get_deck("https://melee.gg/Decklist/View/315233", players)
#     deck_no_rounds = client.get_deck("https://melee.gg/Decklist/View/315233", players, skip_rounds=True)
# except Exception as e:
#     print(f"An error occurred: {e}")
#     pdb.post_mortem()  # Lance le débogueur en mode post-mortem




@pytest.fixture(scope="module")
def setup_decks():
    client = MtgMeleeClient()
    players = client.get_players("https://melee.gg/Tournament/View/16429")
    deck = client.get_deck("https://melee.gg/Decklist/View/315233", players)
    deck_no_rounds = client.get_deck("https://melee.gg/Decklist/View/315233", players, skip_rounds=True)
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
    assert deck.sideboard == expected_mainboard 


def test_should_include_uri(setup_decks):
    deck, _ = setup_decks
    assert deck.deck_uri == "https://melee.gg/Decklist/View/315233"


def test_should_include_format(setup_decks):
    deck, _ = setup_decks
    assert deck.format == "Modern"


def test_should_respect_flag_to_skip_rounds(setup_decks):
    _, deck_no_rounds = setup_decks
    assert deck_no_rounds.rounds is None


def test_should_not_break_on_decks_missing_rounds():
    client = MtgMeleeClient()
    players = client.get_players(urlparse("https://melee.gg/Tournament/View/21"))
    deck = client.get_deck(urlparse("https://melee.gg/Decklist/View/96"), players)
    assert deck.rounds is None


def test_should_not_break_on_player_names_with_brackets():
    client = MtgMeleeClient()
    players = client.get_players(urlparse("https://melee.gg/Tournament/View/7891"))
    deck = client.get_deck(urlparse("https://melee.gg/Decklist/View/170318"), players)
    assert deck.rounds is not None


def test_should_not_break_on_player_names_with_brackets_getting_a_bye():
    client = MtgMeleeClient()
    players = client.get_players(urlparse("https://melee.gg/Tournament/View/14720"))
    deck = client.get_deck(urlparse("https://melee.gg/Decklist/View/284652"), players)
    assert deck.rounds is not None


def test_should_not_break_on_format_exception_errors():
    client = MtgMeleeClient()
    players = client.get_players(urlparse("https://melee.gg/Tournament/View/15300"))
    deck = client.get_deck(urlparse("https://melee.gg/Decklist/View/292670"), players)
    assert deck.rounds is not None


def test_should_not_break_on_double_forfeit_message():
    client = MtgMeleeClient()
    players = client.get_players(urlparse("https://melee.gg/Tournament/View/65803"))
    deck = client.get_deck(urlparse("https://melee.gg/Decklist/View/399414"), players)
    assert deck.rounds is not None 