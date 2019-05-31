import urllib.request
import urllib.error
import json
import asyncio
import concurrent.futures
from time import time


def json2dct(source, use_headers=False):

    headers = {}
    if use_headers is True:
        headers = {'User-Agent': 'Mozilla/5.0'}

    req = urllib.request.Request(source, headers=headers)

    try:
        # with urllib.request.urlopen(req) as data:
        #     return json.loads(data.read().decode())
        data = urllib.request.urlopen(req)
    except urllib.error.URLError as e:
        print('API from {} could not be loaded due to URLError'.format(source))
        return False
    except urllib.error.HTTPError as e:
        print('API from {} could not be loaded due to HTTPError'.format(source))
        return False

    try:
        dct = json.loads(data.read().decode())
    except json.decoder.JSONDecodeError as e:
        print('API from {} could no be loaded due to JSONDecodeError'.format(source))
        return False

    data.close()
    return dct


def compile_ExchangesInfos(ExchangesStatus, ExchangesInfo):

    ActiveExchanges = []

    for ExchangeName, active in ExchangesStatus.items():
        if active is True:
            ActiveExchanges.append(ExchangeName)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(getInfo(ActiveExchanges, ExchangesInfo))

    return ExchangesInfo


# http://skipperkongen.dk/2016/09/09/easy-parallel-http-requests-with-python-and-asyncio/
async def getInfo(ActiveExchanges, ExchangesInfo):

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:

        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor,
                get_ExchangeInfo,
                ActiveExchanges[i],
                ExchangesInfo
            )
            for i in range(len(ActiveExchanges))
        ]
        for response in await asyncio.gather(*futures):
            pass


def get_ExchangeInfo(ExchangeName, ExchangesInfo, print_cycles=True):

    t1 = time()
    load = False
    pairs = []
    rates = []  # all rates in the form of [Bid, Ask]

    # BITTREX
    # https://bittrex.com/home/api
    if ExchangeName == 'bittrex':
        CentralCoins = ['BTC', 'ETH', 'USDT']

        dct = json2dct('https://bittrex.com/api/v1.1/public/getmarketsummaries')
        if dct is not False:
            load = True

            for market in dct['result']:
                pair = market['MarketName'].split('-')
                pairs.append(pair)

                rate = [market['Bid'], market['Ask']]
                rates.append(rate)

    # JUBI
    # https://www.jubi.com/help/api.html
    elif ExchangeName == 'jubi':
        CentralCoins = ['CNY']

        dct = json2dct('https://www.jubi.com/api/v1/allticker/')
        if dct is not False:
            load = True

            for coin in dct:
                pairs.append(['CNY', coin.upper()])
                rates.append([dct[coin]['buy'], dct[coin]['sell']])

    # BTC 38
    # http://www.btc38.com/help/document/2581.html
    elif ExchangeName == 'btc38':
        CentralCoins = ['CNY']

        # dct = json2dct('http://api.btc38.com/v1/ticker.php?c=all', use_headers=True)
        dct = json2dct('http://api.btc38.com/v1/ticker.php?LMCL=MZNfWI&LMCL=qqjNHH&c=all', use_headers=True)
        if dct is not False:
            load = True

            for coin in dct:
                if dct[coin]['ticker']:  # check if data for given coin is not empty
                    pairs.append(['CNY', coin.upper()])
                    rates.append([dct[coin]['ticker']['buy'], dct[coin]['ticker']['sell']])

    # YUNBI
    # https://yunbi.com/swagger/#/default
    elif ExchangeName == 'yunbi':
        CentralCoins = ['CNY']

        dct = json2dct('https://yunbi.com//api/v2/tickers.json')
        if dct is not False:
            load = True

            for pair in dct:
                if pair.endswith('cny'):
                    coin = pair[:-3]
                    pairs.append(['CNY', coin.upper()])
                    rates.append([dct[pair]['ticker']['buy'], dct[pair]['ticker']['sell']])
                else:
                    print("WARNING: pair: {} in Yunbi not considered".format(pair))

    # GEMINI
    # https://docs.gemini.com/rest-api/?python#ticker
    elif ExchangeName == 'gemini':

        CentralCoins = ['USD', 'BTC']

        pairs = [['USD', 'BTC'], ['USD', 'ETH'], ['BTC', 'ETH']]

        baseURL = 'https://api.gemini.com/v1/pubticker/'
        pair_tickers = ['btcusd', 'ethusd', 'ethbtc']

        for pair_ticker in pair_tickers:
            pair_dct = json2dct(baseURL + pair_ticker)

            if pair_dct is not False:
                rates.append([pair_dct['bid'], pair_dct['ask']])

        if rates:
            load = True

    # BITFINEX
    # https://bitfinex.readme.io/v2/reference
    elif ExchangeName == 'bitfinex':

        pairs = []
        rates = []

        CentralCoins = ['USD', 'BTC', 'ETH']
        # all_pairs = [['USD', 'BTC'], ['USD', 'ETH'], ['BTC', 'ETH'], ['USD', 'OMG'], ['BTC', 'OMG'], ['ETH', 'OMG'], ['USD', 'LTC'], ['BTC', 'LTC'], ['USD', 'IOTA'], ['BTC', 'IOTA'], ['ETH', 'IOTA'], ['USD', 'BCH'], ['BTC', 'BCH'], ['ETH', 'BCH'], ['USD', 'EOS'], ['BTC', 'EOS'], ['ETH', 'EOS'], ['USD', 'ETC'], ['BTC', 'ETC'], ['USD', 'XMR'], ['BTC', 'XMR'], ['USD', 'NEO'], ['BTC', 'NEO'], ['ETH', 'NEO'], ['USD', 'DASH'], ['BTC', 'DASH'], ['USD', 'ZEC'], ['BTC', 'ZEC'], ['USD', 'XRP'], ['BTC', 'XRP'], ['USD', 'SAN'], ['BTC', 'SAN'], ['ETH', 'SAN'], ['USD', 'BCC'], ['BTC', 'BCC'], ['USD', 'RRT'], ['BTC', 'RRT'], ['USD', 'BCU'], ['BTC', 'BCU']]
        all_pairs = [['BTC', 'USD'], ['ETH', 'USD'], ['ETH', 'BTC'], ['OMG', 'USD'], ['OMG', 'BTC'], ['OMG', 'ETH'], ['LTC', 'USD'], ['LTC', 'BTC'], ['IOTA', 'USD'], ['IOTA', 'BTC'], ['IOTA', 'ETH'], ['BCH', 'USD'], ['BCH', 'BTC'], ['BCH', 'ETH'], ['EOS', 'USD'], ['EOS', 'BTC'], ['EOS', 'ETH'], ['ETC', 'USD'], ['ETC', 'BTC'], ['XMR', 'USD'], ['XMR', 'BTC'], ['NEO', 'USD'], ['NEO', 'BTC'], ['NEO', 'ETH'], ['DASH', 'USD'], ['DASH', 'BTC'], ['ZEC', 'USD'], ['ZEC', 'BTC'], ['XRP', 'USD'], ['XRP', 'BTC'], ['SAN', 'USD'], ['SAN', 'BTC'], ['SAN', 'ETH'], ['BCC', 'USD'], ['BCC', 'BTC'], ['RRT', 'USD'], ['RRT', 'BTC'], ['BCU', 'USD'], ['BCU', 'BTC']]
        endURL = ''
        for pair in all_pairs:
            endURL += 't' + pair[0] + pair[1] + ','
        baseURL = 'https://api.bitfinex.com/v2/tickers?symbols='

        dct = json2dct(baseURL + endURL)

        i = 0
        if dct is not False:
            for pair_info in dct:
                if pair_info[0] == 't' + all_pairs[i][0] + all_pairs[i][1]:
                    bid, ask = pair_info[1], pair_info[3]
                    pairs.append([all_pairs[i][1], all_pairs[i][0]])
                    rates.append([bid, ask])

                    i += 1

        if rates and pairs:
            load = True

    else:
        print("WARNING: {} is listed as an active exchange but info has not been imported".format(ExchangeName))

    if load is True:
        if print_cycles:
            print('Imported data from {} in \t {}'.format(ExchangeName, time() - t1))
        ExchangesInfo.append({'name': ExchangeName, 'pairs': pairs, 'rates': rates, 'CentralCoins': CentralCoins})
