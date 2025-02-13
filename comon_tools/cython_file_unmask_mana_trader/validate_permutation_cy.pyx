import numpy as np
cimport numpy as cnp
from libc.stdlib cimport malloc, free
import re

# Définition de la fonction en Cython
cpdef tuple validate_permutation(
    list match_combination,
    dict history,
    dict player_indices,
    cnp.ndarray[int, ndim=1] standings_wins,
    cnp.ndarray[int, ndim=1] standings_losses,
    cnp.ndarray[double, ndim=1] standings_gwp,
    set full_list_of_masked_player,
    dict Result_history=None,
    int iteration=0
):
    
    cdef cnp.ndarray[int, ndim=1] Match_wins = history["Match_wins"]
    cdef cnp.ndarray[int, ndim=1] Match_losses = history["Match_losses"]
    cdef cnp.ndarray[int, ndim=1] Game_wins = history["Game_wins"]
    cdef cnp.ndarray[int, ndim=1] Game_losses = history["Game_losses"]
    cdef cnp.ndarray[int, ndim=1] Game_draws = history["Game_draws"]
    cdef dict matchups = history["matchups"]
    
    cdef set modified_players = set()
    cdef dict Match_result = Result_history if Result_history is not None else {}
    
    cdef int player, opponent, player_idx
    cdef double gwp_calculated, total_games
    cdef list results_match, players
    
    for round_item in match_combination:
        results_match = list(map(int, round_item.result.split('-')))
        players = [
            (round_item.player1, round_item.player2, *round_item.scores[0], *results_match),
            (round_item.player2, round_item.player1, *round_item.scores[1], results_match[1], results_match[0], results_match[2])
        ]
        
        for player, opponent, win, loss, M_win, M_loss, M_draw in players:
            if player is None or player not in full_list_of_masked_player:
                continue
            modified_players.add(player)
            
            is_valid_opp = is_unmasked_valid(opponent)
            if opponent in matchups[player] and is_valid_opp:
                return False, (player, opponent)
            else:
                matchups[player].append(opponent)
                if is_valid_opp and not (player in full_list_of_masked_player and opponent in full_list_of_masked_player):
                    matchups[opponent].append(player)
            
            player_idx = player_indices[player]
            Match_wins[player_idx] += win
            Match_losses[player_idx] += loss
            Game_wins[player_idx] += M_win
            Game_losses[player_idx] += M_loss
            Game_draws[player_idx] += M_draw
            
            if Result_history is not None:
                Match_result[player] = Match_result.get(player, ()) + (M_win > M_loss,)
            
            if Match_wins[player_idx] > standings_wins[player_idx] or Match_losses[player_idx] > standings_losses[player_idx]:
                return False, (player, opponent)
    
    for player in modified_players:
        player_idx = player_indices[player]
        if Match_wins[player_idx] == standings_wins[player_idx] and Match_losses[player_idx] == standings_losses[player_idx]:
            total_games = Game_wins[player_idx] + Game_losses[player_idx] + Game_draws[player_idx]
            if total_games > 0:
                gwp_calculated = (Game_wins[player_idx] + (Game_draws[player_idx] / 3.0)) / total_games
                if not np.isclose(gwp_calculated, standings_gwp[player_idx], atol=0.001):
                    return False, (player, "")
    
    return True, "ok"

cpdef bint is_unmasked_valid(str player):
    """Vérifie si le joueur n'est ni None ni masqué."""
    if player is None:
        return False
    return not re.fullmatch(r'.\*{10}.\d*', player)
