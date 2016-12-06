import webapp2
import cgi
import requests
import os
import sys
import json
import logging
import urllib
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
import re
import time
from models import *

class CreateDay(webapp2.RequestHandler):
	def get(self):
		opponentIdDict = {}
		fixturePossessions = {}
		fixturePossMin = {}
		clusters = {}
		clustersZ = {}
		playerList = []
		
		url = "http://tribal-primacy-147515.appspot.com/salary/next"
		response = urlfetch.fetch(url)
		jsonData = json.loads(response.content)
		
		teamUrl = "http://nbacluster.appspot.com/assets/teams.json"
		teamResponse = urlfetch.fetch(teamUrl)
		teamJson = json.loads(teamResponse.content)
		
		playersUrl = "http://nbacluster.appspot.com/assets/players.json"
		playersResponse = urlfetch.fetch(playersUrl)
		playersJson = json.loads(playersResponse.content)
		
		for fixture in jsonData['data']['fixtures']:
			homeTeamFdId = fixture['home_team']['team']['_members'][0]
			awayTeamFdId = fixture['away_team']['team']['_members'][0]
			
			homeTeamId = teamJson[homeTeamFdId]
			awayTeamId = teamJson[awayTeamFdId]
			
			opponentIdDict[homeTeamFdId] = awayTeamId
			opponentIdDict[awayTeamFdId] = homeTeamId
			
			homeTeamEnt = Team.get_by_id(homeTeamId)
			clusters[homeTeamId] = homeTeamEnt.clusters
			clustersZ[homeTeamId] = homeTeamEnt.clustersZ
			homePace = float(homeTeamEnt.data['PACE'])
			
			awayTeamEnt = Team.get_by_id(awayTeamId)
			clusters[awayTeamId] = awayTeamEnt.clusters
			clustersZ[awayTeamId] = awayTeamEnt.clustersZ
			awayPace = float(awayTeamEnt.data['PACE'])
			
			fixturePossessions[int(fixture['id'])] = homePace * awayPace /  99.013
			fixturePossMin[int(fixture['id'])] = (homePace * awayPace /  99.013) / 48
			
		for player in jsonData['data']['players']:
			currentFanduelId = player['id'].split("-")
			realFanduelId = int(currentFanduelId[1])
			playerId = playersJson[realFanduelId]
			
			playerEnt = Players.get_by_id(playerId)
			minutesEnt = PlayerMinutes.get_by_id(playerId)
			
			playerMinutes = minutesEnt.labs
			playerFdppp = playerEnt.pointsPerPossessionFd
			
			opponentId = OpponentIdDict[int(player['team']['_members'][0])]
			clusterRatio = clusters[opponentId]
			clusterZScore = clustersZ[opponentId]
			
			adjustedFdppp = playerFdppp * clusterRatio
			
			gamePossessions = fixturePossessions[int(player['fixture']['_members'][0])]
			gamePossMin = fixturePossMin[int(player['fixture']['_members'][0])]
			
			playerFdppm = gamePossMin * playerFdppp
			playerFdppmAdj = gamePossMin * adjustedFdppp
			
			playerProjectionAdj = playerFdppmAdj * playerMinutes
			playerProjection = playerFdppm * playerMinutes
			
			newPlayer = {
				'fanduel': player,
				'playerId': playerId,
				'minutes': playerMinutes,
				'fppp': playerFdppp,
				'opponentId': opponentId,
				'cluster': playerEnt.cluster,
				'clusterName': clusterNames[playerEnt.cluster],
				'clusterRatio', clusterRatio,
				'clusterZ', clusterZScore,
				'adjFppp', adjustedFdppp,
				'gamePoss', gamePossessions,
				'gamePossMin', gamePossMin,
				'playerFdppm', playerFdppm,
				'playerFdppmAdj', playerFdppmAdj,
				'playerProjectionAdj', playerProjectionAdj,
				'playerProjection', playerProjection
			}
			playerList.append(newPlayer)			
			
		self.response.write(playerList)
		
class ScrapeMinutes(webapp2.RequestHandler):
	def get(self):
		url = "http://tribal-primacy-147515.appspot.com/projections/get?id=FD"
		response = urlfetch.fetch(url)
		jsonData = json.loads(response.content)
		
		mapTable = PlayerTable.get_by_id(1)
		
		for player in jsonData:
			try:
				currentPlayerId = mapTable.data[player['Player_Name']]
			except:
				currentPlayerId = None
			if currentPlayerId is not None:
				currentPlayer = PlayerMinutes.get_by_id(currentPlayerId)
				if currentPlayer is None:
					newPlayer = PlayerMinutes(
						labs = float(player['MinutesProj']),
						id = currentPlayerId
					)
					newPlayer.put()
				else:
					currentPlayer.labs = float(player['MinutesProj'])
					currentPlayer.put()

app = webapp2.WSGIApplication([
	('/day/create', CreateDay),

], debug=True)
