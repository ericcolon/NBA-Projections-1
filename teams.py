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

class TeamDataScrape(webapp2.RequestHandler):
	def get(self):
		url = "http://stats.nba.com/stats/leaguedashteamstats?Conference=&DateFrom=&DateTo=&Division=&GameScope=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Advanced&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=Totals&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2016-17&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision="
		response = urlfetch.fetch(url)
		
		jsonData = json.loads(response.content)
		teams = jsonData['resultSets'][0]['rowSet']
		statHeaders = jsonData['resultSets'][0]['headers']
		
		for i in range(len(teams)):
			teamData = {}
			
			for j in range(len(teams[i])):
				teamData[statHeaders[j]] = teams[i][j]
			
			teamEnt = Team.get_by_id(int(teams[i][0]))
			if teamEnt is None:
				newTeam = Team(
					teamId = teams[i][0],
					name = teams[i][1],
					data = teamData,
					fanduelId = None,
					id = teams[i][0]					
				)
				newTeam.put()
			else:
				teamEnt.data = teamData
				teamEnt.put()
class MapFanduel(webapp2.RequestHandler):
	def get(self):
		url = "http://tribal-primacy-147515.appspot.com/salary/next"
		response = urlfetch.fetch(url)
		jsonData = json.loads(response.content)
		
		teamDict = {}
		teamAbbrDict = {}
		
		for fdTeam in jsonData['data']['teams']:
			teamDict[fdTeam['full_name']] = fdTeam['id']
			teamAbbrDict[fdTeam['full_name']] = fdTeam['code']
		
		teams = Team.query().fetch()
		
		for team in teams:
			try:
				if teamDict[team.name] is not None:
					team.fanduelId = int(teamDict[team.name])
					team.abbr = str(teamAbbrDict[team.name])
					team.put()
			except Exception as e:
				logging.info(e)
				pass
class GetTeams(webapp2.RequestHandler):
	def get(self):
		teamList = []
		teamList = teamList + [p.to_dict() for p in Team.query().fetch()]
		self.response.write(json.dumps(teamList))

		
app = webapp2.WSGIApplication([
	('/teams/data/scrape', TeamDataScrape),
	('/teams/map/fanduel', MapFanduel),
	('/teams/get', GetTeams),

], debug=True)
