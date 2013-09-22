# TwitterSearch - https://github.com/ckoepp/TwitterSearch

import csv, sys, re, datetime

# TODO: look at auto graph generation with one of the python graph libraries

if len(sys.argv) != 2:
  print "Usage: %s <filename.csv>" % (sys.argv[0])
  sys.exit(1)

try:
  f = open(sys.argv[1],"r")
except IOError:
  print "Error opening file: %s" % (sys.argv[1])
  sys.exit(2)

r = csv.DictReader(f)

tids = [] # seen tweet IDs
ids = {} # sender handles {"id": id, "total":totaltweets }
mentions = {} # who is mentioned {"id": id, "total":nummentions}
stats = {"public":0, "mention":0} # public vs mention tweets
hashtags = {} # hashtags and their prevalence
# times: { date: { hour1: numtweets, hour2: numtweets } }
times = {} # do time distribution too

# regular expressions
uid = re.compile(r"(@\w+)", re.I)
tags = re.compile(r"(#\w+)", re.I)
# "Thu, 04 Oct 2012 07:56:50 +0000"
dt = re.compile(r"([A-z]+, \d+ [A-z]+ \d+ [\d:]+) \+\d+", re.I)
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
timezone = 8 # timezone offset

# fields are: TweetID, From User, Tweet, Time
for t in r:
  # since we're concatenating log files, we'll keep track of what tweet IDs
  # we've seen before, skip if we've done this one before
  if t["TweetID"].lower() in tids:
    continue
  else:
    tids.append(t["TweetID"].lower())
  # Who is sending out the tweets?
  if t["From User"].lower() in ids:
    ids[t["From User"].lower()]["total"] += 1
  else:
    ids[t["From User"].lower()] = {"id":t["From User"].lower(), "total":1}

  # Who is being mentioned?
  uids = re.findall(uid, t["Tweet"])
  uids = list(set([a.lower() for a in uids])) # lowercase then uniques only
  for u in uids:
    if u in mentions:
      mentions[u]["total"] += 1
    else:
      mentions[u] = {"id":u, "total":1}

  # How many tweets are public vs only @replies (brainfart, called them mentions)?
  if t["Tweet"][0] == "@":
    stats["mention"] += 1
  else:
    stats["public"] += 1

  # What are the popular hashtags?
  tweettags = re.findall(tags,t["Tweet"])
  tweettags = list(set([a.lower() for a in tweettags])) # lowercase then uniques only
  for tag in tweettags:
    if tag in hashtags:
      hashtags[tag]["total"] += 1
    else:
      hashtags[tag] = {"tag":tag, "total":1}

  # get the date and time, put into the dictionary
  g = re.match(dt,t["Time"])
  if g: # could be malformed, who knows?
    # modify the time to GMT+8 first, this could change the date
    d = datetime.datetime.strptime(g.groups()[0], "%a, %d %b %Y %H:%M:%S")
    # apply timezone to the listed date
    td = datetime.timedelta(hours=timezone)
    d = d + td
    tdate = d.strftime("%Y-%b-%d %a") # Year-Mon-Day DayOfWeek
    hour = d.hour # don't really care about the minute
    
    if tdate not in times: # no date yet, create and zero out hours
      times[tdate] = {"date":tdate}
      for i in xrange(24):
        times[tdate][i] = 0
    times[tdate][hour] += 1 # increment the hour's total
f.close()

# OK, parsing's done, now output some data into new CSVs
#   toot_data_times.csv       Time distribution
#   toot_data_tags.csv        Popular tags
#   toot_data_mentions.csv    Who go mentioned in tweets
#   toot_data_ids.csv         Who tweeted
#   toot_data_summary.txt     Total number of tweets, tweeters, types

o = open("toot_data_times.csv","w")
ow = csv.DictWriter(o, fieldnames=["date",0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23])
ow.writeheader()
for row in sorted(times):
  ow.writerow(times[row])
o.close()

o = open("toot_data_tags.csv","w")
ow = csv.DictWriter(o, fieldnames=["tag","total"])
ow.writeheader()
for row in sorted(hashtags):
  ow.writerow(hashtags[row])
o.close()

o = open("toot_data_mentions.csv","w")
ow = csv.DictWriter(o, fieldnames=["id","total"])
ow.writeheader()
for row in sorted(mentions):
  ow.writerow(mentions[row])
o.close()

o = open("toot_data_ids.csv","w")
ow = csv.DictWriter(o, fieldnames=["id","total"])
ow.writeheader()
for row in sorted(ids):
  ow.writerow(ids[row])
o.close()

o = open("toot_data_summary.txt","w")
o.write("Total tweets: %d\n" % (len(tids)))
o.write("Total unique tweeters: %d\n" % (len(ids)))
o.write("Total unique hashtags: %d\n" % (len(hashtags)))
o.write("Public tweets: %d\n@Replies: %d\n" % (stats["public"], stats["mention"]))
o.close()

