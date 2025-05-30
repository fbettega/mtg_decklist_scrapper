import pytest
from datetime import datetime
# import pdb
# import importlib
# import Client.MtgMeleeClient
from Client.MtgMeleeClientV2 import *




##############################################################################################################################################################################################################################################
# MtgMeleeClient test
## Deckloader test
@pytest.fixture(scope="module")
def client():
    client = MtgMeleeClient()
    return client
@pytest.fixture(scope="module")
def Analyzer():
    Analyzer = MtgMeleeAnalyzer()
    return Analyzer
# @pytest.fixture(scope="module")
# def setup_decks(client):
#     players = client.get_players("https://melee.gg/Tournament/View/16429")
#     deck = client.get_deck("https://melee.gg/Decklist/View/315233", players)
#     deck_no_rounds = client.get_deck("https://melee.gg/Decklist/View/315233", players, skip_round_data=True)
#     return deck, deck_no_rounds


# def test_should_load_rounds(setup_decks):
#     deck, _ = setup_decks
#     expected_rounds = [
#         MtgMeleeRoundInfo("Round 1", RoundItem("CHENG YU CHANG", "Javier Dominguez", "2-0-0")),
#         MtgMeleeRoundInfo("Round 2", RoundItem("Javier Dominguez", "Guillaume Wafo-Tapa", "2-0-0")),
#         MtgMeleeRoundInfo("Round 3", RoundItem("Javier Dominguez", "Kelvin Hoon", "2-1-0")),
#         MtgMeleeRoundInfo("Round 4", RoundItem("Marco Del Pivo", "Javier Dominguez", "2-1-0")),
#         MtgMeleeRoundInfo("Round 5", RoundItem("Javier Dominguez", "Lorenzo Terlizzi", "2-0-0")),
#         MtgMeleeRoundInfo("Round 6", RoundItem("Javier Dominguez", "Anthony Lee", "2-1-0")),
#         MtgMeleeRoundInfo("Round 7", RoundItem("Javier Dominguez", "Edgar Magalhaes", "2-0-0")),
#         MtgMeleeRoundInfo("Round 8", RoundItem("Javier Dominguez", "David Olsen", "2-0-0")),
#         MtgMeleeRoundInfo("Round 9", RoundItem("Javier Dominguez", "Matthew Anderson", "2-0-0")),
#         MtgMeleeRoundInfo("Round 10", RoundItem("Javier Dominguez", "Ben Jones", "2-0-0")),
#         MtgMeleeRoundInfo("Round 11", RoundItem("Javier Dominguez", "Yiren Jiang", "2-1-0")),
#         MtgMeleeRoundInfo("Round 12", RoundItem("Javier Dominguez", "Marei Okamura", "2-0-0")),
#         MtgMeleeRoundInfo("Round 13", RoundItem("Javier Dominguez", "Simon Nielsen", "2-0-0")),
#         MtgMeleeRoundInfo("Round 14", RoundItem("Javier Dominguez", "Kazune Kosaka", "2-1-0")),
#         MtgMeleeRoundInfo("Round 15", RoundItem("Javier Dominguez", "Christian Calcano", "2-1-0")),
#         MtgMeleeRoundInfo("Round 16", RoundItem("Javier Dominguez", "-", "2-0-0")),
#         MtgMeleeRoundInfo("Round 17", RoundItem("Dominic Harvey", "Javier Dominguez", "3-1-0")),
#     ]
#     assert deck.rounds == expected_rounds

# def test_should_load_mainboard_cards(setup_decks):
#     deck, _ = setup_decks
#     expected_mainboard = [
#         DeckItem(4, "Ancient Stirrings"),
#         DeckItem(4, "Chromatic Sphere"),
#         DeckItem(1, "Chromatic Star"),
#         DeckItem(4, "Expedition Map"),
#         DeckItem(3, "Relic of Progenitus"),
#         DeckItem(3, "Dismember"),
#         DeckItem(1, "Talisman of Resilience"),
#         DeckItem(3, "Sylvan Scrying"),
#         DeckItem(4, "Oblivion Stone"),
#         DeckItem(4, "Karn, the Great Creator"),
#         DeckItem(4, "The One Ring"),
#         DeckItem(2, "Wurmcoil Engine"),
#         DeckItem(1, "Karn Liberated"),
#         DeckItem(2, "Ulamog, the Ceaseless Hunger"),
#         DeckItem(1, "Warping Wail"),
#         DeckItem(1, "Boseiju, Who Endures"),
#         DeckItem(3, "Forest"),
#         DeckItem(4, "Urza's Mine"),
#         DeckItem(4, "Urza's Power Plant"),
#         DeckItem(4, "Urza's Tower"),
#         DeckItem(2, "Urza's Saga"),
#         DeckItem(1, "Walking Ballista")
#     ]
#     assert deck.mainboard == expected_mainboard
    
# def test_should_load_sideboard_cards(setup_decks):
#     deck, _ = setup_decks
#     expected_sideboard = [
#         DeckItem(2, "Haywire Mite"),
#         DeckItem(1, "Cityscape Leveler"),
#         DeckItem(1, "Tormod's Crypt"),
#         DeckItem(1, "Pithing Needle"),
#         DeckItem(1, "Liquimetal Coating"),
#         DeckItem(1, "The Stone Brain"),
#         DeckItem(1, "Ensnaring Bridge"),
#         DeckItem(1, "Sundering Titan"),
#         DeckItem(1, "Engineered Explosives"),
#         DeckItem(1, "Walking Ballista"),
#         DeckItem(1, "Wurmcoil Engine"),
#         DeckItem(1, "Chalice of the Void"),
#         DeckItem(1, "Grafdigger's Cage"),
#         DeckItem(1, "Phyrexian Metamorph")
#     ]
#     assert deck.sideboard == expected_sideboard 


# def test_should_include_uri(setup_decks):
#     deck, _ = setup_decks
#     assert deck.deck_uri == "https://melee.gg/Decklist/View/315233"


# def test_should_include_format(setup_decks):
#     deck, _ = setup_decks
#     assert deck.format == "Modern"


# def test_should_respect_flag_to_skip_rounds(setup_decks):
#     _, deck_no_rounds = setup_decks
#     assert deck_no_rounds.rounds == []


# def test_should_not_break_on_decks_missing_rounds( client):
#     players = client.get_players("https://melee.gg/Tournament/View/21")
#     deck = client.get_deck("https://melee.gg/Decklist/View/96", players)
#     assert deck.rounds == []


# def test_should_not_break_on_player_names_with_brackets( client):
#     players = client.get_players("https://melee.gg/Tournament/View/7891")
#     deck = client.get_deck("https://melee.gg/Decklist/View/170318", players)
#     assert deck.rounds is not None


# def test_should_not_break_on_player_names_with_brackets_getting_a_bye( client):
#     players = client.get_players("https://melee.gg/Tournament/View/14720")
#     deck = client.get_deck("https://melee.gg/Decklist/View/284652", players)
#     assert deck.rounds is not None


# def test_should_not_break_on_format_exception_errors():
#     client = MtgMeleeClient()
#     players = client.get_players("https://melee.gg/Tournament/View/15300")
#     deck = client.get_deck("https://melee.gg/Decklist/View/292670", players)
#     assert deck.rounds is not None


# def test_should_not_break_on_double_forfeit_message( client):
#     players = client.get_players("https://melee.gg/Tournament/View/65803")
#     deck = client.get_deck("https://melee.gg/Decklist/View/399414", players)
#     assert deck.rounds is not None 

# # MtgMeleeClient test
# ## NameError Tests 
# def test_should_fix_name_for_magnifying_glass_enthusiast(client):
#     players = client.get_players("https://melee.gg/Tournament/View/8248")
#     deck = client.get_deck("https://melee.gg/Decklist/View/182814", players)
#     assert any(c.card_name == "Jacob Hauken, Inspector" for c in deck.mainboard)

# def test_should_fix_voltaic_visionary(  client):
#     players = client.get_players("https://melee.gg/Tournament/View/8248")
#     deck = client.get_deck("https://melee.gg/Decklist/View/182336", players)
#     assert any(c.card_name == "Voltaic Visionary" for c in deck.mainboard)


# def test_should_fix_name_sticker_goblin(  client):
#     players = client.get_players("https://melee.gg/Tournament/View/17900")
#     deck = client.get_deck("https://melee.gg/Decklist/View/329567", players)
#     assert any(c.card_name == "_____ Goblin" for c in deck.mainboard)

# # MtgMeleeClient test
# ## PlayerLoader Tests 
# @pytest.fixture(scope="module")
# def players(  client):
#     players = client.get_players("https://melee.gg/Tournament/View/72980")
#     return players

# def test_should_load_number_of_players(  players):
#     assert len(players) == 207

# def test_should_include_user_names(  players):
#     for player in players:
#         assert player.username is not None and player.username != ""

# def test_should_include_player_names(  players):
#     for player in players:
#         assert player.player_name is not None and player.player_name != ""

# def test_should_include_results(  players):
#     for player in players:
#         assert player.result is not None and player.result != ""

# def test_should_include_correct_result_data(  players):
#     assert players[0].result == "18-1-0"

# def test_should_load_standings(  players):
#     for player in players:
#         assert player.standing is not None

# def test_should_include_correct_standings_data(  players):
#     expected = Standing(1,"Yoshihiko Ikawa", 54, 18, 1, 0, 0.62502867, 0.75, 0.57640079)
#     assert players[0].standing == expected

# def test_should_include_correct_standings_data_with_draws(  players):
#     expected = Standing(2,"Yuta Takahashi",  41, 13, 4, 2, 0.59543296, 0.68027211, 0.55188929)
#     assert players[1].standing == expected

# def test_should_load_deck_uris(  players):
#     for player in players:
#         for deck in player.decks:
#             assert deck.uri is not None

# def test_should_load_deck_format(  players):
#     for player in players:
#         for deck in player.decks:
#             assert deck.format is not None


# def test_should_load_correct_deck_uris(  players):
#     assert players[7].decks[0].uri == "https://melee.gg/Decklist/View/391605"



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


# MtgMeleeClient test
## TournamentListLoaderTests
@pytest.fixture(scope="module")
def tournament_results(client):
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
    test_data = TournamentList().get_tournament_details(tournament).decks
    return test_data

# a faire tester les dictionnaire
# def to_dict_cache_item_should_return_correct_dict():
#     # je pense que cette appel est pété
#     tournament = MtgMeleeTournament(
#         uri="https://melee.gg/Tournament/View/12867",
#         date=datetime(2022, 11, 19, 0, 0, 0)
#     )
#     test_to_ditc = TournamentList().get_tournament_details(tournament)



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
        date=None,
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
        date=test_data[3].date  ,
        deck_uri=test_data[3].deck_uri,
        player=test_data[3].player,
        format=test_data[3].format,
        result=test_data[3].result,
        mainboard=test_data[3].mainboard,
        sideboard=test_data[3].sideboard,
        rounds=[]  
    )

    assert test_data_no_rounds == expected_deck

# MtgMeleeUpdater test
## RoundsLoaderTests

@pytest.fixture
def test_data_round(client):
    # Setup des données de test
    tournament_1 = MtgMeleeTournament(
        uri="https://melee.gg/Tournament/View/12867", 
        date=datetime(2022, 11, 19, 0, 0, 0)
        )
    test_data_round = TournamentList().get_tournament_details(tournament_1).rounds    
    return test_data_round

@pytest.fixture
def test_data_round2():
    tournament_2 = MtgMeleeTournament(
        uri="https://melee.gg/Tournament/View/7708",
         date=datetime(2021, 11, 9, 0, 0, 0)
         )
    test_data_round2 = TournamentList().get_tournament_details(tournament_2).rounds
    return test_data_round2

@pytest.fixture
def test_data_round3(client):
    tournament_3 = MtgMeleeTournament(
        uri="https://melee.gg/Tournament/View/12946",
         date=datetime(2022, 11, 20, 0, 0, 0)
         )
    test_data_round3 = TournamentList().get_tournament_details(tournament_3).rounds
    return test_data_round3

@pytest.fixture
def test_data_round4(client):
    tournament_4 = MtgMeleeTournament(
        uri="https://melee.gg/Tournament/View/12867", 
        date=datetime(2022, 11, 19, 0, 0, 0), 
        excluded_rounds=["Round 1"])
    test_data_round4 = TournamentList().get_tournament_details(tournament_4).rounds
    return test_data_round4

def test_round_count_is_correct(test_data_round):
    assert len(test_data_round) == 5

def test_rounds_have_name(test_data_round):
    for round in test_data_round:
        assert round.round_name is not None and round.round_name != ""

def test_rounds_have_matches(test_data_round):
    for round in test_data_round:
        assert len(round.matches) > 0

def test_round_data_is_correct(test_data_round):
    test_round = test_data_round[0]
    assert test_round.round_name == "Round 1"
    assert test_round.matches[0] == RoundItem(player1="removed removed", player2="agesZ #84443", result="2-0-0")

def test_should_parse_byes_correctly(test_data_round2):
    round_3 = [r for r in test_data_round2 if r.round_name == "Round 3"]
    match = next((m for m in round_3[0].matches if m.player1 == "Er_gitta"), None)
    assert match == RoundItem(player1="Er_gitta", player2="-", result="2-0-0")

def test_should_parse_draws_correctly(test_data_round3):
    round_5 = [r for r in test_data_round3 if r.round_name == "Round 5"]
    match = next((m for m in round_5[0].matches if m.player1 == "Arthur Rodrigues"), None)
    assert match == RoundItem(player1="Arthur Rodrigues", player2="RudsonC", result="0-0-3")

def test_should_parse_missing_opponent_correctly(test_data_round2):
    round_4 = [r for r in test_data_round2 if r.round_name == "Round 4"]
    match = next((m for m in round_4[0].matches if m.player1 == "Taerian van Rensburg"), None)
    assert match == RoundItem(player1="Taerian van Rensburg", player2 = None, result="2-0-0")

def test_should_be_able_to_skip_rounds(test_data_round4):
    test_round = test_data_round4[0]
    assert test_round.round_name == "Round 2"

# MtgMeleeUpdater test
## StandingsLoaderTests
@pytest.fixture
def test_data_standings(client):
    tournament = MtgMeleeTournament(
        uri="https://melee.gg/Tournament/View/86543"
        )
    test_data_standings = TournamentList().get_tournament_details(tournament).standings
    return test_data_standings
# Test cases
def test_standings_count_is_correct(test_data_standings):
    assert len(test_data_standings) == 9  # Adjust count based on mock data size

# Test cases
def test_standings_have_players(test_data_standings):
    for standing in test_data_standings:
        assert standing.player

def test_standings_have_rank(test_data_standings):
    for standing in test_data_standings:
        assert standing.rank > 0

def test_standings_have_points(test_data_standings):
    for standing in test_data_standings[:-1]:  
        assert standing.points > 0

def test_standings_have_omwp(test_data_standings):
    for standing in test_data_standings:
        assert standing.omwp > 0

def test_decks_have_gwp(test_data_standings):
    for standing in test_data_standings:
        assert standing.gwp > 0

def test_decks_have_ogwp(test_data_standings):
    for standing in test_data_standings:
        assert standing.ogwp > 0

def test_standing_data_is_correct(test_data_standings):
    test_standing = test_data_standings[3]  # Access the 4th standing
    expected_standing = Standing(rank=4, player="Elston", points=6, wins=2, losses=2, draws=0, omwp=0.75, gwp=0.44444444, ogwp=0.75661376)
    assert test_standing == expected_standing


# pytest .\tests\MtgMeleeAnalyser.py    
base_t = client.get_tournaments(datetime(2025, 2, 21, 0, 0, 0, tzinfo=timezone.utc),datetime(2025, 2, 28, 0, 0, 0, tzinfo=timezone.utc))
def test_should_detect_simple_tournaments(client,analyzer):
    tournament =  next(
    (t for t in client.get_tournaments(datetime(2025, 2, 21, 0, 0, 0, tzinfo=timezone.utc),datetime(2025, 2, 28, 0, 0, 0, tzinfo=timezone.utc)) if t.id == 255445),
    None
    )
    result = analyzer.get_scraper_tournaments(tournament)[0]

    assert result.name == "Weekly Legacy"
    assert result.date == datetime(2025, 2, 27, 23, 5)
    assert result.uri == "https://melee.gg/Tournament/View/255445"

# def test_should_not_include_other_format_names_in_json_file(client,analyzer):
#     tournament = next(
#     (t for t in client.get_tournaments(datetime(2022, 11, 19, 0, 0),datetime(2022, 11, 19, 0, 0)) if t.id == 12521),
#     None
#     )
#     result = analyzer.get_scraper_tournaments(tournament)[0]
#     assert "pioneer" in result.json_file
#     assert "legacy" not in result.json_file

# def test_should_ignore_tournaments_with_phases_but_no_decklists(client,analyzer):
#     tournament = next(
#     (t for t in client.get_tournaments(datetime(2023, 10, 15, 0, 0),datetime(2023, 10, 15, 0, 0)) if t.id == 31590),
#     None
#     )
#     result = analyzer.get_scraper_tournaments(tournament)

#     assert result is None

# def test_should_handle_pro_tours_correctly(client,analyzer):
#     tournament = next(
#     (t for t in client.get_tournaments(datetime(2023, 7, 28, 0, 0),datetime(2023, 7, 28, 0, 0)) if t.id == 16429),
#     None
#     )
#     result = analyzer.get_scraper_tournaments(tournament)[0]

#     assert result.name == "Pro Tour The Lord of the Rings"
#     assert result.date == datetime(2023, 7, 28, 7, 0)
#     assert result.uri == "https://melee.gg/Tournament/View/16429"
#     assert result.expected_decks == 3
#     assert result.deck_offset == 0
#     assert result.fix_behavior == "UseFirst" #MtgMeleeMissingDeckBehavior.UseFirst
#     assert result.excluded_rounds == ["Round 1", "Round 2", "Round 3", "Round 9", "Round 10", "Round 11"]
#     assert "modern" in result.json_file

# def test_should_handle_worlds_correctly(client,analyzer):
#     tournament = next(t for t in client.get_tournaments(datetime(2024, 10, 23), datetime(2024, 10, 26)) if t.id == 146430)
#     result = analyzer.get_scraper_tournaments(tournament)[0]

#     assert result.name == "World Championship 30 in Las Vegas"
#     assert result.date == datetime(2024, 10, 24, 16, 0, 0)
#     assert result.uri == "https://melee.gg/Tournament/View/146430"
#     assert result.expected_decks == 3
#     assert result.deck_offset == 0
#     assert result.fix_behavior == "UseFirst"
#     assert result.excluded_rounds == ["Round 1", "Round 2", "Round 3", "Round 9", "Round 10", "Round 11"]
#     assert "standard" in result.json_file

# def test_should_not_consider_wizards_qualifiers_as_pro_tour(client,analyzer):
#     tournament = next(t for t in client.get_tournaments(datetime(2024, 4, 27), datetime(2024, 4, 27)) if t.id == 87465)
#     result = analyzer.get_scraper_tournaments(tournament)[0]

#     assert result.name == "SATURDAY 2nd Chance Pro Tour Qualifier"
#     assert result.date == datetime(2024, 4, 27, 16, 30, 0)
#     assert result.uri == "https://melee.gg/Tournament/View/87465"
#     assert result.expected_decks is None
#     assert result.deck_offset is None
#     assert result.fix_behavior is None
#     assert result.excluded_rounds is None
#     assert "standard" in result.json_file

# def test_should_skip_team_tournaments_for_now(client,analyzer):
#     tournament = next(t for t in client.get_tournaments(datetime(2023, 7, 8), datetime(2023, 7, 8)) if t.id == 15645)
#     result = analyzer.get_scraper_tournaments(tournament)
#     assert result is None

#####################################################################################################################################################################################################################################################
# MtgMeleeUpdater test
## TournamentLoaderTests
@pytest.fixture(scope="module")
def tournament_loader_data():
    tournament_loader_data = TournamentList.DL_tournaments(
    start_date = datetime(2025, 2, 21, 0, 0, 0, tzinfo=timezone.utc),
    end_date = datetime(2025, 2, 28, 0, 0, 0, tzinfo=timezone.utc)
    )
    return tournament_loader_data

def test_tournament_count_is_correct(tournament_loader_data):
    assert len(tournament_loader_data) == 26


def test_tournament_data_is_correct(tournament_loader_data):
    test_tournament = tournament_loader_data[0]  
    expected_tournament = MtgMeleeTournament(
        name="Weekly Legacy",
        date= datetime(2025, 2, 27, 23, 5),
        uri="https://melee.gg/Tournament/View/255445",
        formats="Legacy",
        json_file="weekly-legacy-255445-2025-02-27.json"
        )
    assert test_tournament == expected_tournament


###################### test commander
# test reject commander multi quand tu aurra trouvé un tournoi sur melee
# @pytest.fixture(scope="module")
# def DC_test_data(client):
#     tournament_data_dc = next(t for t in client.get_tournaments(datetime(2024, 12, 8, 0, 0, 0), datetime(2024, 12,8, 0, 0, 0)) if t.id == 193242)
#     DC_test_tournaments_info = analyzer.get_scraper_tournaments(tournament_data_dc)[0]
#     DC_test_data = TournamentList().get_tournament_details(DC_test_tournaments_info)
#     return  DC_test_data

# @pytest.fixture(scope="module")
# def DC_reference_deck(DC_test_data):
#     DC_reference_deck = DC_test_data.decks[0]
#     return  DC_reference_deck


# def should_not_load_not_enougth_player_tournament(client):
#     tournament_data = next(t for t in client.get_tournaments(datetime(2024, 9, 7), datetime(2024, 9, 7)) if t.uri == "https://melee.gg/Tournament/View/145443")
#     not_enoughth_player = analyzer.get_scraper_tournaments(tournament_data)
#     assert  not_enoughth_player is None

# def should_100_cards_sideboard_between_1to3_duel_commander(DC_reference_deck):
#     assert 1 == sum(item.count for item in DC_reference_deck.sideboard) 
#     assert sum(item.count for item in DC_reference_deck.mainboard) + sum(item.count for item in DC_reference_deck.sideboard) == 100

# def should_have_singleton_duel_commander(DC_reference_deck):
#         BASIC_LANDS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}
#         non_basic_mainboard = [item for item in DC_reference_deck.mainboard if item.card_name not in BASIC_LANDS]
#         non_basic_sideboard = [item for item in DC_reference_deck.sideboard if item.card_name not in BASIC_LANDS]
#         # Vérifier que toutes les cartes non-basics ont un count de 1
#         assert all(item.count == 1 for item in non_basic_mainboard)
#         assert all(item.count == 1 for item in non_basic_sideboard)
#         # Vérifier qu'il n'y a pas de doublons de noms de cartes non-basics
#         all_card_names = [item.card_name for item in non_basic_mainboard + non_basic_sideboard]
#         assert len(all_card_names) == len(set(all_card_names))



# REcherche une liste avec companion 
# Une avec partener 
# Une avec les 2
# quand trouvé une dl legale mettre ce test avec partner et companion
            # (sum(item.count for item in deck.sideboard) == 3 and 
            #  sum(item.count for item in deck.mainboard) + sum(item.count for item in deck.sideboard) == 101)
# Decklist commander with companion mais illegale
# def should_correctly_put_companion_in_side_in_DC(DC_test_data):
#     DC_companion_deck = DC_test_data.decks[-2]
#     assert len(DC_companion_deck.sideboard) == 2
#     assert any(item.card_name == "Keruga, the Macrosage" for item in DC_companion_deck.sideboard)

# def should_parse_format_duel_commander(DC_test_data):
#     assert len(DC_test_data.decks) == 29
#     assert DC_test_data.tournament.formats == "Commander"





# https://melee.gg/Decklist/View/461269

# def should_pool_commander_from_free_form():
# duel_commander_tournament = MtgMeleeTournament(
#         uri="https://melee.gg/Tournament/View/15509",
#         date=datetime(2022, 4, 29, 0, 0, 0)
#     )
# test_DC = TournamentList().get_tournament_details(duel_commander_tournament)
