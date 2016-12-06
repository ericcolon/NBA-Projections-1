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
import random
from models import *

class CreatePlayers(webapp2.RequestHandler):
	def get(self):
		url = "http://stats.nba.com/stats/commonallplayers?IsOnlyCurrentSeason=1&LeagueID=00&Season=2016-17";
		response = urlfetch.fetch(url)
		jsonData = json.loads(response.content)
		players = jsonData['resultSets'][0]['rowSet']
		playersToPut = []
			
		for i in range(len(players)):
			newPlayer = Player(
				playerId = players[i][0],
				name = players[i][2],
				teamId = players[i][7],
				teamAbbr = players[i][10],
				id = players[i][0]					
			)
			playersToPut.append(newPlayer)
		ndb.put_multi(playersToPut)
		
class SendPlayerToDataScrape(webapp2.RequestHandler):
	def get(self):
		players = Player.query().fetch(keys_only=True)

		for player in players:
			taskqueue.add(url='/players/data/scrape', params={"id": player.id()}, queue_name='player-stat-collect')

class SendPlayerToHeightScrape(webapp2.RequestHandler):
	def get(self):
		players = Player.query().fetch(keys_only=True)

		for player in players:
			taskqueue.add(url='/players/height/scrape', params={"id": player.id()}, queue_name='player-stat-collect')

class SendRecreateClusterData(webapp2.RequestHandler):
	def get(self):
		players = Player.query().fetch(keys_only=True)

		for player in players:
			taskqueue.add(url='/players/cluster/data/scrape', params={"id": player.id()}, queue_name='cluster-data-recreate')
class RecreateClusterData(webapp2.RequestHandler):
	def post(self):
		playerId = self.request.get("id")
		playerEnt = Player.get_by_id(int(playerId))
		if playerEnt.advancedData is None:
			return
		clusterData = {
			"PCT_BLK" : playerEnt.usageData['PCT_BLK'],
			"PCT_AST_FGM" : playerEnt.scoringData['PCT_AST_FGM'],
			"PCT_FGA_2PT" : playerEnt.scoringData['PCT_FGA_2PT'],
			"PCT_FGA_3PT" : playerEnt.scoringData['PCT_FGA_3PT'],
			"Height" : playerEnt.height,
			"USG_PCT" : playerEnt.usageData['USG_PCT'],
			"PCT_PTS_FT" : playerEnt.scoringData['PCT_PTS_FT'],
			"PCT_STL" : playerEnt.usageData['PCT_STL'],
			"PCT_AST" : playerEnt.usageData['PCT_AST'],
			"PCT_DREB" : playerEnt.usageData['PCT_DREB'],
			"PCT_OREB" : playerEnt.usageData['PCT_OREB'],
			"PCT_PTS_PAINT" : playerEnt.scoringData['PCT_PTS_PAINT']
		}
		playerEnt.clusterData = clusterData
		playerEnt.put()
class PlayerDataScrape(webapp2.RequestHandler):
	def post(self):
		playerId = self.request.get("id")
		playerEnt = Player.get_by_id(int(playerId))
		playerId = str(playerId)
		if playerEnt is None:
			return
			
		exemptStats = ['GROUP_SET', 'GROUP_VALUE', 'CFID', 'CFPARAMS', 'W', 'L', 'W_PCT']
		with requests.Session() as s:
			headers = { 
			  'Referer':'http://stats.nba.com/player/',
			  'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
			}

			url = "http://stats.nba.com/stats/playerdashboardbygeneralsplits?DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerPossession&Period=0&PlayerID=" + playerId + "&PlusMinus=N&Rank=N&Season=2016-17&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&VsConference=&VsDivision="
			
			response = s.get(url, headers=headers)
			jsonData = json.loads(response.content)
			if len(jsonData['resultSets'][0]['rowSet']) == 0:
				return
			else:
				playerStats = jsonData['resultSets'][0]['rowSet'][0]
				statHeaders = jsonData['resultSets'][0]['headers']
				possessionData = {}
				for i in range(len(playerStats)):
					if statHeaders[i] not in exemptStats:
						possessionData[statHeaders[i]] = playerStats[i]
				playerEnt.perPossessionData = possessionData
				
			url = "http://stats.nba.com/stats/playerdashboardbygeneralsplits?DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerPossession&Period=0&PlayerID=" + playerId + "&PlusMinus=N&Rank=N&Season=2016-17&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&VsConference=&VsDivision="
			
			response = s.get(url, headers=headers)
			jsonData = json.loads(response.content)
			if len(jsonData['resultSets'][0]['rowSet']) == 0:
				return
			else:
				playerStats = jsonData['resultSets'][0]['rowSet'][0]
				statHeaders = jsonData['resultSets'][0]['headers']
				advancedData = {}
				for i in range(len(playerStats)):
					if statHeaders[i] not in exemptStats:
						advancedData[statHeaders[i]] = playerStats[i]
				playerEnt.advancedData = advancedData
				
			url = "http://stats.nba.com/stats/playerdashboardbygeneralsplits?DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Usage&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerID=" + playerId + "&PlusMinus=N&Rank=N&Season=2016-17&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&VsConference=&VsDivision="
			response = s.get(url, headers=headers)
			jsonData = json.loads(response.content)
			if len(jsonData['resultSets'][0]['rowSet']) == 0:
				return
			else:
				playerStats = jsonData['resultSets'][0]['rowSet'][0]
				statHeaders = jsonData['resultSets'][0]['headers']
				usageData = {}
				for i in range(len(playerStats)):
					if statHeaders[i] not in exemptStats:
						usageData[statHeaders[i]] = playerStats[i]
				playerEnt.usageData = usageData
				
			url = "http://stats.nba.com/stats/playerdashboardbygeneralsplits?DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Scoring&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerID=" + playerId + "&PlusMinus=N&Rank=N&Season=2016-17&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&VsConference=&VsDivision="
			
			response = s.get(url, headers=headers)
			jsonData = json.loads(response.content)
			if len(jsonData['resultSets'][0]['rowSet']) == 0:
				return
			else:
				playerStats = jsonData['resultSets'][0]['rowSet'][0]
				statHeaders = jsonData['resultSets'][0]['headers']
				scoringData = {}
				for i in range(len(playerStats)):
					if statHeaders[i] not in exemptStats:
						scoringData[statHeaders[i]] = playerStats[i]
				playerEnt.scoringData = scoringData

		playerEnt.updated = int(time.time())
		
		playerEnt.put()
class PlayerHeightScrape(webapp2.RequestHandler):
	def post(self):
		playerId = self.request.get("id")
		url = "http://stats.nba.com/stats/commonplayerinfo?LeagueID=00&PlayerID=" + str(playerId) + "&SeasonType=Regular+Season"
		headers = { 
		  'Cookie':'globalUserOrderId=Id=; bSID=Id=c514c395-4716-43a2-bac2-146844f39de9; rr_rcs=eF4Ny7ENgDAMBMAmFbu85JftvEdgDiBIFHTA_KQ-XVvu77kOI3uB0WXmLmYRLoDt3VftfioyMbEQo28wk0Blxiw1GD9h1hB3; s_pers=%20productnum%3D1%7C1469595367693%3B%20s_last_team%3DBrooklyn%2520Nets%7C1499366460066%3B; s_cc=true; s_fid=4EC1CFB53EAC1C6D-1A876C9377BBC243; s_sq=nbag-n-league%3D%2526pid%253Dstats.nba.com%25253A%25252Fplayer%25252F%2526pidt%253D1%2526oid%253Dhttp%25253A%25252F%25252Fstats.nba.com%25252Fplayer%25252F%2526ot%253DA',
		  'Referer':'http://stats.nba.com/player/',
		}
		options = {
		  'headers': headers
		}
		response = urlfetch.fetch(url, options)
		jsonData = json.loads(response.content)
		heightStr = jsonData['resultSets'][0]['rowSet'][0][10]
		heightSplit = heightStr.split("-")
		height = int(heightSplit[0]) * 12 + int(heightSplit[1])
		playerEnt = Player.get_by_id(int(playerId))
		playerEnt.height = int(height)
		playerEnt.put()
class TeamDataScrape(webapp2.RequestHandler):
	def get(self):
		teamsToPut = []
		
		url = "http://stats.nba.com/stats/leaguedashteamstats?Conference=&DateFrom=&DateTo=&Division=&GameScope=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Advanced&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=Totals&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2016-17&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision="
		response = urlfetch.fetch(url)
		
		jsonData = json.loads(response.content)
		teams = jsonData['resultSets'][0]['rowSet']
		statHeaders = jsonData['resultSets'][0]['headers']
		
		for i in range(len(teams)):
			teamData = {}
			
			for j in range(len(teams[i])):
				teamData[statHeaders[j]] = teams[i][j]
				
			newTeam = Team(
				teamId = teams[i][0],
				name = teams[i][1],
				data = teamData,
				id = teams[i][0]					
			)
			teamsToPut.append(newTeam)
		ndb.put_multi(teamsToPut)
class CalculatePlayersPerPossession(webapp2.RequestHandler):
	def get(self):
		players = Player.query().fetch()
		
		for player in players:
			if player.perPossessionData is not None:
				pointsPerPossessionFd = 0
				pointsPerPossessionFd += player.perPossessionData['PTS']
				pointsPerPossessionFd += player.perPossessionData['REB'] * 1.2
				pointsPerPossessionFd += player.perPossessionData['AST'] * 1.5
				pointsPerPossessionFd += player.perPossessionData['BLK'] * 2
				pointsPerPossessionFd += player.perPossessionData['STL'] * 2
				pointsPerPossessionFd -= player.perPossessionData['TOV']
				
				pointsPerPossessionDk = 0
				pointsPerPossessionDk += player.perPossessionData['PTS']
				pointsPerPossessionDk += player.perPossessionData['FG3M'] * 0.5
				pointsPerPossessionDk += player.perPossessionData['REB'] * 1.25
				pointsPerPossessionDk += player.perPossessionData['AST'] * 1.5
				pointsPerPossessionDk += player.perPossessionData['BLK'] * 2
				pointsPerPossessionDk += player.perPossessionData['STL'] * 2
				pointsPerPossessionDk += (player.perPossessionData['DD2'] - player.perPossessionData['TD3']) * 1.5
				pointsPerPossessionDk += player.perPossessionData['TD3'] * 3
				pointsPerPossessionDk -= player.perPossessionData['TOV'] * 0.5
				
				player.pointsPerPossessionFd = pointsPerPossessionFd
				player.pointsPerPossessionDk = pointsPerPossessionDk
				player.put()
				
class Players(webapp2.RequestHandler):
	def get(self):
		# players = Player.query().fetch()
		playerList = []
		
		playerList = playerList + [p.to_dict() for p in Player.query().fetch()]
		# for player in players:
			# if player.clusterData is None:
				# continue
			# elif player.height is None:
				# continue
			# elif player.scoringData['MIN'] < 12:
				# continue
			# elif player.advancedData['GP'] < 4:
				# continue
			# else:
				# player.clusterData['id'] = player.playerId
				# playerList.append(player.clusterData)
		self.response.write(json.dumps(playerList))
class ClusterPlayers(webapp2.RequestHandler):
	def get(self):
		players = Player.query().fetch()
		playerData = {'players': [], 'columns': {}}
		playerList = []
		
		for k,v in players[0].clusterData.iteritems():
			playerData['columns'][k] = []
		
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
					playerData['columns'][k].append(v)
				player.clusterData['id'] = player.playerId
				playerData['players'].append(player.clusterData)
				
					
		self.response.write(json.dumps(playerData))
class StoreMap(webapp2.RequestHandler):
	def get(self):
		players = Player.query().fetch()
		playerDict = {}

		for player in players:
			playerName = player.name
			playerDict[playerName] = player.playerId
			
			newPlayerName1 = playerName.replace(".", "")
			playerDict[newPlayerName1] = player.playerId
			
			newPlayerName2 = playerName.replace(" Jr.", "")
			playerDict[newPlayerName2] = player.playerId
			
		playerMapToPut = PlayerTable(
			data = playerDict,
			id = 1				
		)
		playerMapToPut.put()

		self.response.write(json.dumps(playerDict))
class MapFanduel(webapp2.RequestHandler):
	def get(self):
		url = "http://tribal-primacy-147515.appspot.com/salary/next"
		response = urlfetch.fetch(url)
		jsonData = json.loads(response.content)
		
		mapTable = PlayerTable.get_by_id(1)
		
		for player in jsonData['data']['players']:
			try:
				currentPlayerId = mapTable.data[player['fullName']]
			except:
				currentPlayerId = None
			if currentPlayerId is not None:
				currentPlayer = Player.get_by_id(currentPlayerId)
				if currentPlayer.fanduelId is None:
					currentFanduelId = player['id'].split("-")
					currentPlayer.fanduelId = int(currentFanduelId[1])
					currentPlayer.put()
class MapLabs(webapp2.RequestHandler):
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
				currentPlayer = Player.get_by_id(currentPlayerId)
				if currentPlayer.labsId is None:
					currentLabsId = player['PlayerId']
					currentPlayer.labsId = int(currentLabsId)
					currentPlayer.put()
class ScrapeMinutes2(webapp2.RequestHandler):
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
class ScrapeMinutes(webapp2.RequestHandler):
	def get(self):
		minutesDict = {}
		
		url = "http://tribal-primacy-147515.appspot.com/projections/get?id=FD"
		response = urlfetch.fetch(url)
		jsonData = json.loads(response.content)
		
		playersUrl = "http://nbacluster.appspot.com/assets/playermap.json"
		playersResponse = urlfetch.fetch(playersUrl)
		playersJson = json.loads(playersResponse.content)
		
		playerMap = {}
		playerMapFd = {}
		for player in playersJson:
			playerMap[int(player['flabsId'])] = int(player['playerId'])
			playerMapFd[int(player['fanduelId'])] = int(player['playerId'])
		
		for player in jsonData:
			try:
				currentPlayerId = playerMap[int(player['PlayerId'])]
			except:
				currentPlayerId = None
			if currentPlayerId is not None:

				# currentPlayer = PlayerMinutes.get_by_id(currentPlayerId)
				
				minutes = float(player['MinutesProj'])
				newRandom = random.randint(-5,5)
				newRandomFloat = float(newRandom) / 10
				
				newMinutes = minutes + newRandomFloat
				
				minutesDict[currentPlayerId] = newMinutes
		salaryUrl = "http://tribal-primacy-147515.appspot.com/salary/next"
		salaryResponse = urlfetch.fetch(salaryUrl)
		salaryJsonData = json.loads(salaryResponse.content)
		
		jsonPlayers = salaryJsonData['data']['players']
		for i in range(len(jsonPlayers)):
			currentFanduelId = jsonPlayers[i]['id'].split("-")
			realFanduelId = int(currentFanduelId[1])
			try:
				realPlayerId = playerMapFd[realFanduelId]
			except KeyError:
				realPlayerId = None 
			if realPlayerId is not None:
				currentPlayer = PlayerMinutes.get_by_id(realPlayerId)
				try:
					newPlayerMinutes = minutesDict[realPlayerId]
				except:
					newPlayerMinutes = 0
				if currentPlayer is None:
					newPlayer = PlayerMinutes(
						labs = newPlayerMinutes,
						id = realPlayerId
					)
					newPlayer.put()
				else:
					currentPlayer.labs = newPlayerMinutes
					currentPlayer.put()

app = webapp2.WSGIApplication([
	('/players/create', CreatePlayers),
	('/players/data/send', SendPlayerToDataScrape),
	('/players/data/scrape', PlayerDataScrape),
	('/players/height/send', SendPlayerToHeightScrape),
	('/players/height/scrape', PlayerHeightScrape),
	('/players/cluster/data/send', SendRecreateClusterData),
	('/players/cluster/data/scrape', RecreateClusterData),
	('/players/cluster/data/get', ClusterPlayers),
	('/players/data/get', Players),
	('/players/data/possession/calculate', CalculatePlayersPerPossession),
	('/players/map/fanduel', MapFanduel),
	('/players/map/labs', MapLabs),
	('/players/map/store', StoreMap),
	('/players/minutes/scrape', ScrapeMinutes),

], debug=True)
