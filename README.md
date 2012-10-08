# stats.py #

## Backstory ##
This is a short Python script which grew out of a session at the ACEC2012
conferece for technology in education where analysis was being given on the
use of Twitter as a back-channel. It sounded like the number crunching and
organisation of data was pretty tedious so I figured I'd write a bit of code
to look at the problem myself.

## What it does ##
The script takes a CSV-formatted text file (I used the output from
[SearchHash](http://searchhash.com))
and produces a number of its of CSV files and a summary text file containing
broken-down data.

Current it generates:
* list of tweeter IDs and number of tweets
* list of @mentions and number of times mentioned
* list of #hashtags and number of times tweeted
* time distribution (broken down by date and hour)
* summary containing total tweets, tweeters, hashtags and public vs @reply
  tweets

## TODO ##
A couple of low-hanging fruit would be
* getting twitter data in the script removing the reliance on third-party tools
* generating graphs from the data as well as the CSVs
