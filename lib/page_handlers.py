"""
All of the RequestHandlers live here. These are akin to traditional Controllers
or Django "views".
"""
import logging
from cgi import escape
from datetime import datetime

from google.appengine.ext.db import GeoPt
from elo import update_ranks

from models import Player, Game, League
from base_handler import BaseHandler
from stats import stats
from oponger_email import send_email

class MainPage(BaseHandler):
  def DoGet(self):

    additional_values = {
        'active_leagues': League.all_active().fetch(5,0) #just the first 5 leagues
    }
    
    self.template_values.update(additional_values)
    self.render_to_response("index.html")

class LeaguePage(BaseHandler):
  def DoGet(self):

    additional_values = {
      'active_games': Game.gql("WHERE player_2 != NULL AND completed_date = NULL"),
      'available_games': Game.gql("WHERE player_2 = NULL"),
      'players' : self.get_players().fetch(7,0), # just the top players
      'completed_games' : Game.all_completed().fetch(5,0) # just a few recently completed games
    }

    self.template_values.update(additional_values)
    self.render_to_response("league.html")

class NewLeague(BaseHandler):
  def DoPost(self):
    league_name = escape(self.request.get('name'))
    if len(league_name) > 15:
      raise Exception("A league name can be no more thn 15 characters long.")
    league_rules = escape(self.request.get('rules'))
    if len(league_rules) > 700:
      raise Exception("A league rulebook can be no more than 700 characters long,\
                       ideally with link to another page on the interwebz.")
    league_logo = escape(self.request.get('logo'))
    if len(league_logo) > 150:
      raise Exception("A league logo is a uri to an icon, no more than 150 characters long.")
    league = League(name = league_name, rules = league_rules, logo = league_logo)
    league.put()
    logging.info("Creating new league %s" % (league))
    self.redirect('/')
    #self.redirect_to_redirect_path_or_home()

class LeagueDetails(BaseHandler):
  def DoGet(self, league_key_name):
    league_to_show = League.get_by_key_name(league_key_name)

    logging.info('Getting league %s' % league_to_show)
    if not league_to_show:
      self.error(404)
      self.response.out.write("""<strong>No League with key %s.
      Try looking through the <a href="/">list of leagues</a>.</strong>""" % league_name)

    additional_values = {
      'league_to_show'  : league_to_show,
      'players' : league_to_show.players(),
    }

    self.template_values.update(additional_values)
    self.render_to_response("league.html")

class Games(BaseHandler):
  def DoGet(self):

    additional_values = {
      'active_games': Game.all_active(),
      'available_games': Game.all_available(),
      'completed_games': Game.all_completed(),
    }

    self.template_values.update(additional_values)
    self.render_to_response("games.html")

class PlayerDetails(BaseHandler):
  def DoGet(self, player_key_name):
    player_to_show = Player.get_by_key_name(player_key_name)

    logging.info('Getting player %s' % player_to_show)
    if not self.player:
      self.error(404)
      self.response.out.write("""<strong>No player with key %s.
      Try looking through the <a href="/players">list of players</a>.</strong>""" % player_key_name)

    additional_values = {
      'player_to_show'  : player_to_show,
      'available_games' : player_to_show.available_games(),
      'completed_games' : player_to_show.completed_games(),
      'active_games'    : player_to_show.active_games(),
      'stats'           : stats(player_to_show)
    }

    self.template_values.update(additional_values)
    self.render_to_response("player.html")

class Profile(BaseHandler):
  def DoGet(self):
    self.render_to_response("profile.html")

class Players(BaseHandler):
  def DoGet(self):

    additional_values = {
      'players'   : self.get_players()
    }

    self.template_values.update(additional_values)
    self.render_to_response("players.html")

class Rulez(BaseHandler):
  def DoGet(self):
    self.render_to_response("rulez.html")

class UpdateProfile(BaseHandler):
  def DoPost(self):
    logging.info("Updating player info")
    pseudonym = escape(self.request.get('pseudonym'))
    if pseudonym != self.player.pseudonym and len(pseudonym) > 15:
      raise Exception("If you update a pseudonym, it must be no more thn 15 characters long.")

    self.player.pseudonym = pseudonym
    (lat, lon) = self.request.get('location').split(',')
    self.player.location = GeoPt(lat, lon)
    self.player.put()
    self.redirect('/profile')

class NewGame(BaseHandler):
  def DoPost(self):
    game = Game(player_1 = self.player)
    game.put()
    logging.info("Creating new game %s" % (game))
    self.redirect_to_redirect_path_or_home()

class JoinGame(BaseHandler):
  def DoPost(self):
    game = Game.get_by_id(long(self.request.get('game_id')))

    if game.player_1 == self.player:
      raise Exception("You can't join your own game, duderino!")
    if game.player_2:
      raise Exception("Oops, looks like someone already joined this game, duderino!")

    game.player_2 = self.player
    game.put()
    logging.info("Player %s joined game %s" % (self.player, game))
    send_email(game.player_1.user, '%s has joined your game' % self.player.pseudonym,
               'To view your games: http://oponger.opower.com/')
    self.redirect_to_redirect_path_or_home()

class CancelGame(BaseHandler):
  def DoPost(self):
    game = Game.get_by_id(long(self.request.get('game_id')))

    if not (game.player_1.key() == self.player.key() or game.player_2.key() == self.player.key()):
      raise Exception("You can't delete a game you don't own, duderino!")

    if game.completed_date != None:
      raise Exception("You can't delete a game that's already been completed, duderino!")

    game.delete()
    logging.info("Player %s deleted game %s" % (self.player, game))
    self.redirect_to_redirect_path_or_home()

class CompleteGame(BaseHandler):
  def DoPost(self):
    game = Game.get_by_id(long(self.request.get('game_id')))

    if not (game.player_1.key() == self.player.key() or
        game.player_2.key() == self.player.key()):
      raise Exception("You can't complete a game you don't own, duderino!")

    if game.completed_date != None:
      raise Exception("You can't complete a game that's already been completed, duderino!")

    player_1_won = bool(self.request.get('player_1_won'))
    player_2_won = bool(self.request.get('player_2_won'))
    if not player_1_won ^ player_2_won:
      raise "One player, and only one player, can win a game."

    game.completed_date = datetime.now()
    if player_1_won:
      game.winner = game.player_1
    else:
      game.winner = game.player_2

    update_ranks(game)

    game.player_1.put()
    game.player_2.put()
    game.put()

    logging.info("Player %s completed game %s" % (self.player, game))
    self.redirect_to_redirect_path_or_home()

