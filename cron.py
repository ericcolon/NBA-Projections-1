cron:
- url: /players/minutes/scrape
  schedule: every 30 minutes from 17:01 to 18:31
  timezone: America/New_York
- url: /players/projections/create
  schedule: every 30 minutes from 17:02 to 18:32
  timezone: America/New_York
- url: /games/send/yesterday
  schedule: every day at 7:00
  timezone: America/New_York