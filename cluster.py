from models import *
import numpy as np
#import matplotlib.pyplot as plt
from google.appengine.api import taskqueue
import json
from kmeans import kmeans

def standardize(x, mean, stdev):
	return (x - mean) / stdev

def createCluster(dataDict):
	ids = []
	means = {}
	stdevs = {}
	allPlayers = []
	fields = []
	clusteredPlayers = {}

	playerData = dataDict['players']
	columnData = dataDict['columns']

	for k,v in columnData.iteritems():
		means[k] = np.mean(v)
		stdevs[k] = np.std(v, ddof=1)

	for i in range(len(playerData)):
		ids.append(playerData[i]['id'])
		currentPlayer = []
		for k,v in playerData[i].iteritems():
			if i == 0 and k != "id":
				fields.append(k)
			if k != "id":
				currentPlayer.append(standardize(v, means[k], stdevs[k]))

		allPlayers.append(currentPlayer)

	X = np.vstack(allPlayers)
	centroids, C = kmeans(X, K = 4)

	for i in range(len(C)):
		taskqueue.add(url='/cluster/assign/task', params={"id": ids[i], "cluster": C[i]}, queue_name='cluster-assign')
		playerEnt = Player.get_by_id(ids[i])
		clusteredPlayers[ids[i]] = C[i].item()
		#clusteredPlayers.append((ids[i],C[i]))
		
	centroidList = []
	for i in range(len(centroids)):
		clust = []
		for j in range(len(centroids[i])):
			clust.append(centroids[i][j].item())
		centroidList.append(clust)
	return centroidList, clusteredPlayers

class Cluster(webapp2.RequestHandler):
	def get(self):
		players = Player.query().fetch()
		dataDict = {'players': [], 'columns': {}}
		
		for k,v in players[0].clusterData.iteritems():
			dataDict['columns'][k] = []
		
		for player in players:
			if player.clusterData is None:
				continue
			elif player.height is None:
				continue
			elif player.scoringData['MIN'] < 12:
				continue
			elif player.advancedData['GP'] < 4:
				continue
			else:
				for k,v in player.clusterData.iteritems():
					dataDict['columns'][k].append(v)
				player.clusterData['id'] = player.playerId
				dataDict['players'].append(player.clusterData)

		centroids, clusteredPlayers = createCluster(dataDict)
		clusterDump = {"centroids": centroids, "players": clusteredPlayers}
		self.response.write(json.dumps(clusterDump))

class AssignClusterTask(webapp2.RequestHandler):
	def post(self):
		playerId = int(self.request.get("id"))
		cluster = int(self.request.get("cluster"))
		playerEnt = Player.get_by_id(playerId)
		playerEnt.cluster = cluster
		playerEnt.put()
class AssignClusterTaskManual(webapp2.RequestHandler):
	def get(self):
		playerId = int(self.request.get("id"))
		cluster = int(self.request.get("cluster"))
		playerEnt = Player.get_by_id(playerId)
		playerEnt.cluster = cluster
		playerEnt.put()
class ClearClusters(webapp2.RequestHandler):
	def get(self):
		teams = Team.query().fetch()
		emptyCluster = {
			0: {'expected': 0, 'actual': 0, 'ratio':0},
			1: {'expected': 0, 'actual': 0, 'ratio':0},
			2: {'expected': 0, 'actual': 0, 'ratio':0},
			3: {'expected': 0, 'actual': 0, 'ratio':0}
		}
		for team in teams:
			team.clusterData = emptyCluster
			team.put()

class CreateClusterZScores(webapp2.RequestHandler):
	def get(self):
		teams = Team.query().fetch()
		clusters = {
			"zero": [],
			"one": [],
			"two": [],
			"three": []
		}
		means = {}
		stdevs = {}
		
		for team in teams:
			clusters["zero"].append(team.clusterData["0"]["ratio"])
			clusters["one"].append(team.clusterData["1"]["ratio"])
			clusters["two"].append(team.clusterData["2"]["ratio"])
			clusters["three"].append(team.clusterData["3"]["ratio"])
		
		for k,v in clusters.iteritems():
			means[k] = np.mean(v)
			stdevs[k] = np.std(v, ddof=1)
			
		for team in teams:
			clusterZ = {
				0: standardize(team.clusterData["0"]["ratio"], means["zero"], stdevs["zero"]),
				1: standardize(team.clusterData["1"]["ratio"], means["one"], stdevs["one"]),
				2: standardize(team.clusterData["2"]["ratio"], means["two"], stdevs["two"]),
				3: standardize(team.clusterData["3"]["ratio"], means["three"], stdevs["three"])
			}
			team.clusterDataZ = clusterZ
			team.put()

app = webapp2.WSGIApplication([
	('/cluster/assign/task', AssignClusterTask),
	('/cluster/assign', AssignClusterTaskManual),
	('/cluster/create', Cluster),
	('/cluster/clear', ClearClusters),
	('/cluster/create/zscores', CreateClusterZScores),

], debug=True)
