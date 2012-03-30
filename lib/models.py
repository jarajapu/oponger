"""
All of our data models go here.

For details on how Google App Engine handles these, see:
http://code.google.com/appengine/docs/python/datastore/modelclass.html
"""
from google.appengine.ext import db
from locations import DC
from elo import INITIAL_RANK

MAX_RESULTS=1000


class League(db.Model):
  name = db.StringProperty()
  rules = db.TextProperty()
  logo = db.StringProperty()

  def players(self):
    """Returns players for this league"""
    players = self.player_set.order("rpi_rank").fetch(MAX_RESULTS, 0)
    #return sorted(players, key = lambda player: player.rpi_rank)
    return players

  @staticmethod
  def all_active():
    return League.gql("WHERE rules !=  NULL")

class Player(db.Model):
  date = db.DateTimeProperty(auto_now_add=True)
  user = db.UserProperty(required=True)
  pseudonym = db.StringProperty()
  location = db.GeoPtProperty(default=DC['geoPt'])
  rank = db.FloatProperty(default=INITIAL_RANK)
  rpi_rank = db.FloatProperty()
  league = db.ReferenceProperty(League)

  def __str__(self):
    return "[Psuedonym: %s, Nickname: %s]" % (self.pseudonym, self.user.nickname())

  def __eq__(self, value):
    if self.__class__ == value.__class__:
      return self.key() == value.key()
    else:
      return False

  def __hash__(self):
    return hash(str(self.key()))

  def games(self):
    """Returns this player's games, sorted by creation date."""
    games = self.game_set_1.order("created_date").fetch(MAX_RESULTS, 0)
    games.extend(self.game_set_2.order('created_date').fetch(MAX_RESULTS, 0))
    return sorted(games, key = lambda game: game.created_date, reverse=True)

  def active_games(self):
    return [game for game in self.games() if game.is_active()]

  def available_games(self):
    return [game for game in self.games() if game.is_available()]

  def completed_games(self):
    completed_games = [game for game in self.games() if game.is_completed()]
    return sorted(completed_games, key = lambda game: game.completed_date, reverse=True)

  @staticmethod
  def all_by_elo_rank():
    return Player.gql("ORDER BY rank DESC")

  @staticmethod
  def all_by_rpi_rank():
    return Player.gql("ORDER BY rpi_rank DESC")

  @staticmethod
  def all_by_rank(type):
    if type == 'elo':
      return Player.all_by_elo_rank()
    elif type == 'rpi':
      return Player.all_by_rpi_rank()
    else:
      raise 'No such rank type %s' % type

class Game(db.Model):
  created_date = db.DateTimeProperty(auto_now_add=True)
  completed_date = db.DateTimeProperty()
  """The player who created the game."""
  player_1 = db.ReferenceProperty(Player, collection_name='game_set_1')
  """The player who joined the game."""
  player_2 = db.ReferenceProperty(Player, collection_name='game_set_2')
  player_1_score = db.IntegerProperty()
  player_2_score = db.IntegerProperty()
  winner = db.ReferenceProperty(Player, collection_name='game_won_set')

  def __str__(self):
    return "[Player_1: %s, Player_2: %s, Created: %s]" % (self.player_1, self.player_2, self.created_date)

  def is_active(self):
    return self.player_1 != None and self.player_2 != None and self.completed_date == None

  def is_available(self):
    return self.player_1 == None or self.player_2 == None

  def is_completed(self):
    return self.completed_date != None

  @staticmethod
  def all_active():
    return Game.gql("WHERE player_2 != NULL AND completed_date = NULL ORDER BY player_2, created_date DESC")

  @staticmethod
  def all_available():
    return Game.gql("WHERE player_2 = NULL ORDER BY created_date DESC")

  @staticmethod
  def all_completed():
    return Game.gql("WHERE completed_date != NULL ORDER BY completed_date DESC")

  @staticmethod
  def all_completed_asc():
    return Game.gql("WHERE completed_date != NULL ORDER BY completed_date ASC")

