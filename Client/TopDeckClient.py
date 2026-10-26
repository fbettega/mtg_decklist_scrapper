import os
import json
from datetime import datetime, timedelta, timezone
import requests
import time
from threading import Lock
from models.base_model import *
from models.Topdeck_model import *
from comon_tools.tools import *


class MissingApiKeyException(Exception):
    def __init__(self):
        super().__init__(f"Could not load API key from {TopDeckConstants.Settings.API_KEY_FILE_PATH}")


class TopdeckClient:
    """
    Client API v2 TopDeck.gg.

    Rate limits (doc) : ~100 req/min pour la plupart des endpoints, plus bas pour
    POST /v2/tournaments (bulk). Observé : 5 appels bulk puis 429 (Retry-After 17 s).
    On espace donc les appels en amont, et sur 429 on obéit au Retry-After.
    """
    MIN_INTERVAL_BULK = 13.0     # POST /v2/tournaments : ~4-5 appels/min
    MIN_INTERVAL_DEFAULT = 0.7   # autres endpoints : < 100 appels/min
    MAX_RETRIES_429 = 8

    def __init__(self):
        self._api_key = TopDeckConstants.Settings.get_api_key()
        if not self._api_key:
            raise MissingApiKeyException()
        self._lock = Lock()
        self._last_call = {"bulk": 0.0, "default": 0.0}
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": self._api_key,
            "Content-Type": "application/json; charset=utf-8",
        })

    # ------------------------------------------------------------------ HTTP
    def _throttle(self, bucket):
        interval = self.MIN_INTERVAL_BULK if bucket == "bulk" else self.MIN_INTERVAL_DEFAULT
        with self._lock:
            wait = self._last_call[bucket] + interval - time.time()
            if wait > 0:
                time.sleep(wait)
            self._last_call[bucket] = time.time()

    def _request(self, method, url, bucket="default", **kwargs):
        for attempt in range(1, self.MAX_RETRIES_429 + 1):
            self._throttle(bucket)
            response = self._session.request(method, url, timeout=60, **kwargs)
            if response.status_code != 429:
                return response
            wait = response.headers.get("Retry-After")
            if wait is None:
                try:
                    wait = response.json().get("retryAfterSeconds")
                except ValueError:
                    wait = None
            wait = int(wait or 20) + 1
            print(f"\n[Topdeck] 429 rate limit ({bucket}), pause {wait}s ({attempt}/{self.MAX_RETRIES_429})")
            time.sleep(wait)
        return response

    @staticmethod
    def _response_to_json(response):
        if response.status_code != 200:
            raise ValueError(f"Topdeck {response.request.method} {response.url} -> {response.status_code}: {response.text[:500]}")
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise ValueError(f"Topdeck: JSON invalide ({e}): {response.text[:500]}")

    # ------------------------------------------------------------- endpoints
    def search_tournaments(self, body: dict) -> list:
        """POST /v2/tournaments (bulk, rate limit bas). Renvoie le JSON brut."""
        r = self._request("POST", TopDeckConstants.Routes.TOURNAMENT_ROUTE, bucket="bulk", json=body)
        data = self._response_to_json(r)
        if not isinstance(data, list):
            raise ValueError(f"Topdeck: liste attendue, reçu {type(data).__name__}: {str(data)[:300]}")
        return data

    def get_full_tournament_raw(self, tournament_id: str) -> dict:
        """GET /v2/tournaments/{TID} : data + standings (decklist/deckObj si fini) + rounds."""
        r = self._request("GET", TopDeckConstants.Routes.FULL_TOURNAMENT_ROUTE.replace("{TID}", tournament_id))
        return self._response_to_json(r)

    def get_tournament_info_raw(self, tournament_id: str) -> dict:
        r = self._request("GET", TopDeckConstants.Routes.TOURNAMENT_INFO_ROUTE.replace("{TID}", tournament_id))
        return self._response_to_json(r)

    # Compat avec l'ancien code / les tests ----------------------------------
    def get_tournament_list(self, request):
        return [self._normalize(TopdeckListTournament, t) for t in self.search_tournaments(request.to_dict())]

    def get_tournament(self, tournament_id):
        return self._normalize(TopdeckTournament, self.get_full_tournament_raw(tournament_id))

    def get_tournament_info(self, tournament_id):
        return self._normalize(TopdeckTournamentInfo, self.get_tournament_info_raw(tournament_id))

    def get_standings(self, tournament_id):
        r = self._request("GET", TopDeckConstants.Routes.STANDINGS_ROUTE.replace("{TID}", tournament_id))
        return [self._normalize(TopdeckStanding, s) for s in self._response_to_json(r)]

    def get_rounds(self, tournament_id):
        r = self._request("GET", TopDeckConstants.Routes.ROUNDS_ROUTE.replace("{TID}", tournament_id))
        return [self._normalize(TopdeckRound, x) for x in self._response_to_json(r)]

    @staticmethod
    def _normalize(cls, json_data):
        result = cls.from_json(json_data)
        result.normalize()
        return result


###########################################################################################################################################
# Parsing des decks (deckObj / decklist texte)

_MAIN_SECTIONS = {"mainboard", "main", "maindeck", "deck"}
_SIDE_SECTIONS = {"sideboard", "side", "commanders", "commander", "companion", "partner"}


def _section_items(section):
    """
    Convertit une section de deckObj en [(nom, quantité)].
    Accepte : {"Card": 4}, {"Card": {"count": 4, ...}}, [{"name": "Card", "count": 4}, ...]
    """
    items = []
    if isinstance(section, dict):
        for name, value in section.items():
            if isinstance(value, (int, float)):
                items.append((name, int(value)))
            elif isinstance(value, dict):
                count = value.get("count", value.get("quantity", value.get("qty", 1)))
                items.append((value.get("name", name), int(count)))
    elif isinstance(section, list):
        for value in section:
            if isinstance(value, dict) and value.get("name"):
                items.append((value["name"], int(value.get("count", value.get("quantity", 1)))))
    return items


def parse_deck_obj(deck_obj):
    """Renvoie (mainboard, sideboard) en listes [(nom, qté)] ou (None, None) si non reconnu."""
    if not isinstance(deck_obj, dict):
        return None, None
    main, side = [], []
    for key, section in deck_obj.items():
        k = key.lower().replace(" ", "")
        if k in _MAIN_SECTIONS:
            main += _section_items(section)
        elif k in _SIDE_SECTIONS:
            side += _section_items(section)
    return (main or None), (side or None)


def parse_decklist_text(text):
    """
    Repli sur le texte : sections '~~Mainboard~~' / '~~Sideboard~~' / '~~Commanders~~'
    ou lignes 'Sideboard' simples ; lignes '4 Card Name'.
    """
    if not text or text.startswith("http"):
        return None, None
    main, side = [], []
    current = main
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        header = line.strip("~").strip().lower().rstrip(":")
        if header in _MAIN_SECTIONS:
            current = main
            continue
        if header in _SIDE_SECTIONS:
            current = side
            continue
        count, _, name = line.partition(" ")
        count = count.rstrip("x")
        if count.isdigit() and name:
            current.append((name.strip(), int(count)))
    return (main or None), (side or None)


###########################################################################################################################################
# TournamentList

class TournamentList:
    VALID_FORMATS = [
        TopDeckConstants.Format.Standard.value,
        TopDeckConstants.Format.Pioneer.value,
        TopDeckConstants.Format.Modern.value,
        TopDeckConstants.Format.Legacy.value,
        TopDeckConstants.Format.Vintage.value,
        TopDeckConstants.Format.Pauper.value,
        TopDeckConstants.Format.DuelCommander.value,
        TopDeckConstants.Format.Premodern.value,
    ]
    _client = None  # partagé : un seul throttle pour tout le run

    def __init__(self):
        self.provider = "topdeck.gg"
        if TournamentList._client is None:
            TournamentList._client = TopdeckClient()
        self.client = TournamentList._client

    # ------------------------------------------------------------------
    @staticmethod
    def _records_from_rounds(rounds):
        """
        Victoires/défaites/nuls par id joueur, recalculés depuis les rondes.
        Les byes NE sont PAS comptés : c'est ce que renvoyait l'ancienne colonne 'wins'
        (vérifié sur les fichiers du cache : 1089/1091 standings identiques).
        """
        rec = {}

        def add(pid, field):
            if pid is None:
                return
            rec.setdefault(pid, {"wins": 0, "losses": 0, "draws": 0})[field] += 1

        for rnd in rounds or []:
            for table in rnd.get("tables", []):
                players = table.get("players", [])
                ids = [p.get("id") or p.get("name") for p in players]
                status = table.get("status")
                winner_id = table.get("winner_id")
                winner = table.get("winner")
                if status == "Bye" or table.get("table") == "Byes" or len(players) == 1:
                    continue
                elif winner_id == "Draw" or winner == "Draw":
                    for pid in ids:
                        add(pid, "draws")
                elif winner_id or winner:
                    for p, pid in zip(players, ids):
                        won = (winner_id and p.get("id") == winner_id) or (not winner_id and p.get("name") == winner)
                        add(pid, "wins" if won else "losses")
        return rec

    @staticmethod
    def _rounds_from_raw(rounds):
        result = []
        for rnd in rounds or []:
            items = []
            for table in rnd.get("tables", []):
                players = table.get("players", [])
                names = [p.get("name") for p in players]
                winner_id = table.get("winner_id")
                winner = table.get("winner")
                if table.get("status") == "Bye" or table.get("table") == "Byes" or len(players) == 1:
                    # comportement historique conservé : bye noté "0-0-1", player2 vide
                    for n in names:
                        items.append(RoundItem(player1=n, player2="", result="0-0-1"))
                elif winner_id == "Draw" or winner == "Draw":
                    items.append(RoundItem(player1=names[0], player2=names[1], result="0-0-1"))
                elif winner_id or winner:
                    if (winner_id and players[1].get("id") == winner_id) or (not winner_id and names[1] == winner):
                        items.append(RoundItem(player1=names[1], player2=names[0], result="1-0-0"))
                    else:
                        items.append(RoundItem(player1=names[0], player2=names[1], result="1-0-0"))
                # sinon : match non terminé, ignoré
            result.append(Round(round_name=str(rnd.get("round")), matches=items))
        return result

    # ------------------------------------------------------------------
    def get_tournament_details(self, tournament):
        tournament_id = tournament.uri.split("/")[-1]
        raw = self.client.get_full_tournament_raw(tournament_id)   # 1 seul appel, endpoint 100/min
        raw_standings = raw.get("standings", []) or []
        raw_rounds = raw.get("rounds", []) or []

        records = self._records_from_rounds(raw_rounds)
        rounds = self._rounds_from_raw(raw_rounds)

        standings, decks = [], []
        CardNameNormalizer.initialize()
        for s in raw_standings:
            pid = s.get("id") or s.get("name")
            r = records.get(pid, {"wins": 0, "losses": 0, "draws": 0})
            rank = s.get("standing")
            standings.append(Standing(
                player=s.get("name"),
                rank=rank,
                points=s.get("points"),
                wins=r["wins"], losses=r["losses"], draws=r["draws"],
                gwp=s.get("gameWinRate"),
                omwp=s.get("opponentWinRate", s.get("opponentSuccessRate")),
                ogwp=s.get("opponentGameWinRate"),
            ))

            main, side = parse_deck_obj(s.get("deckObj"))
            if not main:
                main, side = parse_decklist_text(s.get("decklist"))
            if not main:
                continue
            decklist = s.get("decklist")
            anchor = decklist if isinstance(decklist, str) and decklist.startswith("http") else tournament.uri
            decks.append(Deck(
                player=s.get("name"),
                date=tournament.date,
                result=f"{rank}th Place" if rank and rank > 3 else f"{rank}st Place",
                anchor_uri=anchor,
                mainboard=[DeckItem(count=c, card_name=CardNameNormalizer.normalize(n)) for n, c in main],
                sideboard=[DeckItem(count=c, card_name=CardNameNormalizer.normalize(n)) for n, c in (side or [])],
            ))
        return CacheItem(tournament=tournament, standings=standings, rounds=rounds, decks=decks)

    # ------------------------------------------------------------------
    @staticmethod
    def DL_tournaments(start_date: datetime, end_date: datetime = None) -> List[Tournament]:
        if start_date < datetime(2020, 1, 1, tzinfo=timezone.utc):
            return []
        if end_date is None:
            end_date = datetime.now(timezone.utc) + timedelta(days=1)
        client = TournamentList()._client
        result = []
        print(f"\r[Topdeck] Downloading tournaments from {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}", end='')

        for fmt in TournamentList.VALID_FORMATS:
            tournaments = client.search_tournaments({
                "game": TopDeckConstants.Game.MagicTheGathering,
                "format": fmt,
                "start": int(start_date.timestamp()),
                "end": int(end_date.timestamp()),
                "columns": ["id"],   # payload léger : les decks sont pris dans get_tournament_details
            })
            print(f"\n[Topdeck] {fmt}: {len(tournaments)} tournois", end='')
            for t in tournaments:
                date = datetime.fromtimestamp(t["startDate"], tz=timezone.utc)
                result.append(Tournament(
                    name=t.get("tournamentName"),
                    date=date,
                    formats=fmt,
                    uri=TopDeckConstants.Misc.TOURNAMENT_PAGE.replace("{tournamentId}", t["TID"]),
                    json_file=FilenameGenerator.generate_file_name(
                        t["TID"], t.get("tournamentName"), date, fmt, list(TournamentList.VALID_FORMATS), -1
                    ),
                ))
        print("\n[Topdeck] Download finished")
        return result