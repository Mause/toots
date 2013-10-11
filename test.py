#!/Library/Frameworks/Python.framework/Versions/3.3/bin/python3
from toots import *

db = TootsDB(1)

#keywords = ["ECAWA","WApln","TMWA"]
keywords = ["ECAWA"]
for kw in keywords:
  #db.get_new_tweets([kw])
  t = db.retrieve(kw,20131008)
  tooter = Toots(kw,t)
  tooter.build_tweeters(kw+'_tweeters.svg')
  tooter.build_mentions(kw+'_mentions.svg')
  tooter.build_hashtags(kw+'_hashtags.svg')
  tooter.build_timeline(kw+'_timeline.svg') 

# TODO: seems be an issue with timeline building of tweeters, mentions and hashtags
# timeline seems to be getting built properly though
