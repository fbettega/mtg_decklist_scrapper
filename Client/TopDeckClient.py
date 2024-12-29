




class TopDeckConstants:
    class Format(Enum):
        EDH = "EDH"
        PauperEDH = "Pauper EDH"
        Standard = "Standard"
        Pioneer = "Pioneer"
        Modern = "Modern"
        Legacy = "Legacy"
        Pauper = "Pauper"
        Vintage = "Vintage"
        Premodern = "Premodern"
        Limited = "Limited"
        Timeless = "Timeless"
        Historic = "Historic"
        Explorer = "Explorer"
        Oathbreaker = "Oathbreaker"

    class Game(Enum):
        MagicTheGathering = "Magic: The Gathering"

    class Misc:
        NO_DECKLISTS_TEXT = "No Decklist Available"
        DRAW_TEXT = "Draw"
        TOURNAMENT_PAGE = "https://topdeck.gg/event/{tournamentId}"

    class PlayerColumn(Enum):
        Name = "name"
        Decklist = "decklist"
        DeckSnapshot = "deckSnapshot"
        Commanders = "commanders"
        Wins = "wins"
        WinsSwiss = "winsSwiss"
        WinsBracket = "winsBracket"
        WinRate = "winRate"
        WinRateSwiss = "winRateSwiss"
        WinRateBracket = "winRateBracket"
        Draws = "draws"
        Losses = "losses"
        LossesSwiss = "lossesSwiss"
        LossesBracket = "lossesBracket"
        ID = "id"

    class Routes:
        ROOT_URL = "https://topdeck.gg/api"
        TOURNAMENT_ROUTE = f"{ROOT_URL}/v2/tournaments"
        STANDINGS_ROUTE = f"{ROOT_URL}/v2/tournaments/{{TID}}/standings"
        ROUNDS_ROUTE = f"{ROOT_URL}/v2/tournaments/{{TID}}/rounds"
        TOURNAMENT_INFO_ROUTE = f"{ROOT_URL}/v2/tournaments/{{TID}}/info"
        FULL_TOURNAMENT_ROUTE = f"{ROOT_URL}/v2/tournaments/{{TID}}"

    class Settings:
        API_KEY_ENV_VAR = "TOPDECK_API_KEY"
        @staticmethod
        def get_api_key():
            return os.getenv(TopDeckConstants.Settings.API_KEY_ENV_VAR, "Default_API_Key")
        
