import logging
from lib.base_handler import BaseHandler
from lib.models import Player, Game
import elo


class MainPage(BaseHandler):
  def DoGet(self):
    self.render_to_response("admin_index.html")

class UpdateSchema(BaseHandler):
  def DoGet(self):
    # By loading and storing each player, we're updating the player for any
    # schema changes.
    # This will not work once we have more than 1000 records, but it's fine for now.
    for player in Player.all():
      player.put()

    for game in Game.all():
      game.put()

    self.render_to_response("update_schema.html")

class CalculateRankings(BaseHandler):
  def DoGet(self):

    logging.info('Calculating rankings')
    # Reset ranks
    for player in Player.all():
      player.rank = elo.INITIAL_RANK
      player.put()

    # Calculate ranks for games in ascending order, since the order matters for ELO
    for game in Game.all_completed_asc():
      logging.info('Updating rankings based on game completed at %s:  %s' % (game.completed_date, game))
      elo.update_ranks(game)
      game.player_1.put()
      game.player_2.put()

    self.render_to_response("calculate_rankings.html")

