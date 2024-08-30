print('program started...')

#libraries that need to be imported
import praw
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web

import time
import requests
import calendar
import datetime
import numpy as np

import matplotlib.pyplot as plt
#https://github.com/shilewenuw/get_all_tickers - link for get-all-tickers pip install stuff
#from get_all_tickers import get_tickers as gt

#set to true if you want the program to show progress when it is running
showProgress = True

def optprint(*args):
    if showProgress:
        for arg in args:
            print(arg, end= ' ')
    print()

#csv files containing a list of all publicly traded stock ticker symbols on the NASDAQ and NYSE+
#NOTE: You can also manually set this list to only the ticker's you want to get data for to speed up computation
optprint('creating a list of all publicly traded stock ticker symbols on the NASDAQ and NYSE...')

NYSETickers = pd.read_csv("C:/AaravWorld/StockMarketData/NYSEDataNow.csv")
NASDAQTickers = pd.read_csv("C:/AaravWorld/StockMarketData/NASDAQDataNow.csv")
AllTickers = ['GME']#list(NYSETickers['Symbol']) + list(NASDAQTickers['Symbol'])

optprint('created a list of all stock tickers')
print(AllTickers)

optprint('signing client into reddit praw webscraper...')
#reddit praw webscraper client info+
reddit = praw.Reddit(
    client_id = "EXAMPLE",
    client_secret="EXAMPLE",
    password="EXAMPLE",
    user_agent="EXAMPLE",
    username="EXAMPLE",
)

#authenticates I am the correct user**********************
print(reddit.user.me())

wsb = reddit.subreddit('wallstreetbets')

optprint('signed client into reddit')


#gets the hype, market cap, and short ratio for each popular stock
def getTickerData(subreddit, posts):
    optprint('GETTING TICKER DATA...')
    tickerData = {}

    #goes through the posts on WallStreetBets
    for post in posts:

        # identifies tickers listed in a post
        tickersIdentified = []
        for ticker in AllTickers:
            for i in range(len(post.title) - len(ticker) + 1):
                if post.title[i:i + len(ticker)] == ticker.upper():


                    leadChar = False
                    followChar = False

                    # sees if the leading character implies the beginning of a ticker symbol
                    if i == 0:
                        leadChar = True
                    else:
                        leadingChar = post.title[i - 1]
                        if leadingChar == '$' or leadingChar == ' ':
                            leadChar = True

                    # see if the last character implies the end of a ticker symbol
                    if i == len(post.title) - len(ticker):
                        followChar = True
                    else:
                        followingChar = post.title[i + len(ticker)]
                        if not followingChar.isalpha():
                            followChar = True

                    #adds ticker to list if the leading character and following character are valid and the ticker symbol is not already part of the list
                    if leadChar and followChar and ticker not in tickersIdentified:
                        tickersIdentified.append(ticker)

        #gets the post's score and number of comments
        numComments = post.num_comments
        score = post.score

        #calculates the "hype" of the post
        hype = score + 2 * numComments

        for t in tickersIdentified:

            #creates new entry in dict tickerData if not already there
            if t not in tickerData:
                #THIS OTHER DATA NEEDS TO BE INDEXED BACK TO THE APPROPRIATE DATE. UNTIL THEN, I WILL EXCLUDE THEM
                pubTicker = yf.Ticker(t)

                # get short ratio
                shortRatio = 0#pubTicker.info['shortRatio']**
                # get market cap
                marketCap = 0#data.get_quote_yahoo(t)['marketCap'].tolist()[0]**

                # initial hype (zero), market cap, and short ratio for each stock
                tickerData[t] = [0, marketCap, shortRatio]

            #adds a base hype of 1500 per post plus a proportional amount of extra hype as calculated earlier
            tickerData[t][0] += 1500 + hype / len(tickersIdentified)

    optprint('got ticker data')
    return tickerData


#creates one score based on the ticker's data
def calcTickerScores(tickerData):
    optprint('calculating ticker scores...')
    tickerScores = {}

    for ticker in tickerData:
        ##I will put the most weight on the "hype behind a stock
        score = tickerData[ticker][0] - 0.000001 * tickerData[ticker][1] + 1000 * tickerData[ticker][2]
        if score > 0:
            tickerScores[ticker] = score

    optprint('calculated ticker scores')
    return tickerScores



#gets reddit posts from a specific time range
def submissions_pushshift_praw(subreddit, start=None, end=None, limit=100, extra_query=""):
    optprint('GETTING PRAW REDDIT POST SUBMISSIONS...')
    """
    For more information on PRAW, see: https://github.com/praw-dev/praw
    For more information on Pushshift, see: https://github.com/pushshift/api
    """
    matching_praw_submissions = []

    # Default time values if none are defined (credit to u/bboe's PRAW `submissions()` for this section)
    utc_offset = 28800
    now = int(time.time())
    start = max(int(start) + utc_offset if start else 0, 0)
    end = min(int(end) if end else now, now) + utc_offset

    # Format our search link properly.
    search_link = ('https://api.pushshift.io/reddit/submission/search/'
                   '?subreddit={}&after={}&before={}&sort_type=score&sort=asc&limit={}&q={}')
    search_link = search_link.format(subreddit, start, end, limit, extra_query)

    # Get the data from Pushshift as JSON.
    retrieved_data = requests.get(search_link)
    returned_submissions = retrieved_data.json()['data']

    # Iterate over the returned submissions to convert them to PRAW submission objects.
    for submission in returned_submissions:
        # Take the ID, fetch the PRAW submission object, and append to our list
        praw_submission = reddit.submission(id=submission['id'])
        matching_praw_submissions.append(praw_submission)

    # Return all PRAW submissions that were obtained.
    optprint('got praw reddit posts')
    return matching_praw_submissions


#creates a graph to visualize a stock's hype compared to its price
def createTickerGraph(ticker, tickerHypeOverTime, start = '2020-12-14', end = '2021-06-17'):

    optprint('CREATING TICKER GRAPH...')
    # x axis value is time (dates)
    dates = []
    # y axis values are market prices and hype
    hype = []
    marketPrices = []

    #creates a dataframe of downloaded market prices
    optprint('downloading prices...')
    marketPricesDf = yf.download(ticker, start, end)['Adj Close']#web.DataReader(ticker, 'yahoo',start, end)

    #program waits while data is downloading
    for i in range(3):
        optprint(3-i, 'seconds left')
        time.sleep(1)
    print('marketPricesDf')
    print(marketPricesDf.head())

    #converts the dates into an interactable form
    oldIndex = list(marketPricesDf.index)
    newIndex = []
    for i in oldIndex:
        newIndex.append(str(i).split()[0][5:].strip('-'))

    #updates the index for marketPricesDf
    marketPricesDf.index = newIndex
    print('marketPricesDf.index')
    print(list(marketPricesDf.index))
    '''#print(marketPricesDf.get_value('2020-12-14', 'Adj Close'))
    #print(marketPricesDf['2020-12-14'])
    print('market prices df', marketPricesDf)'''

    #formats the tickerHype data
    optprint('formatting tickerHype data...')
    for date in tickerHypeOverTime:
        #some nasty code to format the epoch time variable into a date
        formattedTime = datetime.datetime.fromtimestamp(date)
        fullyFormattedTime = str(formattedTime).split()[0][5:].strip('-')

        #adds the market price to the y-axis values marketPrices
        try:
            marketPrices.append(marketPricesDf[fullyFormattedTime])
        except:
            #will be called if the asset is not traded that day (since weekend or holiday)
            if len(marketPrices) != 0:
                marketPrices.append(marketPrices[-1])
            else:
                marketPrices.append(0)

        #updates the date to the x-axis values dates
        dates.append(fullyFormattedTime)

        #adds to "hype" if ticker in tickerHypeOverTime
        snap = tickerHypeOverTime[date]
        if ticker in snap:
            hype.append(tickerHypeOverTime[date][ticker])
        else:
            hype.append(0)

    optprint('starting to plot data...')
    # plotting the points for the first y-axis
    fig, ax  = plt.subplots()
    ax.plot(dates, hype, color = 'red', marker = 'o')
    ax.set_xlabel('Date')
    ax.set_ylabel(ticker + ' Hype', color = 'red')

    #plots the points for the second y-axis
    ax2=ax.twinx()
    ax2.plot(dates, marketPrices, color = 'blue', marker = 'o')
    ax2.set_ylabel("Market Price", color="blue")

    plt.xticks(np.arange(0, len(dates)+1, 2))

    # giving a title to my graph
    plt.title(ticker + ' Hype Over Time')

    # function to show the plot
    optprint('showing data...')
    plt.show()
    optprint('created ticker graph')




#function which creates dictionary that shows ticker scores for each date

#start, updateRate, and end times for the simulation are in terms of epoch time
#converter for epoch times https://www.epochconverter.com/
#difference for one day in terms of epoch time is 86400

#WARNING, THE PROCESS COULD TAKE UP TO HOURS, ESPECIALLY IF A SHORTER UPDATE RATE IS CHOSEN
def getTickerScoresOverTime(postsPerPeriod =  250 ,simStartTime = 1607835600+86400, updateRate = 86400, simEndTime = calendar.timegm(time.gmtime())):
    optprint('GETTING TICKER SCORES...')
    tickerScoresOverTime = {}
    simTime = simStartTime + 0
    updateRateDays = updateRate//86400 #converts from epoch time to days
    if updateRateDays == 0:
        updateRateDays = 1

    while simTime < simEndTime:

        try:
            #gets the posts and tickerData (marketcap, short ratio, hype) over the last time period
            prawPosts = submissions_pushshift_praw(wsb, start=simTime, end=simTime + updateRateDays * 86400, limit=postsPerPeriod)
            myTickerData = getTickerData(wsb, prawPosts)
        except Exception as e:
            tickerScoresOverTime[simTime] = {'ERROR IN REQUEST': str(e)}
            simTime += updateRateDays * 86400
            continue

        #get the stocks' "scores"
        myTickerScores = calcTickerScores(myTickerData)
        print(simTime, ': ', myTickerScores, ',')

        tickerScoresOverTime[simTime] = myTickerScores

        #updates the simTime
        simTime += updateRateDays * 86400

    print('tickerScoresOverTime)')
    print(tickerScoresOverTime)
    print('got ticker scores')
    return tickerScoresOverTime


if __name__ == "__main__":
    #starts on December 14 (1615957200)
    myTickerScoresOverTime = getTickerScoresOverTime(postsPerPeriod= 200, simStartTime=1630095558, updateRate=172800)

    #I can create a ticker graph for really any stock I want
    createTickerGraph('GME', myTickerScoresOverTime, '2020-12-14', '2021-6-17')
    #ataFrame(data={‘Tick’: tickerlist, ‘Counts’: sum})
    print('program ended...')
