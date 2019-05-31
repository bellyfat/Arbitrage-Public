import sqlite3


def writedb(database, cycles, exchanges, uniqueCoins, time):
    conn = sqlite3.connect(database)
    c = conn.cursor()

    # create exchange dictionary
    c.execute('SELECT id, name FROM exchange')
    exchanges_table = c.fetchall()
    exchanges_id_tick = {}
    for row in exchanges_table:
        exchanges_id_tick[row[0]] = row[1]

    for exchange in exchanges:
        if exchange not in exchanges_id_tick.values():
            t = (exchange,)
            c.execute('INSERT INTO exchange (name) VALUES (?)', t)
            exchanges_id_tick[max(exchanges_id_tick.keys()) + 1] = exchange

    # create coin dictionary
    c.execute('SELECT id, tick FROM coin')
    coins_table = c.fetchall()
    coins_id_tick = {}
    for row in coins_table:
        coins_id_tick[row[0]] = row[1]

    for coin in uniqueCoins:
        if coin not in coins_id_tick.values():
            t = (coin,)
            c.execute('INSERT INTO coin (tick) VALUES (?)', t)
            coins_id_tick[max(coins_id_tick.keys()) + 1] = coin

    # create cycle ditionary and write to history table
    c.execute('SELECT id, route FROM cycle')
    cycles_table = c.fetchall()
    cycles_id_route = {}
    for row in cycles_table:
        cycles_id_route[row[0]] = row[1]

    cycles_entries = []
    for cycle in cycles:
        profit, route = cycle[0], cycle[1]

        if str(route) in cycles_id_route.values():
            cycle_id = list(cycles_id_route.keys())[list(cycles_id_route.values()).index(str(route))]

        else:
            t = str(route), \
                route[0].exchange.name, route[2].exchange.name, \
                route[0].coin, route[1].coin, route[2].coin, route[4].coin
            c.execute('INSERT INTO cycle \
                (route, exchange0, exchange2, coin0, coin1, coin2, coin3) VALUES \
                (?, ?, ?, ?, ?, ?, ?)', t)

            t = (str(route),)
            c.execute('SELECT id FROM cycle WHERE route=?', t)
            cycle_id = c.fetchall()[0][0]
            cycles_id_route[cycle_id] = (profit, str(route))

        cycles_entries.append((time, profit, cycle_id))

    c.executemany('INSERT INTO history (time, profit, cycle) VALUES (?, ?, ?)', cycles_entries)

    conn.commit()
    conn.close()
