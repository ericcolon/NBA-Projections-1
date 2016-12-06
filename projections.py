import webapp2
import cgi
import os
import sys
import json
import logging
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
import datetime
from models import *

class Create(webapp2.RequestHandler):
	def get(self):
		opponentIdDict = {}
		opponentDict = {}
		fixturePossessions = {}
		fixturePossMin = {}
		clusters = {}
		clustersZ = {}
		playerList = []
		clusterNames = {0: 'Ball Handler', 1: 'Wing', 2: 'Big', 3: 'Swing', 4: 'N/A'}
		url = "http://tribal-primacy-147515.appspot.com/salary/next"
		response = urlfetch.fetch(url)
		jsonData = json.loads(response.content)
		
		teamMap = 	{
			679: 1610612737,
			680: 1610612738,
			696: 1610612751,
			681: 1610612766,
			682: 1610612741,
			683: 1610612739,
			684: 1610612742,
			685: 1610612743,
			686: 1610612765,
			687: 1610612744,
			688: 1610612745,
			689: 1610612754,
			690: 1610612746,
			691: 1610612747,
			692: 1610612763,
			693: 1610612748,
			694: 1610612749,
			695: 1610612750,
			697: 1610612740,
			698: 1610612752,
			699: 1610612760,
			700: 1610612753,
			701: 1610612755,
			702: 1610612756,
			703: 1610612757,
			704: 1610612758,
			705: 1610612759,
			706: 1610612761,
			707: 1610612762,
			708: 1610612764
		}
		
		playersUrl = "http://nbacluster.appspot.com/assets/playermap.json"
		playersResponse = urlfetch.fetch(playersUrl)
		playersJson = json.loads(playersResponse.content)
		
		playerMap = {}
		for player in playersJson:
			playerMap[player['fanduelId']] = player['playerId']
		
		for fixture in jsonData['data']['fixtures']:
			homeTeamFdId = int(fixture['home_team']['team']['_members'][0])
			awayTeamFdId = int(fixture['away_team']['team']['_members'][0])
			
			homeTeamId = teamMap[homeTeamFdId]
			awayTeamId = teamMap[awayTeamFdId]
			
			opponentIdDict[homeTeamFdId] = awayTeamId
			opponentIdDict[awayTeamFdId] = homeTeamId
			
			homeTeamEnt = Team.get_by_id(homeTeamId)
			clusters[homeTeamId] = homeTeamEnt.clusterData
			clustersZ[homeTeamId] = homeTeamEnt.clusterDataZ
			homePace = float(homeTeamEnt.data['PACE'])
			
			awayTeamEnt = Team.get_by_id(awayTeamId)
			clusters[awayTeamId] = awayTeamEnt.clusterData
			clustersZ[awayTeamId] = awayTeamEnt.clusterDataZ
			awayPace = float(awayTeamEnt.data['PACE'])
			
			opponentDict[homeTeamFdId] = awayTeamEnt.abbr
			opponentDict[awayTeamFdId] = homeTeamEnt.abbr
			
			fixturePossessions[int(fixture['id'])] = homePace * awayPace /  99.013
			fixturePossMin[int(fixture['id'])] = (homePace * awayPace /  99.013) / 48
			
		jsonPlayers = jsonData['data']['players']
		for i in range(len(jsonPlayers)):
		# for player in jsonData['data']['players']:
			
			currentFanduelId = jsonPlayers[i]['id'].split("-")
			realFanduelId = int(currentFanduelId[1])
			try:
				playerId = playerMap[realFanduelId]
			except KeyError:
				continue

			playerEnt = Player.get_by_id(playerId)
			minutesEnt = PlayerMinutes.get_by_id(playerId)

			if minutesEnt is None:
				logging.info("No minutesEnt for " + playerEnt.name)
				playerMinutes = 0
			else:
				playerMinutes = minutesEnt.labs
			
			playerFdppp = playerEnt.pointsPerPossessionFd
			if playerFdppp is None:
				continue
			
			opponentId = opponentIdDict[int(jsonPlayers[i]['team']['_members'][0])]
			opponent = opponentDict[int(jsonPlayers[i]['team']['_members'][0])]
			
			if playerEnt.cluster is not None:
				clusterRatio = clusters[opponentId][str(playerEnt.cluster)]['ratio']
				clusterZScore = clustersZ[opponentId][str(playerEnt.cluster)]
			else:
				clusterRatio = 1
				clusterZScore = 0

			
			adjustedFdppp = playerFdppp * clusterRatio
			
			gamePossessions = fixturePossessions[int(jsonPlayers[i]['fixture']['_members'][0])]
			gamePossMin = fixturePossMin[int(jsonPlayers[i]['fixture']['_members'][0])]
			
			playerFdppm = gamePossMin * playerFdppp
			playerFdppmAdj = gamePossMin * adjustedFdppp
			
			playerProjectionAdj = playerFdppmAdj * playerMinutes
			playerProjection = playerFdppm * playerMinutes
			
			playerCluster = playerEnt.cluster
			if playerCluster is None:
				playerCluster = 4

			newPlayer = {
				'fanduel': jsonPlayers[i],
				'playerId': playerId,
				'minutes': playerMinutes,
				'fppp': playerFdppp,
				'opponentId': opponentId,
				'cluster': playerCluster,
				'clusterName': clusterNames[playerCluster],
				'clusterRatio': clusterRatio,
				'clusterZ': clusterZScore,
				'adjFppp': adjustedFdppp,
				'gamePoss': gamePossessions,
				'gamePossMin': gamePossMin,
				'fdppm': playerFdppm,
				'fdppmAdj': playerFdppmAdj,
				'projectionAdj': playerProjectionAdj,
				'projection': playerProjection,
				'opponent': opponent
			}
			playerList.append(newPlayer)
			
		today = datetime.datetime.today()
		day = str(today.day)
		month = str(today.month)
		year = str(today.year)
		if len(day) == 1:
			day = "0" + day
		
		projectionId = int(month + day + year)
		newProjections = Projections(
			data = playerList,
			id = projectionId
		)
		newProjections.put()

app = webapp2.WSGIApplication([
	('/projections/create', Create),

], debug=True)
