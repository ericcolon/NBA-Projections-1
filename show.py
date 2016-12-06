import webapp2
from models import *
import cgi
import os
from google.appengine.ext import ndb
import jinja2
from jinja2 import Template
import sys
import datetime
import json
sys.path.insert(0, 'libs')
JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class Clusters(webapp2.RequestHandler):
	def get(self):
		teams = Team.query().fetch()
		teamList = []
		for team in teams:
			newDict = {
				'name': team.name,
				'clusters' : team.clusterData
			}
			teamList.append(newDict)
		template_values = {

			'teams': teamList,

		}

		template = JINJA_ENVIRONMENT.get_template('clusters.html')
		self.response.write(template.render(template_values))
class ClustersRaw(webapp2.RequestHandler):
	def get(self):
		teams = Team.query().fetch()
		teamList = []
		for team in teams:
			newDict = {
				'name': team.name,
				'clusters' : team.clusterData
			}
			teamList.append(newDict)

		self.response.write(json.dumps(teamList))
class ClustersZ(webapp2.RequestHandler):
	def get(self):
		teams = Team.query().fetch()
		teamList = []
		for team in teams:
			newDict = {
				'name': team.name,
				'clusters' : team.clusterDataZ
			}
			teamList.append(newDict)

		self.response.write(json.dumps(teamList))

class PlayerClusters(webapp2.RequestHandler):
	def get(self):
		players = Player.query().fetch()
		playerList = []
		
		for player in players:
			if player.cluster is not None:
				playerList.append([player.name, player.cluster])
		self.response.write(json.dumps(playerList))
class Teams(webapp2.RequestHandler):
	def get(self):		
		teamList = []
		
		teamList = teamList + [p.to_dict() for p in Team.query().fetch()]
		self.response.write(json.dumps(teamList))
class Minutes(webapp2.RequestHandler):
	def get(self):		
		playerList = []
		
		# playerList = playerList + [p.to_dict() for p in PlayerMinutes.query().fetch()]
		
		players = PlayerMinutes.query().fetch()
		for player in players:
			playerList.append(player)
		self.response.write(playerList)
class ClusterEdit(webapp2.RequestHandler):
	def get(self):		
		clusterNames = {0: 'Ball Handler', 1: 'Wing', 2: 'Big', 3: 'Swing', 4: 'N/A'}
		playerList = []
		
		players = Player.query().fetch()
		for player in players:
			if player.cluster is None:
				playerCluster = 4
			else:
				playerCluster = player.cluster
			newPlayer = {
				'id': player.playerId,
				'cluster': playerCluster,
				'name': player.name,
				'clusterName': clusterNames[playerCluster],
			}
			playerList.append(newPlayer)
			
		template_values = {
			'players': playerList,
		}
		template = JINJA_ENVIRONMENT.get_template('cluster-edit.html')
		self.response.write(template.render(template_values))
class PlayerClusters(webapp2.RequestHandler):
	def get(self):		
		clusterNames = {0: 'Ball Handler', 1: 'Wing', 2: 'Big', 3: 'Swing', 4: 'N/A'}
		playerList = []
		
		players = Player.query().fetch()
		for player in players:
			if player.cluster is None:
				playerCluster = 4
			else:
				playerCluster = player.cluster
			newPlayer = {
				'id': player.playerId,
				'cluster': playerCluster,
				'name': player.name,
				'team': player.teamAbbr,
				'clusterName': clusterNames[playerCluster],
			}
			playerList.append(newPlayer)
			
		template_values = {
			'players': playerList,
		}
		template = JINJA_ENVIRONMENT.get_template('player-clusters.html')
		self.response.write(template.render(template_values))
class ProjectionData(webapp2.RequestHandler):
	def get(self):		
		today = datetime.datetime.today()
		day = str(today.day)
		month = str(today.month)
		year = str(today.year)
		if len(day) == 1:
			day = "0" + day
		
		projectionId = int(month + day + year)
		ent = Projections.get_by_id(projectionId)
		self.response.write(json.dumps(ent.data))
app = webapp2.WSGIApplication([
	('/show/clusters', Clusters),
	('/show/players/clusters', PlayerClusters),
	('/show/clusters/edit', ClusterEdit),
	('/show/clusters/raw', ClustersRaw),
	('/show/clusters/zscores', ClustersZ),
	('/show/players/clusters', PlayerClusters),
	('/show/teams', Teams),
	('/show/projections', ProjectionData),
	('/show/minutes', Minutes),

], debug=True)
