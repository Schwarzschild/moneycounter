def fifo(dfg, d):
    """
    Calculate realized gains for sells later than d.
    Loop forward from bottom
       0. Initialize pnl = 0 (scalar)
       1. everytime we hit a sell
          a. if dfg.dt > dt: calculate and add it to pnl
          b. reduce q for sell and corresponding buy records.
    """

    # mask = (dfg.dt < dt) & (dfg.q > 0.0001)
    # buys = dfg.where(mask)

    def realize_q(n, row):
        pnl = 0

        for j in range(n):
            buy_row = dfg.iloc[j]
            if buy_row.q <= 0.0001:
                continue

            q = -row.q
            if buy_row.q >= q:
                adj_q = q
            else:
                adj_q = buy_row.q

            if row.d > d:
                pnl += row.cs * q * (row.p - buy_row.p)

            dfg.at[j, 'q'] = buy_row.q - adj_q
            dfg.at[n, 'q'] = row.q + adj_q
            row.q = dfg.iloc[n].q

            if row.q > 0.0001:
                break

        return pnl

    realized = 0
    for i in range(len(dfg)):
        row = dfg.iloc[i]
        if row.q < 0:
            pnl = realize_q(i, row)
            realized += pnl

    return realized
