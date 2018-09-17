# Slack-crypto
This repo consists of two closely related programs. First, an incoming webhook to detect large/sudden changes in a cryptocurrency and post an update message to slack.
Secondly, code for an app integration which provides a slash command to get the current and historical prices.

## Webhook
Slack-crypto uses the [Coinbase API](https://docs.pro.coinbase.com/#get-historic-rates) to retrieve the hourly price
 for the last 300 hours (resolution can bet set at 5/15/60 minutes, although will increase the number of API calls). 
 It then uses this to calculate an exponential moving average (using the period set) and if the current price is above/below 
 this EMA by a threshold amount then a message will be posted.
 
To prevent multiple messages being sent there is a reset threshold. The price must go back within this threshold to 'reset' the system.
However this is not required if the price continues to go up/down in the previous direction. Instead the last price replaces the EMA
as the base price for which the current price needs to be above/below.

## Slash command
The slash command is a slack app. I only provide my code, so you would have to host it and add the app yourself. 
The command allows custom currency pairs to be retrieved, as well as custom days.

## Customisation
Command line args (via argparse) are used to set required and optional variables. 
Currently the amount of command line options is limited to only the variables that I find useful, but more can easily be added.
 At the moment only BTC-USD is supported for the webhook, however it should be really easy to change this if needed.
 
For the webhook the 'script name' can be provided; this is needed to change where logs are stored and where json data is saved.
Both the slash command and webhook use python's logging library, and can be configured to output to stdout/stderr, and to text files

## Requirements
Python 3.6+ and standard libraries\
Requests