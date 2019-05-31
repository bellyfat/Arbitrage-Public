import networkx as nx
# import logging
from time import time, sleep, strftime, localtime
from numpy import array
from math import log
# from itertools import islice
from more_itertools import unique_everseen
from collections import defaultdict

from exchanges import compile_ExchangesInfos
import history


# logging.basicConfig(filename='history/history.csv', level=logging.INFO, format='%(message)s')
print_cycles = True
log_history = False
run_continously = False


class Exchange:

    def __init__(self, name, pairs, rates, CentralCoins, fee=None):

        self.name = name
        self.pairs = pairs
        # self.fee = fee
        self.coins = unique_everseen(array(pairs).ravel())

        for coin in self.coins:
            if coin not in UniqueCoins and coin not in InactiveCoins:
                CoinNode(coin)
                UniqueCoins.append(coin)

        for coin in CentralCoins:
            CentralNode(coin, self)
            if not isFiat(coin):  # comment out to include Fiat to Fiat transfers
                Edge(CentralNodes[coin + self.name], CoinNodes[coin], 1.0)
                Edge(CoinNodes[coin], CentralNodes[coin + self.name], 1.0)

        for key, pair in enumerate(pairs):
            coin1_tick, coin2_tick = pair[0], pair[1]
            bid, ask = float(rates[key][0]), float(rates[key][1])

            if coin1_tick in InactiveCoins or coin2_tick in InactiveCoins \
                    or bid == 0 or ask == 0:
                continue

            if coin1_tick not in CentralCoins and coin2_tick not in CentralCoins:
                print("warning: pair: {} - {} in exchange: {} has not been considered".format(coin1_tick, coin2_tick, self.name))
                continue

            if coin1_tick in CentralCoins and coin2_tick in CentralCoins:

                if isFiat(coin1_tick) ^ isFiat(coin2_tick):

                    if isFiat(coin1_tick):
                        fiat = coin1_tick
                        crypto = coin2_tick
                    else:
                        fiat = coin2_tick
                        crypto = coin1_tick

                    Edge(CentralNodes[fiat + self.name], CoinNodes[crypto], rate=1 / ask)
                    Edge(CoinNodes[crypto], CentralNodes[fiat + self.name], rate=bid)

                elif isFiat(coin1_tick) is False and isFiat(coin2_tick) is False:

                    Edge(CentralNodes[coin1_tick + self.name], CoinNodes[coin2_tick], rate=1 / ask)
                    Edge(CoinNodes[coin1_tick], CentralNodes[coin2_tick + self.name], rate=1 / ask)

                    Edge(CoinNodes[coin2_tick], CentralNodes[coin1_tick + self.name], rate=bid)
                    Edge(CentralNodes[coin2_tick + self.name], CoinNodes[coin1_tick], rate=bid)

                else:
                    print('Central Fiat to Central Fiat not supported')

            else:

                if coin1_tick in CentralCoins:
                    coin1 = CentralNodes[coin1_tick + self.name]
                else:
                    coin1 = CoinNodes[coin1_tick]
                if coin2_tick in CentralCoins:
                    coin2 = CentralNodes[coin2_tick + self.name]
                else:
                    coin2 = CoinNodes[coin2_tick]

                Edge(coin1, coin2, rate=1 / ask)
                Edge(coin2, coin1, rate=bid)

        Exchanges[self.name] = self

    def __repr__(self):
        return "Exchange('{}', '{}')".format(self.name, self.pairs)


class Node:

    def __init__(self, coin):

        self.coin = coin
        self.isFiat = isFiat(coin)


class CentralNode(Node):

    def __init__(self, coin, exchange):
        super().__init__(coin)
        self.exchange = exchange
        self.fullname = coin + exchange.name

        CentralNodes[self.coin + self.exchange.name] = self

    def __repr__(self):
        # return "CN({}, {})".format(self.coin, self.exchange.name)
        return self.coin + '-' + self.exchange.name


class CoinNode(Node):

    def __init__(self, coin):
        super().__init__(coin)
        self.fullname = coin

        CoinNodes[coin] = self

    def __repr__(self):
        # return "N({})".format(self.coin)
        return self.coin


class Edge:

    def __init__(self, fr, to, rate):

        self.fr = fr
        self.to = to
        self.rate = float(rate)
        self.weight = -log(rate) + BIG
        if isinstance(self.fr, CentralNode):
            self.exchange = self.fr.exchange
        elif isinstance(self.to, CentralNode):
            self.exchange = self.to.exchange
        else:
            raise Exception("Edge from {} to {} does not pass through an exchange".format(self.fr.coin, self.to.coin))

        Edges[self.fr][self.to] = self

    def __repr__(self):

        return "E('{}', '{}', {}, {}, '{}')".format(
            self.fr.coin, self.to.coin, self.rate, self.weight, self.exchange.name)


def isFiat(ticker):
    FiatList = ['CNY', 'USD']
    if ticker in FiatList:
        return True
    else:
        return False


BIG = 40.0


while True:

    loop_start = time()

    Exchanges = {}
    CentralNodes = {}
    CoinNodes = {}
    Edges = defaultdict(dict)
    UniqueCoins = []

    InactiveCoins = []
    ExchangesStatus = {
        'bittrex': True,
        # 'jubi': True,
        # 'btc38': True,
        # 'yunbi': True,
        'gemini': True,
        'bitfinex': True
    }

    t1 = time()
    ExchangesInfo = []
    compile_ExchangesInfos(ExchangesStatus, ExchangesInfo)
    for ex in ExchangesInfo:
        Exchange(ex['name'], ex['pairs'], ex['rates'], ex['CentralCoins'])
    print('total runtime: \t \t \t \t \t', time() - t1)


    graph_start = time()
    G = nx.DiGraph()
    G.add_nodes_from(CentralNodes)
    G.add_nodes_from(CoinNodes)

    for FrNode, ToNode_edge in Edges.items():
        for ToNode, edge in ToNode_edge.items():
            G.add_edge(edge.fr, edge.to, object=edge, weight=edge.weight)

    # H = nx.DiGraph()
    # for key, node in CentralNodes.items():
    #     H.add_node(node.coin + node.exchange.name, type='central')
    # for key, node in CoinNodes.items():
    #     H.add_node(node.coin)

    # for FrNode, ToNode_edge in Edges.items():
    #     for ToNode, edge in ToNode_edge.items():
    #         fr = FrNode.coin
    #         to = ToNode.coin
    #         if isinstance(FrNode, CentralNode):
    #             fr = FrNode.coin + FrNode.exchange.name
    #         if isinstance(ToNode, CentralNode):
    #             to = ToNode.coin + ToNode.exchange.name

    #         H.add_edge(fr, to, weight=edge.rate)

    # nx.write_graphml(H, 'graphs/test2.graphml')

    All_Cycles_Profits = []

    ProfitableCycles = []
    ProfitableAmounts = []
    nCycles = 0

    PathsMatrix = defaultdict(dict)
    RatesMatrix = defaultdict(dict)
    for keyFr, FrNode in CentralNodes.items():
        for keyTo, ToNode in CentralNodes.items():
            if FrNode == ToNode:
                continue

            br_Nodes = [node for node in G.neighbors(FrNode) if node in G.neighbors(ToNode)]
            br_Rates = []

            for br_node in br_Nodes:
                br_Rates.append(G[FrNode][br_node]['object'].rate * G[br_node][ToNode]['object'].rate)

            brs_sorted = [[br_node, br_rate] for (br_rate, br_node)
                          in sorted(zip(br_Rates, br_Nodes), key=lambda pair: pair[0], reverse=True)]
            nCycles += len(brs_sorted)

            PathsMatrix[FrNode][ToNode] = []
            RatesMatrix[FrNode][ToNode] = []
            for bridge in brs_sorted:
                if len(RatesMatrix[FrNode][ToNode]) > 5:
                    break
                br_node, rate = bridge[0], bridge[1]
                PathsMatrix[FrNode][ToNode].append([FrNode, br_node, ToNode])
                RatesMatrix[FrNode][ToNode].append(rate)

    for key1, FrNode in CentralNodes.items():
        for key2, ToNode in CentralNodes.items():
            if key1 >= key2:
                continue

            for i in range(len(RatesMatrix[FrNode][ToNode])):
                for j in range(len(RatesMatrix[FrNode][ToNode])):

                    CycleProfit = RatesMatrix[FrNode][ToNode][i] * RatesMatrix[ToNode][FrNode][j]

                    All_Cycles_Profits.append([CycleProfit, PathsMatrix[FrNode][ToNode][i] + PathsMatrix[ToNode][FrNode][j]])

                    if CycleProfit > 1.0:
                        ProfitableCycles.append(PathsMatrix[FrNode][ToNode][i] + PathsMatrix[ToNode][FrNode][j])
                        ProfitableAmounts.append(CycleProfit)

    # for cycles_profits in All_Cycles_Profits:
    #     profit, cycle = cycles_profits[0], cycles_profits[1]
    #     line = str(loop_start) + ',' + str(profit) + ','
    #     for node in cycle:
    #         line += node.fullname + ' '
    #     logging.info(line)

    if log_history:
        history.writedb('history/log.db', All_Cycles_Profits, Exchanges, UniqueCoins, time())

        print('Logged cycles at {}'.format(strftime("%a, %d %b %Y %H:%M:%S -4000", localtime())))

    if print_cycles:
        print('Generated at {}'.format(strftime("%a, %d %b %Y %H:%M:%S -4000", graph_start)))
        print('Time to generate graph: {}'.format(time() - graph_start))

        print("Profitable Cycles:")
        cycles_sorted = [[cycle, profit] for (profit, cycle)
                         in sorted(zip(ProfitableAmounts, ProfitableCycles), key=lambda pair: pair[0], reverse=True)]
        for Cycle_Profit in cycles_sorted:
            cycle, profit = Cycle_Profit[0], Cycle_Profit[1]
            print(profit, '\t', cycle)

        for node in CentralNodes:
            print(node)

        print('{} of {} cycles profitable'.format(len(cycles_sorted), nCycles))

    if not run_continously:
        break
        elapsed = time() - loop_start
        if elapsed < 60:
            sleep(60 - elapsed)
