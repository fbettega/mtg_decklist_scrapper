
    def calculate_stats_for_matches(self,matches: List[RoundItem], standings: List[Standing]):
        # Initialiser les stats
        stats = {
            "Rank": None,
            "Points": 0,
            "Wins": 0,
            "Losses": 0,
            "Draws": 0,
            "OMP": 0.0,
            "GWP": 0.0,
            "OGP": 0.0,
        }
        # Variables auxiliaires pour GWP et OGP
        total_games_played = 0
        total_games_won = 0
        opponents = set()

        # Parcourir les matchs
        player_names = {standing.player for standing in standings}

        # Parcourir les matchs
        for match in matches:
            p1_wins, p2_wins, draws = map(int, match.result.split('-'))

            # Identifier le joueur et son adversaire
            if match.player1 in player_names:
                player = match.player1
                opponent = match.player2
                player_wins, player_losses = p1_wins, p2_wins
            elif match.player2 in player_names:
                player = match.player2
                opponent = match.player1
                player_wins, player_losses = p2_wins, p1_wins
            else:
                continue  # Ignorer les matchs dont les joueurs ne sont pas dans standings

            # Calculer les victoires, défaites et égalités
            stats["Wins"] += player_wins
            stats["Losses"] += player_losses
            stats["Draws"] += draws

            # Ajouter aux points (3 pour chaque victoire, 1 pour chaque égalité)
            stats["Points"] += 3 * player_wins + draws

            # Ajouter aux jeux joués et gagnés
            total_games_played += player_wins + player_losses + draws
            total_games_won += player_wins

            # Ajouter l'adversaire à la liste
            opponents.add(opponent)

        # Calculer GWP (Game-Win Percentage)
        if total_games_played > 0:
            stats["GWP"] = total_games_won / total_games_played

        # Calculer OMP (Opponents’ Match-Win Percentage)
        opponent_match_points = 0
        opponent_total_matches = 0
        for opponent in opponents:
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_match_points += opponent_standing.points
                opponent_total_matches += 3 * len(matches)  # Nombre de rounds (approximé ici)

        if opponent_total_matches > 0:
            stats["OMP"] = opponent_match_points / opponent_total_matches

        # Calculer OGP (Opponents’ Game-Win Percentage)
        opponent_game_wins = 0
        opponent_game_total = 0
        for opponent in opponents:
            opponent_standing = next((s for s in standings if s.player == opponent), None)
            if opponent_standing:
                opponent_game_wins += opponent_standing.wins
                opponent_game_total += opponent_standing.wins + opponent_standing.losses + opponent_standing.draws

        if opponent_game_total > 0:
            stats["OGP"] = opponent_game_wins / opponent_game_total

        # Calculer le rang du joueur en fonction des points
        standings_with_updated_points = sorted(
            standings + [Standing(player=player, points=stats["Points"])],
            key=lambda s: s.points,
            reverse=True,
        )
        stats["Rank"] = next(
            (i + 1 for i, s in enumerate(standings_with_updated_points) if s.player == player),
            None,
        )
        return stats
    

    def calculate_player_stats(self, rounds: List[Round], standings: List[Standing]) -> Tuple[Dict[str, List[Dict]], List[str], List[str]]: 
            # Étape 1 : Mapper les noms masqués aux joueurs réels
            masked_to_actual = defaultdict(list)
            for standing in standings:
                if standing.player:
                    masked_name = f"{standing.player[0]}{'*' * 10}{standing.player[-1]}"
                    masked_to_actual[masked_name].append(standing.player)
            # Étape 3 : Identifier les joueurs dupliqués (nom masqué avec plusieurs joueurs réels)
            duplicated_masked_names = {masked for masked, actuals in masked_to_actual.items() if len(actuals) > 1}
            
            # Étape 4 : Collecter les matchs impliquant des noms masqués dupliqués
            masked_matches = defaultdict(list)  # masked_name -> list of (role, round_name, match)
            for masked in duplicated_masked_names:
                for rnd in rounds:
                    for match in rnd.matches:
                        if match.player1 == masked:
                            masked_matches[masked].append(('player1', rnd.round_name, match))
                        if match.player2 == masked:
                            masked_matches[masked].append(('player2', rnd.round_name, match))

            # Étape 5 : Générer toutes les combinaisons possibles d'assignations pour chaque joueur dupliqué
            assignments_per_masked = {}
            for masked, matches_info in masked_matches.items():
                actual_players = masked_to_actual[masked]
                per_round_assignments = []  # Contient les combinaisons possibles par round
                # Organiser les matchs par round
                matches_by_round = defaultdict(list)
                for role, round_name, match in matches_info:
                    matches_by_round[round_name].append((role, match))

                # Générer les permutations pour chaque round
                for round_name, matches in matches_by_round.items():
                    round_combinations = []
                    for match_info in matches:
                        role, match = match_info

                        # Créer toutes les permutations en remplaçant le joueur masqué
                        for player in actual_players:
                            # Copier le match pour éviter d'écraser les données originales
                            new_match = RoundItem(
                                player1=match.player1 if role != 'player1' else player,
                                player2=match.player2 if role != 'player2' else player,
                                result=match.result,
                            )
                            round_combinations.append(new_match)
                    # Ajouter les combinaisons de ce round aux résultats globaux
                    per_round_assignments.append(round_combinations)
                # Générer toutes les combinaisons possibles entre les rounds
                assignments_per_masked[masked] = list(product(*per_round_assignments))

            recalculated_stats = {}
            for masked_name, match_combinations in assignments_per_masked.items():
                player_stats_for_combinations = []

                for combination in match_combinations:
                    # Chaque combination est une liste de RoundItem correspondant aux 9 rounds.
                    all_matches = list(combination)  # Extraire directement les RoundItem de la combinaison.

                    # Recalculer les statistiques pour ces matchs
                    stats = self.calculate_stats_for_matches(all_matches, standings)

                    # Ajouter les statistiques recalculées aux résultats
                    player_stats_for_combinations.append(stats)

                # Stocker les statistiques recalculées pour ce joueur masqué
                recalculated_stats[masked_name] = player_stats_for_combinations
