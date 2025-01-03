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


#######################################################################################################
# StandingsLoaderTests
@pytest.fixture
def standings_data():
    tournament = Tournament(uri="https://www.manatraders.com/tournaments/30/", date=datetime(2022, 8, 31))
    standings_data = TournamentList().get_tournament_details(tournament).standings
    return standings_data


def test_standings_count_is_correct(standings_data):
    assert len(standings_data) == 195


def test_standings_have_players(standings_data):
    for standing in standings_data:
        assert standing['Player'] is not None and standing['Player'] != ''


def test_standings_have_rank(standings_data):
    for standing in standings_data:
        assert standing['Rank'] > 0


def test_standings_have_points(standings_data):
    for standing in standings_data[:32]:
        assert standing['Points'] > 0


def test_standings_have_omwp(standings_data):
    for standing in standings_data[:32]:
        assert standing['OMWP'] > 0


def test_decks_have_gwp(standings_data):
    for standing in standings_data[:32]:
        assert standing['GWP'] > 0


def test_decks_have_ogwp(standings_data):
    for standing in standings_data[:32]:
        assert standing['OGWP'] > 0


def test_standing_data_is_correct(standings_data):
    test_standing = standings_data[0]
    assert test_standing == Standing(1, "Fink64", 21, 0.659, 0.75, 0.584, 7, 1, 0)




#######################################################################################################
# BracketWithExtraMatchesLoaderTests
# Données de test
@pytest.fixture
def test_data():
    source = Mock()
    source.get_tournament_details = Mock(return_value={
        "Rounds": [
            Round("Quarterfinals", [
                RoundItem("zuri1988", "Fink64", "2-1-0"),
                RoundItem("kvza", "Harry13", "2-0-0"),
                RoundItem("ModiSapiras", "Daking3603", "2-0-0"),
                RoundItem("Cinciu", "ScouterTF2", "2-0-0")
            ]),
            Round("Semifinals", [
                RoundItem("kvza", "zuri1988", "2-1-0"),
                RoundItem("ModiSapiras", "Cinciu", "2-0-0")
            ]),
            Round("Finals", [
                RoundItem("ModiSapiras", "kvza", "2-0-0")
            ])
        ]
    })
    return source.get_tournament_details(Mock())

# Tests
def test_bracket_item_count_is_correct(test_data):
    assert len(test_data[0].matches) == 4  # Quarterfinals
    assert len(test_data[1].matches) == 2  # Semifinals
    assert len(test_data[2].matches) == 1  # Finals

def test_bracket_items_have_winning_player(test_data):
    for round_data in test_data:
        for match in round_data.matches:
            assert match.player1 is not None
            assert match.player1 != ""

def test_bracket_items_have_losing_player(test_data):
    for round_data in test_data:
        for match in round_data.matches:
            assert match.player2 is not None
            assert match.player2 != ""

def test_bracket_items_have_result(test_data):
    for round_data in test_data:
        for match in round_data.matches:
            assert match.result is not None
            assert match.result != ""

def test_bracket_rounds_should_be_in_correct_order(test_data):
    expected_round_names = ["Quarterfinals", "Semifinals", "Finals"]
    actual_round_names = [round_data.round_name for round_data in test_data]
    assert actual_round_names == expected_round_names

def test_should_contain_extra_brackets(test_data):
    assert len(test_data) == 3  # Expected 3 rounds: Quarterfinals, Semifinals, Finals

def test_bracket_items_data_is_correct(test_data):
    expected = [
        Round("Quarterfinals", [
            RoundItem("zuri1988", "Fink64", "2-1-0"),
            RoundItem("kvza", "Harry13", "2-0-0"),
            RoundItem("ModiSapiras", "Daking3603", "2-0-0"),
            RoundItem("Cinciu", "ScouterTF2", "2-0-0")
        ]),
        Round("Semifinals", [
            RoundItem("kvza", "zuri1988", "2-1-0"),
            RoundItem("ModiSapiras", "Cinciu", "2-0-0")
        ]),
        Round("Finals", [
            RoundItem("ModiSapiras", "kvza", "2-0-0")
        ])
    ]

    for round_data, expected_round in zip(test_data, expected):
        assert round_data.round_name == expected_round.round_name
        for match, expected_match in zip(round_data.matches, expected_round.matches):
            assert match.player1 == expected_match.player1
            assert match.player2 == expected_match.player2
            assert match.result == expected_match.result


#######################################################################################################
# BracketWithoutExtraMatchesLoaderTests
# Fixture pour fournir les données de test
@pytest.fixture
def test_data():
    source = Mock()
    source.get_tournament_details = Mock(return_value={
        "Rounds": [
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
    })
    return source.get_tournament_details(Mock())

# Tests
def test_bracket_item_count_is_correct(test_data):
    assert len(test_data[0].matches) == 4  # Quarterfinals
    assert len(test_data[1].matches) == 2  # Semifinals
    assert len(test_data[2].matches) == 1  # Finals

def test_bracket_items_have_winning_player(test_data):
    for round_data in test_data:
        for match in round_data.matches:
            assert match.player1 is not None
            assert match.player1 != ""

def test_bracket_items_have_losing_player(test_data):
    for round_data in test_data:
        for match in round_data.matches:
            assert match.player2 is not None
            assert match.player2 != ""

def test_bracket_items_have_result(test_data):
    for round_data in test_data:
        for match in round_data.matches:
            assert match.result is not None
            assert match.result != ""

def test_bracket_rounds_should_be_in_correct_order(test_data):
    expected_round_names = ["Quarterfinals", "Semifinals", "Finals"]
    actual_round_names = [round_data.round_name for round_data in test_data]
    assert actual_round_names == expected_round_names

def test_should_not_contain_extra_brackets(test_data):
    assert len(test_data) == 3  # Expected 3 rounds: Quarterfinals, Semifinals, Finals

def test_bracket_items_data_is_correct(test_data):
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

    for round_data, expected_round in zip(test_data, expected):
        assert round_data.round_name == expected_round.round_name
        for match, expected_match in zip(round_data.matches, expected_round.matches):
            assert match.player1 == expected_match.player1
            assert match.player2 == expected_match.player2
            assert match.result == expected_match.result


#######################################################################################################
# DeckLoaderTests

# Fixture pour fournir les données de test
@pytest.fixture
def test_data():
    # Mock de la source des données
    decks = [
        # Inclure ici des exemples simulés de decks (résumés pour simplifier)
        Deck("Player1", None, None, "Result1", [DeckItem("CardA", 4)], [DeckItem("CardB", 2)]),
        # Ajoutez d'autres decks si nécessaire, y compris le deck utilisé pour le test DeckDataIsCorrect
        Deck(
            "Fink64",
            "https://www.manatraders.com/webshop/personal/874208",
            None,
            "8th Place",
            [
                DeckItem("Mausoleum Wanderer", 4),
                DeckItem("Spectral Sailor", 4),
                DeckItem("Rattlechains", 4),
                DeckItem("Selfless Spirit", 1),
                DeckItem("Shacklegeist", 4),
                DeckItem("Supreme Phantom", 4),
                DeckItem("Empyrean Eagle", 3),
                DeckItem("Katilda, Dawnhart Martyr", 1),
                DeckItem("Skyclave Apparition", 4),
                DeckItem("Spell Queller", 4),
                DeckItem("Collected Company", 4),
                DeckItem("Botanical Sanctum", 4),
                DeckItem("Branchloft Pathway", 4),
                DeckItem("Breeding Pool", 1),
                DeckItem("Eiganjo, Seat of the Empire", 1),
                DeckItem("Hallowed Fountain", 4),
                DeckItem("Hengegate Pathway", 4),
                DeckItem("Island", 1),
                DeckItem("Mana Confluence", 1),
                DeckItem("Otawara, Soaring City", 1),
                DeckItem("Secluded Courtyard", 1),
                DeckItem("Temple Garden", 1),
            ],
            [
                DeckItem("Portable Hole", 2),
                DeckItem("Shapers' Sanctuary", 2),
                DeckItem("Lofty Denial", 4),
                DeckItem("Rest in Peace", 2),
                DeckItem("Selfless Spirit", 1),
                DeckItem("Extraction Specialist", 4),
            ],
        ),
    ]
    return decks

# Tests
def test_deck_count_is_correct(test_data):
    assert len(test_data) == 194  # Attendu : 194 decks

def test_decks_dont_have_date(test_data):
    for deck in test_data:
        assert deck.date is None

def test_decks_have_players(test_data):
    for deck in test_data:
        assert deck.player is not None
        assert deck.player != ""

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
    test_deck = test_data[1]  # L'exemple de test
    assert test_deck.player == "Fink64"
    assert test_deck.anchor_uri == "https://www.manatraders.com/webshop/personal/874208"
    assert test_deck.date is None
    assert test_deck.result == "8th Place"
    assert len(test_deck.mainboard) == 22
    assert len(test_deck.sideboard) == 6
    assert any(item.card_name == "Mausoleum Wanderer" and item.count == 4 for item in test_deck.mainboard)

def test_should_apply_top8_ordering_to_decks(test_data):
    top8 = ["ModiSapiras", "kvza", "Cinciu", "zuri1988", "Daking3603", "Harry13", "ScouterTF2", "Fink64"]
    actual_top8 = [deck.player for deck in test_data[:8]]
    assert actual_top8 == top8

#######################################################################################################
# RoundsLoaderTests

@pytest.fixture
def test_data():
    source = ManaTradersSource()
    tournament = Tournament(uri="https://www.manatraders.com/tournaments/30/", date=datetime(2022, 8, 31))
    return source.GetTournamentDetails(tournament).Rounds


def test_round_count_is_correct(test_data):
    assert len(test_data) == 15


def test_rounds_have_number(test_data):
    for round in test_data:
        assert round['RoundName'] is not None and round['RoundName'] != ''


def test_rounds_have_matches(test_data):
    for round in test_data:
        assert len(round['Matches']) > 0


def test_round_data_is_correct(test_data):
    test_round = test_data[0]
    assert test_round['RoundName'] == "Round 1"
    assert test_round['Matches'][0] == RoundItem("SuperCow12653", "Demrakh", "2-0-0")


#######################################################################################################
# RoundsWithNoBracketLoaderTests

@pytest.fixture
def test_data_no_bracket():
    source = ManaTradersSource()
    tournament = Tournament(uri="https://www.manatraders.com/tournaments/34/", date=datetime(2022, 12, 31))
    return source.GetTournamentDetails(tournament).Rounds


def test_round_count_is_correct_no_bracket(test_data_no_bracket):
    assert len(test_data_no_bracket) == 9


def test_rounds_have_number_no_bracket(test_data_no_bracket):
    for round in test_data_no_bracket:
        assert round['RoundName'] is not None and round['RoundName'] != ''


def test_rounds_have_matches_no_bracket(test_data_no_bracket):
    for round in test_data_no_bracket:
        assert len(round['Matches']) > 0


def test_round_data_is_correct_no_bracket(test_data_no_bracket):
    test_round = test_data_no_bracket[0]
    assert test_round['RoundName'] == "Round 1"
    assert test_round['Matches'][0] == RoundItem("sneakymisato", "Mogged", "0-2-0")



#######################################################################################################
# TournamentLoaderTests


@pytest.fixture
def tournament_data():
    source = ManaTradersSource()
    return source.GetTournaments(datetime(2001, 1, 1))


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