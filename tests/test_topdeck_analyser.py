import pytest
from datetime import datetime, timezone
import json
from Client.TopDeckClient import *
import requests
###########################################################################################################################################
# DeckLoaderTest
@pytest.fixture(scope="module")
def get_test_data(self):
    test_data = TournamentList.get_tournament_details(
        Tournament(
            name="CCS Summer Showdown Modern 2k",
            date= datetime.fromtimestamp(1717934400, tz=timezone.utc),
            uri="https://topdeck.gg/event/SrJAEZ8vbglVge29fG7l"
    )
    )
    return test_data

def test_decks_should_load(self, get_test_data):
    assert get_test_data.decks is not None and len(get_test_data.decks) > 0

def test_decks_should_have_cards(self, get_test_data):
    for deck in get_test_data.decks:
        assert deck.mainboard is not None and len(deck.mainboard) > 0

def test_decks_should_have_players(self, get_test_data):
    for deck in get_test_data.decks:
        assert deck.player is not None and len(deck.player) > 0

def test_decks_should_have_results(self, get_test_data):
    for deck in get_test_data.decks:
        assert deck.result is not None and len(deck.result) > 0

def test_decks_should_have_anchor_uris(self, get_test_data):
    for deck in get_test_data.decks:
        assert deck.anchor_uri is not None

###########################################################################################################################################
# RoundsLoaderTest

@pytest.fixture(scope="module")
def get_test_data(self):
    test_data = TopdeckSource().get_tournament_details(Tournament(
        name="CCS Summer Showdown Modern 2k",
        date=datetime.utcfromtimestamp(1717934400),
        uri="https://topdeck.gg/event/SrJAEZ8vbglVge29fG7l"
    ))
    return test_data

def test_rounds_should_load(self, get_test_data):
    assert get_test_data.rounds is not None and len(get_test_data.rounds) > 0

def test_rounds_should_have_names(self, get_test_data):
    for round in get_test_data.rounds:
        assert round.round_name is not None and len(round.round_name) > 0

def test_rounds_should_have_matches(self, get_test_data):
    for round in get_test_data.rounds:
        assert round.matches is not None and len(round.matches) > 0

def test_matches_should_have_players(self, get_test_data):
    for match in get_test_data.rounds:
        for m in match.matches:
            assert m.player1 is not None and len(m.player1) > 0

def test_matches_should_have_results(self, get_test_data):
    for match in get_test_data.rounds:
        for m in match.matches:
            assert m.result is not None and len(m.result) > 0

###########################################################################################################################################
# StandingsLoaderTest

@pytest.fixture(scope="module")
def get_test_data(self):
    test_data = TopdeckSource().get_tournament_details(Tournament(
        name="CCS Summer Showdown Modern 2k",
        date=datetime.utcfromtimestamp(1717934400),
        uri="https://topdeck.gg/event/SrJAEZ8vbglVge29fG7l"
    ))
    return test_data

def test_should_load_standings(self, get_test_data):
    assert get_test_data.standings is not None and len(get_test_data.standings) > 0

def test_standings_should_have_names(self, get_test_data):
    for standing in get_test_data.standings:
        assert standing.player is not None and len(standing.player) > 0

def test_standings_should_have_ranks(self, get_test_data):
    for standing in get_test_data.standings:
        assert standing.rank > 0

def test_standings_should_have_wins(self, get_test_data):
    wins = [s for s in get_test_data.standings if s.wins > 0]
    assert len(wins) > 0

def test_standings_should_have_losses(self, get_test_data):
    losses = [s for s in get_test_data.standings if s.losses > 0]
    assert len(losses) > 0

def test_standings_should_have_draws(self, get_test_data):
    draws = [s for s in get_test_data.standings if s.draws > 0]
    assert len(draws) > 0

def test_standings_should_have_game_win_percent(self, get_test_data):
    gwp = [s for s in get_test_data.standings if s.gwp > 0]
    assert len(gwp) > 0

def test_standings_should_have_opponent_match_win_percent(self, get_test_data):
    omwp = [s for s in get_test_data.standings if s.omwp > 0]
    assert len(omwp) > 0

def test_standings_should_have_opponent_game_win_percent(self, get_test_data):
    ogwp = [s for s in get_test_data.standings if s.ogwp > 0]
    assert len(ogwp) > 0

###########################################################################################################################################
# TournamentLoaderTests
@pytest.fixture(scope="module")
def get_test_data(self):
    test_data = TopdeckSource().get_tournaments(
        datetime(2024, 4, 1, 0, 0, 0),
        datetime(2024, 4, 30, 0, 0, 0)
    )
    return test_data

def test_tournament_count_is_correct(self, get_test_data):
    assert len(get_test_data) == 8

def test_tournament_data_is_correct(self, get_test_data):
    expected_tournament = Tournament(
        name="Emjati - Eternal - Modern",
        date=datetime(2024, 4, 5, 6, 0, 0),
        uri="https://topdeck.gg/event/iCMd298218qbEqeGt5d7"
    )
    assert get_test_data[0] == expected_tournament
