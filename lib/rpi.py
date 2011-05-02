"""
A ranking system based on the Ratings Percent Index, which is used in NCAA Basketball rankings.

The equation is:

RPI = (WP * 0.25) + (OWP * 0.50) + (OOWP * 0.25)

Where,
  WP = Win Percentage
  OWP = Opponents' Win Percentage
  OOWP = Opponents' Opponents' Win Percentage

See http://en.wikipedia.org/wiki/Ratings_Percentage_Index
"""
import logging

from models import Player
from stats import stats

class RPI_Calculator:

  def __init__(self):
    players = Player.all()
    self.player_opponents = {}
    logging.info("Initializing RPI Calculator.")
    logging.info("Finding opponents for all players.")
    for player in players:
      self.player_opponents[hash(player)] = self._get_opponents_for_player(player)

  def _get_opponents_for_player(self, player):
    """
    Retrieves the set of opponents for a given player.
    """
    opponents = set()
    for game in player.completed_games():
      opponents.add(game.player_1)
      opponents.add(game.player_2)

    # If we added the player itself, we must remove it
    if player in opponents:
      opponents.remove(player)

    return opponents

  def _get_opponents_for_players(self, players):
    """
    Retrieves the set of opponents for a set of players.
    """
    opponents = set()
    for player in players:
      opponents = set.union(opponents, self.player_opponents[hash(player)])

    return opponents

  def _average_percent_win(self, players):
    """
    Calculates the average win percentage for a set of players.
    """
    if not len(players):
      return 0

    sum = 0
    for player in players:
      sum += stats(player)['percent_win']

    return float(sum)/len(players)

  def calculate_rankings(self):
    """
    Calculates rankings based on the RPI method. The implementation
    is naive, and would not work for a large number of players.
    """
    logging.info("Calculating RPI rankings.")
    for player in Player.all():
      wp = stats(player)['percent_win']

      opponents = self.player_opponents[hash(player)]
      owp = self._average_percent_win(opponents)

      opponents_opponents = self._get_opponents_for_players(opponents)
      oowp = self._average_percent_win(opponents_opponents)

      rpi_rank = (wp * 0.25) + (owp * 0.5) + (oowp * 0.25)
      logging.info('For player %s. RPI = %s (%s * 0.25 + %s * 0.5 + %s * 0.25)'
                   % (player.pseudonym,rpi_rank, wp, owp, oowp))

      player.rpi_rank = rpi_rank
      player.put()

