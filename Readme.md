# Slack-crypto
A simple python program to detect larger changes in a cryptocurrency then post an update message to slack (using an incoming webhook).

## How it works
Slack-crypto uses the [Coinbase API](https://docs.pro.coinbase.com/#get-historic-rates) to retrieve the hourly price
 for the last 300 hours (so the resolution is hourly). It then uses this to calculate an exponential moving average
 (using the period set) and if the current price is above/below this EMA by a threshold amount then a message will be posted.
 
To prevent multiple messages being sent for a single increase/decrease, a cooldown value is set. This stops a message being sent,
 unless the current price has gone up/down by the threshold amount according to the price when the message was last sent.
 Additionally this cooldown period is ignored if the direction of the change is reversed. The details of the last
 message sent are stored in a json file (the name of which can be configured to support multiple cron jobs).

## Customisation
Command line args (via argparse) is used to set variables to be tweaked, although only the slack incoming webhook url is
 required. Currently the amount of command line options is limited to only the variables that I find useful (EMA period, 
 threshold percentage, cooldown period, slack channel, webhook name). There are more things that could be customisable
 via command line (eg. images, currency pair, colour thresholds), but those are easily tweakable from within the script, 
 and can be easily added via argparse (I should add them at some point).
 
 At the moment only BTC-USD is 'supported', however as mentioned the constants at the start of the script are setup so
 it's trivial to change (change the primary/secondary currency). 

## Requirements
Python 3.6+ and standard libraries\
Requests