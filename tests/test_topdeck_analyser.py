import pytest
from datetime import datetime, timezone
import json
from Client.TopDeckClient import *
import requests
# pytest .\tests\test_topdeck_analyser.py
###########################################################################################################################################
# DeckLoaderTest
@pytest.fixture(scope="module")
def get_test_data():
    get_test_data = TournamentList().get_tournament_details(
        Tournament(
            name="CCS Summer Showdown Modern 2k",
            date= datetime.fromtimestamp(1717934400, tz=timezone.utc),
            uri="https://topdeck.gg/event/SrJAEZ8vbglVge29fG7l"
    )
    )
    return get_test_data
# @pytest.fixture(scope="module")
# def get_test_data_moxfield_deck():
#     get_test_data_moxfield_deck = TournamentList().get_tournament_details(
#             Tournament(
#                 name="The Island Vacation",
#                 date= datetime(2024, 12, 7, 0, 0, 0, tzinfo=timezone.utc),
#                 uri="https://topdeck.gg/event/z97Wwe0sadHGT2ymc5Ss"
#         )
#         )
#     return get_test_data_moxfield_deck


def test_decks_should_load( get_test_data):
    assert get_test_data.decks is not None and len(get_test_data.decks) > 0

def test_decks_should_have_cards( get_test_data):
    for deck in get_test_data.decks:
        assert deck.mainboard is not None and len(deck.mainboard) > 0

def test_decks_should_have_players( get_test_data):
    for deck in get_test_data.decks:
        assert deck.player is not None and len(deck.player) > 0

def test_decks_should_have_results( get_test_data):
    for deck in get_test_data.decks:
        assert deck.result is not None and len(deck.result) > 0

def test_decks_should_have_anchor_uris( get_test_data):
    for deck in get_test_data.decks:
        assert deck.anchor_uri is not None






###########################################################################################################################################
# RoundsLoaderTest
def test_rounds_should_load( get_test_data):
    assert get_test_data.rounds is not None and len(get_test_data.rounds) > 0

def test_rounds_should_have_names( get_test_data):
    for round in get_test_data.rounds:
        assert round.round_name is not None and len(round.round_name) > 0

def test_rounds_should_have_matches( get_test_data):
    for round in get_test_data.rounds:
        assert round.matches is not None and len(round.matches) > 0

def test_matches_should_have_players( get_test_data):
    for match in get_test_data.rounds:
        for m in match.matches:
            assert m.player1 is not None and len(m.player1) > 0

def test_matches_should_have_results( get_test_data):
    for match in get_test_data.rounds:
        for m in match.matches:
            assert m.result is not None and len(m.result) > 0

###########################################################################################################################################
# StandingsLoaderTest
def test_should_load_standings( get_test_data):
    assert get_test_data.standings is not None and len(get_test_data.standings) > 0

def test_standings_should_have_names( get_test_data):
    for standing in get_test_data.standings:
        assert standing.player is not None and len(standing.player) > 0

def test_standings_should_have_points( get_test_data):
    for standing in get_test_data.standings:
        assert standing.points is not None 

def test_standings_should_have_ranks( get_test_data):
    for standing in get_test_data.standings:
        assert standing.rank > 0

def test_standings_should_have_wins( get_test_data):
    wins = [s for s in get_test_data.standings if s.wins > 0]
    assert len(wins) > 0

def test_standings_should_have_losses( get_test_data):
    losses = [s for s in get_test_data.standings if s.losses > 0]
    assert len(losses) > 0

def test_standings_should_have_draws( get_test_data):
    draws = [s for s in get_test_data.standings if s.draws > 0]
    assert len(draws) > 0

def test_standings_should_have_game_win_percent( get_test_data):
    gwp = [s for s in get_test_data.standings if s.gwp > 0]
    assert len(gwp) > 0

def test_standings_should_have_opponent_match_win_percent( get_test_data):
    omwp = [s for s in get_test_data.standings if s.omwp > 0]
    assert len(omwp) > 0

def test_standings_should_have_opponent_game_win_percent( get_test_data):
    ogwp = [s for s in get_test_data.standings if s.ogwp > 0]
    assert len(ogwp) > 0

###########################################################################################################################################
# TournamentLoaderTests
@pytest.fixture(scope="module")
def TournamentLoader(self):
    TournamentLoader = TournamentList.DL_tournaments(
        datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2024, 4, 30, 0, 0, 0, tzinfo=timezone.utc)
    )
    return TournamentLoader

def test_tournament_count_is_correct( TournamentLoader):
    assert len(TournamentLoader) == 10

def test_tournament_data_is_correct( TournamentLoader):
    expected_tournament = Tournament(
        name="Emjati - Eternal - Modern",
        date=datetime(2024, 4, 5, 6, 0, 0, tzinfo=timezone.utc),
        uri="https://topdeck.gg/event/iCMd298218qbEqeGt5d7"
    )
    assert TournamentLoader[0].name == expected_tournament.name
    assert TournamentLoader[0].date == expected_tournament.date
    assert TournamentLoader[0].uri == expected_tournament.uri
