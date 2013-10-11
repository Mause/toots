import sqlite3
import re
import sys
import datetime
from pprint import pprint

import pygal
from pygal.style import *
from TwitterSearch import *

class TootsDB():
  '''
  Database interface object for storing and retrieving tweet information for a particular
  set of keywords
  '''
  def __init__(self, DEBUG=0):
    self.DEBUG = DEBUG
    self.db = sqlite3.connect("toots.db")
    # TODO: exceptions on this?
    self.cur = self.db.cursor()
    self.cur.execute("CREATE TABLE IF NOT EXISTS toots (id INTEGER, searchterm TEXT, datestamp INTEGER, timestamp TEXT, userid TEXT, tweetid INTEGER, tweettext TEXT, PRIMARY KEY (id));")
    # TODO: check for comfirmation on table create - rowcount might not work as a check if
    # the table already exists?

  def report_error(self, error: list) -> None:
    '''
    Report errors to error.txt along with when it occured and what it was about.
    '''
    source, e = error
    t = datetime.datetime.now().strftime("%Y%m%d-%H:%M")
    if self.DEBUG: print("Caught an error: {} {}".format(source,e)) # DEBUG
    # TODO: should probably error check the error log creation :(
    with open("error.txt","w") as err:
      err.write("{} Error: {} Exception: {}\n".format(t,source,e))

  def _store(self, tweets: list, keywords: list) -> None:
    '''
    Store tweets in the database that have a tweetid greater than the last tweet seen for
    this keyword. Store each tweet along whichever keyword search it matched. This has the
    effect of increasing the space we use since two tweets with the same search term will be
    stored twice, but it also makes it easier to search later.
    '''
    months = { "Jan":"01", "Feb":"02", "Mar":"03", "Apr":"04", "May":"05", "Jun":"06", "Jul":"07", "Aug":"08", "Sep":"09", "Oct":"10", "Nov":"11", "Dec":"12" }
    new = 0
    for kw in keywords:
      last_id = self.cur.execute("select max(tweetid) from toots where searchterm=?;", (kw,)).fetchone()[0]
      if not last_id:
        last_id = 0
      for tweet in tweets:
        userid = tweet['user']['screen_name']
        tweetid = tweet['id']
        m = re.match(r"\w{3} (\w{3}) (\d+) (\d\d:\d\d):\d\d \+\d{4} (\d{4})",tweet['created_at'])
        if m:
          datestamp = int(m.group(4)+months[m.group(1)]+m.group(2))
          timestamp = m.group(3)
        else:
          continue
        tweettext = tweet['text']
        if last_id >= tweetid: # seen this tweet or later one before
          continue
        self.cur.execute("insert into toots (searchterm, datestamp, timestamp, userid, tweetid, tweettext) values (?,?,?,?,?,?);",(kw,datestamp,timestamp,userid,tweetid,tweettext))
        new += 1
        # TODO: error checking here for rowcount
    self.db.commit()
    if self.DEBUG: print("{} new tweets found.".format(new)) # DEBUG

  def retrieve(self, tag: str, date_from: int = 0, date_to: int = 0) -> list:
    '''
    Retrieve tweets matching the given hashtag. Optionally specify a date range in YYYYMMDD format.
    Returns a list of dicts.
    '''
    if date_from and date_to:
      self.cur.execute("select datestamp, userid, tweettext, timestamp from toots where datestamp >= ? and datestamp <= ? and searchterm = ?;", (date_from, date_to, tag,))
    elif date_from:
      self.cur.execute("select datestamp, userid, tweettext, timestamp from toots where datestamp >= ? and searchterm = ?;", (date_from, tag,))
    elif date_to:
      self.cur.execute("select datestamp, userid, tweettext, timestamp from toots where datestamp <= ? and searchterm = ?;", (date_to, tag,))
    else:
      self.cur.execute("select datestamp, userid, tweettext, timestamp from toots where searchterm = ?;", (tag,))
    results = self.cur.fetchall()
    tweets = []
    for result in results:
      tweets.append({
        "date": result[0],
        "user": result[1],
        "text": result[2],
        "time": result[3],
        "term": tag,
        })
    return tweets

  def get_new_tweets(self, keywords: list) -> None:
    '''
    Use the TwitterSearch lib to fetch tweets that match the given keywords.
    Pass tweets to the _store method to update the database.
    '''
    tweets = []
    if self.DEBUG: print("Searching for tweets with {} as keywords.".format(keywords)) # DEBUG
    try:
      tso = TwitterSearchOrder()
      tso.setKeywords(keywords)
      tso.setLanguage('en')
      tso.setCount(1)
      tso.setIncludeEntities(False)

      ts = TwitterSearch(
          consumer_key = 'YOUR STUFF HERE',
          consumer_secret = 'YOUR STUFF HERE',
          access_token = 'YOUR STUFF HERE',
          access_token_secret = 'YOUR STUFF HERE'
        )
      ts.authenticate()
      for tweet in ts.searchTweetsIterable(tso):
        tweets.append(tweet)
    except TwitterSearchException as e:
      self.report_error(["TwitterSearchException",e])

    if self.DEBUG: print("Fetched {} new tweets with {} as keywords.".format(len(tweets),keywords)) # DEBUG
    self._store(tweets, keywords)

  def __del__(self):
    if self.DEBUG: print("Cleaning up.") # DEBUG
    self.db.commit()
    self.cur.close()
    self.db.close()

class Toots():
  '''
  Process tweets and build charts for display.
  Requires a list of tweets retrieved from a TootsDB object.
  '''
  def __init__(self, keyword: str, tweets: list, timezone: int = 8, DEBUG: int = 0):
    self.DEBUG = DEBUG
    self.tweets = tweets
    self.keyword = keyword
    self.timezone = timezone

  def get_num(self) -> int:
    '''
    Return the total number of tweets associated with this object.
    '''
    return len(self.tweets)

  def _get_tweeters(self) -> dict:
    '''
    Return a dictionary containing the number of tweets each person has sent.
    '''
    tweeters = {}
    for tweet in self.tweets:
      if tweet['user'] not in tweeters:
        tweeters[tweet['user']] = 1
      else:
        tweeters[tweet['user']] += 1
    if self.DEBUG: pprint(tweeters) # DEBUG
    return tweeters

  def _get_mentions(self) -> dict:
    '''
    Return a dictionary containing the number of times people were @mentioned.
    This includes reply tweets which have the handle as the first word.
    '''
    mentions = {}
    for tweet in self.tweets:
      handles = re.findall(r"(@\w+)",tweet['text'])
      for h in handles:
        h = h.lower()
        if h not in mentions:
          mentions[h] = 1
        else:
          mentions[h] += 1
    if self.DEBUG: pprint(mentions) # DEBUG
    return mentions

  def public_vs_private(self) -> dict:
    '''
    Return a dict of 'public' (not @replies) vs 'private' (are @replies) tweets.
    '''
    pvp = { "public": 0, "private": 0 }
    for tweet in self.tweets:
      if tweet['text'][0] == '@':
        pvp['private'] += 1
      else:
        pvp['public'] += 1
    if self.DEBUG: pprint(pvp) # DEBUG
    return pvp

  def _popular_tags(self) -> dict:
    '''
    Return a dict of popular hashtags, filtering for the tag associated with
    this object.
    '''
    hashes = {}
    for tweet in self.tweets:
      tags = re.findall(r'#\w+',tweet['text'])
      for tag in tags:
        tag = tag.lower()
        if tag[1:] == self.keyword.lower():
          continue
        if tag not in hashes:
          hashes[tag] = 1
        else:
          hashes[tag] += 1
    if self.DEBUG: pprint(hashes) # DEBUG
    return hashes

  def _time_distribution(self) -> dict:
    '''
    Build an hourly time distribution with the number of tweets.
    Return as a dictionary of days containing a dictionary of hours.
    '''
    times = {}
    for tweet in self.tweets:
      d = datetime.datetime.strptime("{} {}".format(tweet['date'],tweet['time']), '%Y%m%d %H:%M')
      td = datetime.timedelta(hours=self.timezone) # offset by timezone
      d = d + td
      tdate = d.strftime("%Y-%b-%d")
      hour = d.hour
      if tdate not in times:
        times[tdate] = { 'date': tdate }
        for i in range(24):
          times[tdate][i] = 0
      times[tdate][hour] += 1
    if self.DEBUG: pprint(times) # DEBUG
    return times

  def build_tweeters(self, filename: str=None, top: int=15) -> str:
    '''
    Get the list of top tweeters (max of 'top' responses) and build a sorted
    horizontal histogram. If a filename is passed return the filename upon success,
    otherwise return a SVG string for live embedding.
    '''
    chart = pygal.HorizontalBar(show_legend=False, style=BlueStyle)
    chart.title = 'Top Tweeters ({})'.format(self.keyword)
    tweets = self._get_tweeters()
    tweeterlist = sorted(tweets, key=lambda x: tweets[x],reverse=True)[:top]
    if self.DEBUG:
      print("DEBUG: Tweeterlist") # DEBUG
      for t in tweeterlist:
        print("{}: {}".format(t,tweets[t]))
    chart.x_labels = tweeterlist
    tweeters = [tweets[x] for x in tweeterlist]
    chart.add("Tweeters", tweeters)
    if filename:
      chart.render_to_file(filename)
      return filename
    else:
      return chart.render()

  def build_mentions(self, filename: str=None, top: int=15) -> str:
    '''
    Get the list of mentions (max of 'top' responses) and build a sorted
    horizontal histogram. If a filename is passed return the filename upon success,
    otherwise return a SVG string for live embedding.
    '''
    chart = pygal.HorizontalBar(show_legend=False, style=BlueStyle)
    chart.title = 'Top @mentions ({})'.format(self.keyword)
    mentions = self._get_mentions()
    mentionlist = sorted(mentions, key=lambda x: mentions[x],reverse=True)[:top]
    if self.DEBUG:
      print("DEBUG: Mentionlist") # DEBUG
      for t in mentionlist:
        print("{}: {}".format(t,mentions[t]))
    chart.x_labels = mentionlist
    m = [mentions[x] for x in mentionlist]
    chart.add("Mentions", m)
    if filename:
      chart.render_to_file(filename)
      return filename
    else:
      return chart.render()

  def build_hashtags(self, filename: str=None, top: int=15) -> str:
    '''
    Get the list of hashtags (other than the keyword) which have been seen up to a max
    of 'top' responses and build a sorted horizontal histogram. If a filename is passed return
    the filename upon success, otherwise return a SVG string for live embedding.
    '''
    chart = pygal.HorizontalBar(show_legend=False, style=BlueStyle)
    chart.title = 'Top #hashtags (not including {})'.format(self.keyword)
    hashtags = self._popular_tags()
    hashlist = sorted(hashtags, key=lambda x: hashtags[x],reverse=True)[:top]
    if self.DEBUG:
      print("DEBUG: Hashtags") # DEBUG
      for t in hashtags:
        print("{}: {}".format(t,hashtags[t]))
    chart.x_labels = hashlist
    hashes = [hashtags[x] for x in hashlist]
    chart.add("Hashtags", hashes)
    if filename:
      chart.render_to_file(filename)
      return filename
    else:
      return chart.render()

  def build_timeline(self, filename: str=None) -> str:
    '''
    Get the time distribution of tweets and build a histogram showing number of tweets over
    time. If a filename is passed return the filename upon success, otherwise return a SVG for
    live embedding.
    '''
    chart = pygal.Bar(show_legend=True, style=RedBlueStyle, x_label_rotation=30, x_title='Hour')
    chart.title = 'Tweet Time Distribution ({}, GMT{}{})'.format(self.keyword,"+" if self.timezone >= 0 else "-", self.timezone)
    timeline = self._time_distribution()

    dates = sorted([x for x in timeline]) # list of dates
    chart.x_labels = map(lambda x: "{0:02d}:00".format(x), range(24))
    for date in dates:
      data = [timeline[date][x] for x in range(24)]
      chart.add(date, data)

    if filename:
      chart.render_to_file(filename)
      return filename
    else:
      return chart.render()
