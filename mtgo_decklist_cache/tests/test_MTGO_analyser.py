import pytest
# from  MTGmelee.MtgMeleeClient import *
import pdb
import importlib
from datetime import datetime, timezone
from models.base_model import *
import MTGO.MTGOclient as MTGO
import time
# import MTGmelee.MtgMeleeClient
# # Recharger le module
# importlib.reload(MTGmelee.MtgMeleeClient)
# # Réimporter tous les objets exportés par le module
# from MTGmelee.MtgMeleeClient import *

# pytest .\tests\MtgMelee.py 
# pytest .\tests\

#################################################################################
# TournamentLoaderBasicTests
# The test functions using pytest
@pytest.fixture(scope="module")
def test_data():
    # Setup code to fetch the test data
    test_data = MTGO.TournamentList.DL_tournaments(
    start_date = datetime(2020, 6, 1, 0, 0, 0),
    end_date = datetime(2020, 6, 2, 0, 0, 0)
    )
    return test_data

def test_tournament_count_is_correct(test_data):
    assert len(test_data) == 15


def test_tournament_data_is_correct(test_data):
    expected_tournaments = [
        Tournament(datetime(2020, 6, 2, 0, 0, 0), "Limited Super Qualifier", "https://www.mtgo.com/decklist/limited-super-qualifier-2020-06-0212162899", "limited-super-qualifier-2020-06-0212162899.json"),
        Tournament(datetime(2020, 6, 2, 0, 0, 0), "Limited Super Qualifier", "https://www.mtgo.com/decklist/limited-super-qualifier-2020-06-0212162898", "limited-super-qualifier-2020-06-0212162898.json"),
        Tournament(datetime(2020, 6, 2, 0, 0, 0), "Modern League", "https://www.mtgo.com/decklist/modern-league-2020-06-025082", "modern-league-2020-06-025082.json"),
        Tournament(datetime(2020, 6, 2, 0, 0, 0), "Pauper League", "https://www.mtgo.com/decklist/pauper-league-2020-06-025090", "pauper-league-2020-06-025090.json"),
        Tournament(datetime(2020, 6, 2, 0, 0, 0), "Pioneer League", "https://www.mtgo.com/decklist/pioneer-league-2020-06-025098", "pioneer-league-2020-06-025098.json"),
        Tournament(datetime(2020, 6, 2, 0, 0, 0), "Standard League", "https://www.mtgo.com/decklist/standard-league-2020-06-025106", "standard-league-2020-06-025106.json"),
        Tournament(datetime(2020, 6, 2, 0, 0, 0), "Vintage League", "https://www.mtgo.com/decklist/vintage-league-2020-06-025182", "vintage-league-2020-06-025182.json"),
        Tournament(datetime(2020, 6, 2, 0, 0, 0), "Legacy League", "https://www.mtgo.com/decklist/legacy-league-2020-06-025190", "legacy-league-2020-06-025190.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Modern Super Qualifier", "https://www.mtgo.com/decklist/modern-super-qualifier-2020-06-0112162897", "modern-super-qualifier-2020-06-0112162897.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Modern League", "https://www.mtgo.com/decklist/modern-league-2020-06-015082", "modern-league-2020-06-015082.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Pauper League", "https://www.mtgo.com/decklist/pauper-league-2020-06-015090", "pauper-league-2020-06-015090.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Pioneer League", "https://www.mtgo.com/decklist/pioneer-league-2020-06-015098", "pioneer-league-2020-06-015098.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Standard League", "https://www.mtgo.com/decklist/standard-league-2020-06-015106", "standard-league-2020-06-015106.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Vintage League", "https://www.mtgo.com/decklist/vintage-league-2020-06-015182", "vintage-league-2020-06-015182.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Legacy League", "https://www.mtgo.com/decklist/legacy-league-2020-06-015190", "legacy-league-2020-06-015190.json")
    ]
    
    for expected, actual in zip(expected_tournaments, test_data):   
        assert expected.date.date() == actual.date
        assert expected.name == actual.name
        assert expected.uri == actual.uri
        assert expected.json_file == actual.json_file

#################################################################################
# TournamentLoaderCrossMonthTests
@pytest.fixture(scope="module")
def test_data_CrossMonth():
    # Setup code to fetch the test data
    test_data_CrossMonth = MTGO.TournamentList.DL_tournaments(
    start_date = datetime(2020, 5, 31, 0, 0, 0),
    end_date = datetime(2020, 6, 1, 0, 0, 0)
    )
    return test_data_CrossMonth

def test_tournament_count_is_correct(test_data_CrossMonth):
    assert len(test_data_CrossMonth) == 19


def test_tournament_data_is_correct(test_data_CrossMonth):
    expected_data = [
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Modern Super Qualifier", "https://www.mtgo.com/decklist/modern-super-qualifier-2020-06-0112162897", "modern-super-qualifier-2020-06-0112162897.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Modern League", "https://www.mtgo.com/decklist/modern-league-2020-06-015082", "modern-league-2020-06-015082.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Pauper League", "https://www.mtgo.com/decklist/pauper-league-2020-06-015090", "pauper-league-2020-06-015090.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Pioneer League", "https://www.mtgo.com/decklist/pioneer-league-2020-06-015098", "pioneer-league-2020-06-015098.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Standard League", "https://www.mtgo.com/decklist/standard-league-2020-06-015106", "standard-league-2020-06-015106.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Vintage League", "https://www.mtgo.com/decklist/vintage-league-2020-06-015182", "vintage-league-2020-06-015182.json"),
        Tournament(datetime(2020, 6, 1, 0, 0, 0), "Legacy League", "https://www.mtgo.com/decklist/legacy-league-2020-06-015190", "legacy-league-2020-06-015190.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Standard Challenge", "https://www.mtgo.com/decklist/standard-challenge-2020-05-3112162941", "standard-challenge-2020-05-3112162941.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Pauper Challenge", "https://www.mtgo.com/decklist/pauper-challenge-2020-05-3112162939", "pauper-challenge-2020-05-3112162939.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Legacy Challenge", "https://www.mtgo.com/decklist/legacy-challenge-2020-05-3112162938", "legacy-challenge-2020-05-3112162938.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Modern Challenge", "https://www.mtgo.com/decklist/modern-challenge-2020-05-3112162936", "modern-challenge-2020-05-3112162936.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Limited Super Qualifier", "https://www.mtgo.com/decklist/limited-super-qualifier-2020-05-3112162896", "limited-super-qualifier-2020-05-3112162896.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Vintage Challenge", "https://www.mtgo.com/decklist/vintage-challenge-2020-05-3112162935", "vintage-challenge-2020-05-3112162935.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Modern League", "https://www.mtgo.com/decklist/modern-league-2020-05-315082", "modern-league-2020-05-315082.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Pauper League", "https://www.mtgo.com/decklist/pauper-league-2020-05-315090", "pauper-league-2020-05-315090.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Pioneer League", "https://www.mtgo.com/decklist/pioneer-league-2020-05-315098", "pioneer-league-2020-05-315098.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Standard League", "https://www.mtgo.com/decklist/standard-league-2020-05-315106", "standard-league-2020-05-315106.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Vintage League", "https://www.mtgo.com/decklist/vintage-league-2020-05-315182", "vintage-league-2020-05-315182.json"),
        Tournament(datetime(2020, 5, 31, 0, 0, 0), "Legacy League", "https://www.mtgo.com/decklist/legacy-league-2020-05-315190", "legacy-league-2020-05-315190.json"),
    ]
    for expected, actual in zip(expected_data, test_data_CrossMonth): 
        assert expected.date.date() == actual.date
        assert expected.name == actual.name
        assert expected.uri == actual.uri
        assert expected.json_file == actual.json_file
        # print(expected.date.date() == actual.date)
        # print( expected.name == actual.name)
        # print( expected.uri == actual.uri)
        # print( expected.json_file == actual.json_file  )

#################################################################################
# TournamentLoaderCrossYearTests
@pytest.fixture(scope="module")
def test_data_CrossYearTests():
    # Setup code to fetch the test data
    test_data_CrossYearTests = MTGO.TournamentList.DL_tournaments(
    start_date = datetime(2021, 12, 31, 0, 0, 0),
    end_date = datetime(2022, 1, 1, 0, 0, 0)
    )
    return test_data_CrossYearTests

def test_tournament_count_is_correct(test_data_CrossYearTests):
    assert len(test_data_CrossYearTests) == 18


def test_tournament_data_is_correct(test_data_CrossYearTests):
    expected_data = [
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Pioneer Challenge", "https://www.mtgo.com/decklist/pioneer-challenge-2022-01-0112367816", "pioneer-challenge-2022-01-0112367816.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Vintage Challenge", "https://www.mtgo.com/decklist/vintage-challenge-2022-01-0112367814", "vintage-challenge-2022-01-0112367814.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Modern Challenge", "https://www.mtgo.com/decklist/modern-challenge-2022-01-0112367813", "modern-challenge-2022-01-0112367813.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Convention Championship", "https://www.mtgo.com/decklist/convention-championship-2022-01-0112367722", "convention-championship-2022-01-0112367722.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Standard Challenge", "https://www.mtgo.com/decklist/standard-challenge-2022-01-0112367812", "standard-challenge-2022-01-0112367812.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Pauper Challenge", "https://www.mtgo.com/decklist/pauper-challenge-2022-01-0112367810", "pauper-challenge-2022-01-0112367810.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Legacy League", "https://www.mtgo.com/decklist/legacy-league-2022-01-016237", "legacy-league-2022-01-016237.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Modern League", "https://www.mtgo.com/decklist/modern-league-2022-01-016245", "modern-league-2022-01-016245.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Pauper League", "https://www.mtgo.com/decklist/pauper-league-2022-01-016253", "pauper-league-2022-01-016253.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Pioneer League", "https://www.mtgo.com/decklist/pioneer-league-2022-01-016261", "pioneer-league-2022-01-016261.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Standard League", "https://www.mtgo.com/decklist/standard-league-2022-01-016269", "standard-league-2022-01-016269.json"),
        Tournament(datetime(2022, 1, 1, 0, 0, 0), "Vintage League", "https://www.mtgo.com/decklist/vintage-league-2022-01-016277", "vintage-league-2022-01-016277.json"),
        Tournament(datetime(2021, 12, 31, 0, 0, 0), "Legacy League", "https://www.mtgo.com/decklist/legacy-league-2021-12-316237", "legacy-league-2021-12-316237.json"),
        Tournament(datetime(2021, 12, 31, 0, 0, 0), "Modern League", "https://www.mtgo.com/decklist/modern-league-2021-12-316245", "modern-league-2021-12-316245.json"),
        Tournament(datetime(2021, 12, 31, 0, 0, 0), "Pauper League", "https://www.mtgo.com/decklist/pauper-league-2021-12-316253", "pauper-league-2021-12-316253.json"),
        Tournament(datetime(2021, 12, 31, 0, 0, 0), "Pioneer League", "https://www.mtgo.com/decklist/pioneer-league-2021-12-316261", "pioneer-league-2021-12-316261.json"),
        Tournament(datetime(2021, 12, 31, 0, 0, 0), "Standard League", "https://www.mtgo.com/decklist/standard-league-2021-12-316269", "standard-league-2021-12-316269.json"),
        Tournament(datetime(2021, 12, 31, 0, 0, 0), "Vintage League", "https://www.mtgo.com/decklist/vintage-league-2021-12-316277", "vintage-league-2021-12-316277.json"),
    ]
    for expected, actual in zip(expected_data, test_data_CrossYearTests): 
        assert expected.date.date() == actual.date
        assert expected.name == actual.name
        assert expected.uri == actual.uri
        assert expected.json_file == actual.json_file
        # print(expected.date.date() == actual.date)
        # print( expected.name == actual.name)
        # print( expected.uri == actual.uri)
        # print( expected.json_file == actual.json_file  )