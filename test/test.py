from toots import *

db = TootsDB()
keywords = ["ECAWA"]
# harvest mode
db.get_new_tweets(keywords)
# process mode
t = db.retrieve("ECAWA")
tooter = Toots("ECAWA",t)
tooter.build_tweeters('test_tweeters.svg')
tooter.build_mentions('test_mentions.svg')
tooter.build_hashtags('test_hashtags.svg')
tooter.build_timeline('test_timeline.svg')
