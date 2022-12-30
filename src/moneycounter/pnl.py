from datetime import date, datetime
import pandas as pd
from .dt import our_localize
from .dt import day_start_next_day, day_start


def realized_trades(trades_df):
    """
    :param df:  Pandas dataframe with single account and ticker.
    :return: realized_df Pandas dataframe of realized trades.
    """

    df = trades_df.copy()

    buy_sum = df.where(df.q >= 0).q.sum()
    sell_sum = -df.where(df.q < 0).q.sum()
    delta = buy_sum - sell_sum

    # Start
    if buy_sum == sell_sum:
        realized_df = df
    if buy_sum > sell_sum:
        last_i = df.where(df.q < 0).index[-1]
        realized_df = df.head(last_i + 1)

        # A short loop to reduce last sell trades by delta
        for j in range(last_i, -1, -1):
            rec = realized_df.loc[j]
            q = rec.q
            if q > 0:
                if delta > q:
                    delta -= q
                    realized_df.at[j, 'q'] = 0
                else:
                    realized_df.at[j, 'q'] -= delta
                    break

    elif sell_sum > buy_sum:
        last_i = df.where(df.q >= 0).index[-1]
        realized_df = df.head(last_i + 1)

        # A short loop to reduce last sell trades by delta
        for j in range(last_i, -1, -1):
            rec = realized_df.loc[j]
            q = rec.q
            if q < 0:
                if delta < q:
                    delta -= q
                    realized_df.at[j, 'q'] = 0
                else:
                    realized_df.at[j, 'q'] -= delta
                    break

    realized_df.reset_index(drop=True, inplace=True)
    return realized_df


def pnl_calc(df, price=None):
    '''
    :param df:  Trades data frame
    :return: profit or loss
    '''
    if df.empty:
        return 0

    pnl = (-df.q * df.p).sum()
    if price:
        pnl += df.q.sum() * price

    cs = df.cs[0]
    pnl *= cs

    return pnl


def pnl(df, price=0):
    """
    Calculate FIFO PnL

    :param df: Pandas dataframe with single account and ticker
    :param price:     Closing price if there are unrealized trades
    :return:          realized pnl, unrealized pnl, total
    """
    realized_df = realized_trades(df)
    realized_pnl = pnl_calc(realized_df)
    total = pnl_calc(df, price=price)
    unrealized_pnl = total - realized_pnl

    return realized_pnl, unrealized_pnl, total


def wap_calc(df):
    '''
    total based on unrealized trades
    total = cs * pos * (price - wap)
    wap = price - total / cs / pos

    :param df: trades
    :return: wap
    '''

    if df.empty:
        return 0.0

    pos = df.q.sum()
    if pos == 0:
        return 0.0

    realized_pnl, unrealized_pnl, total = pnl(df)
    cs = df.cs[0]
    wap = -unrealized_pnl / cs / pos

    return wap


def fifo(dfg, dt):
    """
    Calculate realized gains for sells later than d.
    THIS ONLY WORKS FOR TRADES ENTERED AS LONG POSITIONS
    Loop forward from bottom
       0. Initialize pnl = 0 (scalar)
       1. everytime we hit a sell
          a. if dfg.dt > dt: calculate and add it to pnl
          b. reduce q for sell and corresponding buy records.
    """

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


def realized_gains_fifo(trades_df, year):
    #
    # Use this to find realized pnl for things sold this year
    #
    dt = our_localize(datetime(year, 1, 1))
    sells_df = stocks_sold(trades_df, year)
    a_t = sells_df.loc[:, ['a', 't']]
    a_t = a_t.drop_duplicates()

    # get only trades for a/t combos that had sold anything in the given year
    df = pd.merge(trades_df, a_t, how='inner', on=['a', 't'])

    # df['d'] = pd.to_datetime(df.dt).dt.date
    realized = df.groupby(['a', 't']).apply(fifo, dt).reset_index(name="realized")

    return realized


def realized_gains_one(trades_df, year):
    trades_df.reset_index(drop=True, inplace=True)
    t = day_start(date(year, 1, 1))
    df = trades_df[trades_df.dt < t]
    realized_prior, _, _ = pnl(df)

    t = day_start_next_day(date(year, 12, 31))
    df = trades_df[trades_df.dt < t]
    realized, _, _ = pnl(df)

    result = realized - realized_prior

    return result


def realized_gains(trades_df, year):
    pnl = trades_df.groupby(['a', 't']).apply(realized_gains_one, year).reset_index(name="realized")
    return pnl
