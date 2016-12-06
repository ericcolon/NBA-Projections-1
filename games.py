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
import datetime
from datetime import timedelta
from models import *

def getGamePossessions(gameData):
	gameFga = gameData[0][7] + gameData[1][7]
	gameFta = gameData[0][13] + gameData[1][13]
	gameOrb = gameData[0][15] + gameData[1][15]
	gameTov = gameData[0][21] + gameData[1][21]
	
	return float(gameFga + (0.44 * gameFta) - gameOrb + gameTov) / 2.0

def getFanduelScore(player):
	points = player[26]
	reb = player[20] * 1.2
	ast = player[21] * 1.5
	to = player[24]
	blk = player[23] * 2
	stl = player[22] * 2
	
	return points + reb + ast - to + blk + stl

	
class SendYesterday(webapp2.RequestHandler):
	def get(self):
		yesterday = datetime.datetime.today() - timedelta(1)
		day = str(yesterday.day)
		month = str(yesterday.month)
		year = str(yesterday.year)
		taskqueue.add(url='/games/send/day', params={'day': day, 'month': month, 'year': year}, queue_name='game-scrape')

class ScrapeGamesByDayManual(webapp2.RequestHandler):
	def get(self):
		day = self.request.get('day')
		month = self.request.get('month')
		year = self.request.get('year')
		taskqueue.add(url='/games/send/day', params={'day': day, 'month': month, 'year': year}, queue_name='game-scrape')

class ScrapeGamesByDayAll(webapp2.RequestHandler):
	def get(self):
		for i in xrange(25,31,1):
			# ScrapeGamesByDay(i, 10, 2016)
			taskqueue.add(url='/games/send/day', params={'day': i, 'month': 10, 'year': 2016}, queue_name='game-scrape')
		for i in xrange(1,31,1):
			# ScrapeGamesByDay(i, 11, 2016)
			taskqueue.add(url='/games/send/day', params={'day': i, 'month': 11, 'year': 2016}, queue_name='game-scrape')

class ScrapeGamesByDay(webapp2.RequestHandler):
	def post(self):
		day = self.request.get("day")
		month = self.request.get("month")
		year = self.request.get("year")
		
		with requests.Session() as s:
			headers = { 
			  'Referer':'http://stats.nba.com/player/',
			  'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
			}
			url = "http://stats.nba.com/stats/scoreboardV2?DayOffset=0&LeagueID=00&gameDate=" + str(month) + "%2F" + str(day) + "%2F" + str(year)

			response = s.get(url, headers=headers)

		jsonData = json.loads(response.content)
		gamesList = jsonData['resultSets'][0]['rowSet']
		for game in gamesList:
			params = {'quarters': game[9], 'id': game[2]}
			taskqueue.add(url='/games/data/scrape', params=params, queue_name='game-scrape')
# def ScrapeGamesByDay(day, month, year):
	# with requests.Session() as s:
		# headers = { 
		  # 'Referer':'http://stats.nba.com/player/',
		  # 'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
		# }
		# url = "http://stats.nba.com/stats/scoreboardV2?DayOffset=0&LeagueID=00&gameDate=" + str(month) + "%2F" + str(day) + "%2F" + str(year)

		# response = s.get(url, headers=headers)

	# jsonData = json.loads(response.content)
	# gamesList = jsonData['resultSets'][0]['rowSet']
	# for game in gamesList:
		# params = {'quarters': game[9], 'id': game[2]}
		# taskqueue.add(url='/games/data/scrape', params=params, queue_name='game-scrape')

class ScrapeGame(webapp2.RequestHandler):
	def post(self):
		gameId = self.request.get('id')
		gameQuarters = self.request.get('quarters')
		
		gameEnt = Game.get_by_id(int(gameId))
		if gameEnt is None:
			# if gameEnt.added is True:
				# return

			url = "http://stats.nba.com/stats/boxscoretraditionalv2?EndPeriod=10&EndRange=31800&GameID=" + str(gameId) + "&RangeType=0&Season=2016-17&SeasonType=Regular+Season&StartPeriod=1&StartRange=0"
			response = urlfetch.fetch(url)
			jsonData = json.loads(response.content)
		else:
			jsonData = gameEnt.data
			
		gameData = jsonData['resultSets'][1]['rowSet']

		gamePossessions = getGamePossessions(gameData)

		if int(gameQuarters) == 4:
			gameMinutes = 48
		else:
			gameMinutes = 48 + ((int(gameQuarters)-4) * 5)

		homeTeamId = gameData[0][1]
		awayTeamId = gameData[1][1]
		
		homeTeamEnt = Team.get_by_id(int(homeTeamId))
		awayTeamEnt = Team.get_by_id(int(awayTeamId))
		
		playerList = jsonData['resultSets'][0]['rowSet']

		for player in playerList:
			playerEnt = Player.get_by_id(int(player[4]))
			
			if playerEnt is None:
				continue
				
			if playerEnt.pointsPerPossessionFd is None or playerEnt.cluster is None:
				continue

			pointsPerPossessionFd = playerEnt.pointsPerPossessionFd
			
			playerMinutesString = player[8]
			if playerMinutesString is None:
				continue
			playerMinutesString = playerMinutesString.split(":")
			playerMinutes = float(playerMinutesString[0]) + ((float(playerMinutesString[1]) * float(100.0/60.0))/100.0)
			
			
			playerGamePossessions = (playerMinutes / gameMinutes) * gamePossessions
			
			playerGameFanduelPoints = getFanduelScore(player)
			
			playerExpectedFanduelPoints = pointsPerPossessionFd * playerGamePossessions
			if player[1] == homeTeamId:
				awayTeamEnt.clusterData[str(playerEnt.cluster)]['expected'] += playerExpectedFanduelPoints
				awayTeamEnt.clusterData[str(playerEnt.cluster)]['actual'] += playerGameFanduelPoints
				awayTeamEnt.clusterData[str(playerEnt.cluster)]['ratio'] = awayTeamEnt.clusterData[str(playerEnt.cluster)]['actual'] / awayTeamEnt.clusterData[str(playerEnt.cluster)]['expected']
			else:
				homeTeamEnt.clusterData[str(playerEnt.cluster)]['expected'] += playerExpectedFanduelPoints
				homeTeamEnt.clusterData[str(playerEnt.cluster)]['actual'] += playerGameFanduelPoints
				homeTeamEnt.clusterData[str(playerEnt.cluster)]['ratio'] = homeTeamEnt.clusterData[str(playerEnt.cluster)]['actual'] / homeTeamEnt.clusterData[str(playerEnt.cluster)]['expected']

			
		awayTeamEnt.put()
		homeTeamEnt.put()
		newTeam = Game(
			data = jsonData,
			time = int(time.time()),
			added = True,
			id = int(gameId)
		)
		newTeam.put()
		
app = webapp2.WSGIApplication([
	('/games/data/scrape', ScrapeGame),
	('/games/send/day', ScrapeGamesByDay),
	('/games/send/manual', ScrapeGamesByDayManual),
	('/games/send/all', ScrapeGamesByDayAll),	
	('/games/send/yesterday', SendYesterday),	

], debug=True)