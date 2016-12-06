import webapp2
import cgi
import os
from google.appengine.ext import ndb
import sys

class PlayerTable(ndb.Model):	
	data = ndb.JsonProperty(indexed=False)
class Player(ndb.Model):	
	perPossessionData = ndb.JsonProperty(indexed=False)
	usageData = ndb.JsonProperty(indexed=False)
	scoringData = ndb.JsonProperty(indexed=False)
	advancedData = ndb.JsonProperty(indexed=False)
	clusterData = ndb.JsonProperty(indexed=False)
	height = ndb.IntegerProperty(indexed=False)
	playerId = ndb.IntegerProperty(indexed=False)
	fanduelId = ndb.IntegerProperty(indexed=False)
	labsId = ndb.IntegerProperty(indexed=False)
	name = ndb.StringProperty(indexed=False)
	teamId = ndb.IntegerProperty(indexed=False)
	teamAbbr = ndb.StringProperty(indexed=False)
	pointsPerPossessionFd = ndb.FloatProperty(indexed=False)
	pointsPerPossessionDk = ndb.FloatProperty(indexed=False)
	projectedMinutes = ndb.FloatProperty(indexed=False)
	cluster = ndb.IntegerProperty(indexed=False)
	clusterString = ndb.StringProperty(indexed=False)
	updated = ndb.IntegerProperty(indexed=False)
class PlayerMinutes(ndb.Model):	
	labs = ndb.FloatProperty(indexed=False)
	bbm = ndb.FloatProperty(indexed=False)
	rg = ndb.FloatProperty(indexed=False)
class Team(ndb.Model):	
	data = ndb.JsonProperty(indexed=False)
	abbr = ndb.StringProperty(indexed=False)
	pace = ndb.FloatProperty(indexed=False)
	teamId = ndb.IntegerProperty(indexed=False)
	fanduelId = ndb.IntegerProperty(indexed=True)
	name = ndb.StringProperty(indexed=False)
	clusterData = ndb.JsonProperty(indexed=False)
	clusterDataZ = ndb.JsonProperty(indexed=False)
class Game(ndb.Model):	
	data = ndb.JsonProperty(indexed=False)
	time = ndb.IntegerProperty(indexed=False)
	added = ndb.BooleanProperty(indexed=False)
class Clusters(ndb.Model):	
	centroids = ndb.JsonProperty(indexed=False)
	assignments = ndb.JsonProperty(indexed=False)
	time = ndb.IntegerProperty(indexed=False)
	name = ndb.StringProperty(indexed=True)
class Projections(ndb.Model):
	player = ndb.JsonProperty(repeated=True)
	data = ndb.JsonProperty(repeated=True)
	teams = ndb.JsonProperty(indexed=False)
	time = ndb.IntegerProperty(indexed=False)