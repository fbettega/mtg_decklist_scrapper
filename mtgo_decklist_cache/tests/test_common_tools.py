import pytest
# from datetime import datetime
# import pdb
# import importlib
from models.base_model import *
from comon_tools.tools import *

CardNameNormalizer.initialize()
##############################################################################
# CardNormalizerTests
def test_should_remove_leading_spaces():
    assert CardNameNormalizer.normalize(" Arclight Phoenix") == "Arclight Phoenix"
    assert CardNameNormalizer.normalize("  Arclight Phoenix") == "Arclight Phoenix"

def test_should_remove_trailing_spaces():
    assert CardNameNormalizer.normalize("Arclight Phoenix ") == "Arclight Phoenix"
    assert CardNameNormalizer.normalize("Arclight Phoenix  ") == "Arclight Phoenix"

# a corriger
def test_should_normalize_split_cards():
    assert CardNameNormalizer.normalize("Fire") == "Fire // Ice"
    assert CardNameNormalizer.normalize("Fire/Ice") == "Fire // Ice"
    assert CardNameNormalizer.normalize("Fire / Ice") == "Fire // Ice"
    assert CardNameNormalizer.normalize("Fire//Ice") == "Fire // Ice"
    assert CardNameNormalizer.normalize("Fire // Ice") == "Fire // Ice"
    assert CardNameNormalizer.normalize("Fire///Ice") == "Fire // Ice"
    assert CardNameNormalizer.normalize("Fire /// Ice") == "Fire // Ice"

def test_should_normalize_flip_cards():
    assert CardNameNormalizer.normalize("Akki Lavarunner") == "Akki Lavarunner"
    assert CardNameNormalizer.normalize("Akki Lavarunner/Tok-Tok, Volcano Born") == "Akki Lavarunner"
    assert CardNameNormalizer.normalize("Akki Lavarunner / Tok-Tok, Volcano Born") == "Akki Lavarunner"
    assert CardNameNormalizer.normalize("Akki Lavarunner//Tok-Tok, Volcano Born") == "Akki Lavarunner"
    assert CardNameNormalizer.normalize("Akki Lavarunner // Tok-Tok, Volcano Born") == "Akki Lavarunner"
    assert CardNameNormalizer.normalize("Akki Lavarunner///Tok-Tok, Volcano Born") == "Akki Lavarunner"
    assert CardNameNormalizer.normalize("Akki Lavarunner /// Tok-Tok, Volcano Born") == "Akki Lavarunner"

def test_should_normalize_adventure_cards():
    assert CardNameNormalizer.normalize("Brazen Borrower") == "Brazen Borrower"
    assert CardNameNormalizer.normalize("Brazen Borrower/Petty Theft") == "Brazen Borrower"
    assert CardNameNormalizer.normalize("Brazen Borrower / Petty Theft") == "Brazen Borrower"
    assert CardNameNormalizer.normalize("Brazen Borrower//Petty Theft") == "Brazen Borrower"
    assert CardNameNormalizer.normalize("Brazen Borrower // Petty Theft") == "Brazen Borrower"
    assert CardNameNormalizer.normalize("Brazen Borrower///Petty Theft") == "Brazen Borrower"
    assert CardNameNormalizer.normalize("Brazen Borrower /// Petty Theft") == "Brazen Borrower"

def test_should_normalize_dual_face_cards():
    assert CardNameNormalizer.normalize("Delver of Secrets") == "Delver of Secrets"
    assert CardNameNormalizer.normalize("Delver of Secrets/Insectile Aberration ") == "Delver of Secrets"
    assert CardNameNormalizer.normalize("Delver of Secrets / Insectile Aberration ") == "Delver of Secrets"
    assert CardNameNormalizer.normalize("Delver of Secrets//Insectile Aberration ") == "Delver of Secrets"
    assert CardNameNormalizer.normalize("Delver of Secrets // Insectile Aberration ") == "Delver of Secrets"
    assert CardNameNormalizer.normalize("Delver of Secrets///Insectile Aberration ") == "Delver of Secrets"
    assert CardNameNormalizer.normalize("Delver of Secrets /// Insectile Aberration ") == "Delver of Secrets"

def test_should_fix_universes_within_cards():
    assert CardNameNormalizer.normalize("Rick, Steadfast Leader") == "Greymond, Avacyn's Stalwart"

def test_should_fix_universes_within_dfc_cards():
    assert CardNameNormalizer.normalize("Hawkins National Laboratory") == "Havengul Laboratory"
    assert CardNameNormalizer.normalize("Hawkins National Laboratory // The Upside Down") == "Havengul Laboratory"

def test_should_convert_alchemy_buffs_and_nerfs_to_regular_card():
    assert CardNameNormalizer.normalize("A-Dragon's Rage Channeler") == "Dragon's Rage Channeler"

def test_should_convert_alchemy_adventure_cards_to_normal_card():
    assert CardNameNormalizer.normalize("A-Blessed Hippogriff // Tyr's Blessing") == "Blessed Hippogriff"

############################################################################################################################
# DeckNormalizerTests
def test_should_reorder_cards():
    input_deck = Deck(
        date = None,
        player = "test player",
        result = [],
        anchor_uri = "test_url",
        mainboard=[
            DeckItem(card_name="Mishra's Bauble", count=3),
            DeckItem(card_name="Dragon's Rage Channeler", count=4),
            DeckItem(card_name="Murktide Regent", count=4),
            DeckItem(card_name="Delver of Secrets", count=1),
            DeckItem(card_name="Brazen Borrower", count=1),
            DeckItem(card_name="Counterbalance", count=2),
            DeckItem(card_name="Force of Negation", count=1),
            DeckItem(card_name="Daze", count=3),
        ],
        sideboard=[
            DeckItem(card_name="Tropical Island", count=1),
            DeckItem(card_name="End the Festivities", count=1),
            DeckItem(card_name="Meltdown", count=2),
            DeckItem(card_name="Red Elemental Blast", count=1),
            DeckItem(card_name="Pyroblast", count=2),
        ]
    )

    expected_deck = Deck(
        date = None,
        player = "test player",
        result = [],
        anchor_uri = "test_url",
        mainboard=[
            DeckItem(card_name="Brazen Borrower", count=1),
            DeckItem(card_name="Counterbalance", count=2),
            DeckItem(card_name="Daze", count=3),
            DeckItem(card_name="Delver of Secrets", count=1),
            DeckItem(card_name="Dragon's Rage Channeler", count=4),
            DeckItem(card_name="Force of Negation", count=1),
            DeckItem(card_name="Mishra's Bauble", count=3),
            DeckItem(card_name="Murktide Regent", count=4),
        ],
        sideboard=[
            DeckItem(card_name="End the Festivities", count=1),
            DeckItem(card_name="Meltdown", count=2),
            DeckItem(card_name="Pyroblast", count=2),
            DeckItem(card_name="Red Elemental Blast", count=1),
            DeckItem(card_name="Tropical Island", count=1),
        ]
    )
    normalized_deck = DeckNormalizer.normalize(input_deck)
    assert normalized_deck == expected_deck


def test_should_combine_duplicates():
    input_deck = Deck(
        date = None,
        player = "test player",
        result = [],
        anchor_uri = "test_url",
        mainboard=[
            DeckItem(card_name="Mishra's Bauble", count=3),
            DeckItem(card_name="Mishra's Bauble", count=1),
            DeckItem(card_name="Dragon's Rage Channeler", count=4),
            DeckItem(card_name="Murktide Regent", count=4),
        ],
        sideboard=[
            DeckItem(card_name="Tropical Island", count=1),
            DeckItem(card_name="End the Festivities", count=1),
            DeckItem(card_name="End the Festivities", count=2),
            DeckItem(card_name="Meltdown", count=2),
        ]
    )

    expected_deck = Deck(
        date = None,
        player = "test player",
        result = [],
        anchor_uri = "test_url",
        mainboard=[
            DeckItem(card_name="Dragon's Rage Channeler", count=4),
            DeckItem(card_name="Mishra's Bauble", count=4),
            DeckItem(card_name="Murktide Regent", count=4),
        ],
        sideboard=[
            DeckItem(card_name="End the Festivities", count=3),
            DeckItem(card_name="Meltdown", count=2),
            DeckItem(card_name="Tropical Island", count=1),
        ]
    )

    normalized_deck = DeckNormalizer.normalize(input_deck)
    assert normalized_deck == expected_deck

    ######################################################################################
    # OrderNormalizerTests
def test_should_reorder_using_bracket():
    decks = [
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Fifth", result="1st Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Winner", result="2nd Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Sixth", result="3rd Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Seventh", result="4th Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Third", result="5th Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Eighth", result="6th Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Fourth", result="7th Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Second", result="8th Place"),
    ]
        
    standings = [
        Standing(player="Fifth", points=10),
        Standing(player="Winner", points=9),
        Standing(player="Sixth", points=8),
        Standing(player="Seventh", points=7),
        Standing(player="Third", points=6),
        Standing(player="Eighth", points=5),
        Standing(player="Fourth", points=4),
        Standing(player="Second", points=3),
    ]

    bracket = [
        Round(
            round_name="Quarterfinals",
            matches=[
                RoundItem(player1="Winner", player2="Fifth", result="2-0-0"),
                RoundItem(player1="Second", player2="Sixth", result="2-0-0"),
                RoundItem(player1="Third", player2="Seventh", result="2-0-0"),
                RoundItem(player1="Fourth", player2="Eighth", result="2-0-0"),
            ],
        ),
        Round(
            round_name="Semifinals",
            matches=[
                RoundItem(player1="Winner", player2="Third", result="2-0-0"),
                RoundItem(player1="Second", player2="Fourth", result="2-0-0"),
            ],
        ),
        Round(
            round_name="Finals",
            matches=[
                RoundItem(player1="Winner", player2="Second", result="2-0-0")
            ],
        ),
    ]
    expected_decks = [
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Winner", result="1st Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Second", result="2nd Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Third", result="3rd Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Fourth", result="4th Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Fifth", result="5th Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Sixth", result="6th Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Seventh", result="7th Place"),
        Deck(date = None,anchor_uri = "test_url",mainboard=[],sideboard=[],player="Eighth", result="8th Place"),
    ]

    normalized_decks = OrderNormalizer.reorder_decks(decks, standings, bracket, update_result=True)
    assert normalized_decks == expected_decks