from datetime import date, datetime
import pandas as pd
from .dt import our_localize
from .dt import day_start_next_day, day_start


def fifo(dfg, dt):
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
        quantity = row.q
        add_pnl = row['dt'] >= dt
        cs = row.cs
        price = row.p

        for j in range(n):
            buy_row = dfg.iloc[j]
            if buy_row.q <= 0.0001:
                continue

            q = -quantity
            if buy_row.q >= q:
                adj_q = q
            else:
                adj_q = buy_row.q

            if add_pnl:
                pnl += cs * adj_q * (price - buy_row.p)

            dfg.at[j, 'q'] = buy_row.q - adj_q
            quantity += adj_q
            dfg.at[n, 'q'] = quantity

            if quantity > 0.0001:
                break

        return pnl

    realized = 0
    dfg.reset_index(drop=True, inplace=True)
    for i in range(len(dfg)):
        row = dfg.iloc[i]
        if row.q < 0:
            pnl = realize_q(i, row)
            realized += pnl

    return realized


def stocks_sold(trades_df, year):
    # Find any stock sells this year
    t1 = day_start(date(year, 1, 1))
    t2 = day_start_next_day(date(year, 12, 31))
    mask = (trades_df['dt'] >= t1) & (trades_df['dt'] < t2) & (trades_df['q'] < 0)
    sells_df = trades_df.loc[mask]
    return sells_df


def realized_gains(trades_df, year):
    dt = our_localize(datetime(year, 1, 1))
    sells_df = stocks_sold(trades_df, year)
    a_t = sells_df.loc[:, ['a', 't']]
    a_t = a_t.drop_duplicates()

    # get only trades for a/t combos that had sold anything in the given year
    df = pd.merge(trades_df, a_t, how='inner', on=['a', 't'])

    # df['d'] = pd.to_datetime(df.dt).dt.date
    realized = df.groupby(['a', 't']).apply(fifo, dt).reset_index(name="realized")

    return realized
