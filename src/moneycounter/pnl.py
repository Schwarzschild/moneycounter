from datetime import date, datetime
import pandas as pd
from .dt import our_localize
from .dt import day_start_next_day, day_start
from .str_utils import is_near_zero


def find_sign_change(df, csum=None):
    """
    Calculate csum and find the last sign change.

    :param df:
    :return:
    """

    if csum is None:
        csum = df.q.cumsum()

    pos = csum.iat[-1]

    if pos > 0:
        flags = csum <= 0
    else:
        flags = csum >= 0

    i = df.index[0]
    if flags.any():
        i = df[flags][-1:].index[0] + 1

    return csum, pos, i


def separate_trades(df):
    """
    Return two dataframes: 1. realized trades; and 2. unrealized trades.

    :param df:
    :return realized_df, unrealized_df:

    Case 1
     q     csum   realized    unrealized
    +2      2        2            0
    -2      0       -2            0
    +10    10        6            4
    -5      5       -5            0
    +2      7        0            2
    +1      8        0            1
    -1      7       -1            0

    Case 2
    +2      2        0            2

    Case 3
     q     csum   realized    unrealized
    +10    10       10            0
    -5      5       -5            0
    -20   -15       -6          -14
    +1    -14        1            0
    -2    -16        0           -2
    +5    -11        5            0

    Case 4
         q     csum        q    csum       unrealized_q   realized_q
        +10    10          0     0            0              10
        -5      5          0     0            0              -5
     i -11     -6         -6    -6            0             -11
        -4    -10     =>  -4    -10     =>    0              -4
        -5    -15         -5    -15          -3              -2
       +12     -3          0    -15           0              12
        -1     -4         -1    -16          -1               0
                         q_sum = 12

    To find unrealized:
      Step 1
            Copy df to df_unrealized
            Find i at last csum sign change
            Set all q before i to zero
            Set q[i] = csum[i]

      Step 2
            q_sum = q[q > 0].sum()    Get sum of positive trades.
            Set q[q > 0] = 0          Zero out all positive trades.
            find csum
            Find first time csum <= -q_sum at j
            q[j] = csum[j] + q_sum


    df_realized = df - df_unrealized

    Remove all records where q=0 from both df_realized and df_unrealized

    """
    pos = df.q.sum()

    if is_near_zero(pos):
        unrealized_df = df.head(0)
        realized_df = df
    else:
        # Step 1
        unrealized_df = df.copy()
        csum, pos, i = find_sign_change(df)
        unrealized_df.loc[:i, 'q'] = 0.0
        unrealized_df.loc[i, 'q'] = csum.loc[i]

        # Step 2
        if pos >= 0:
            flags = unrealized_df.q < 0
            q_sum = unrealized_df[flags].q.sum()
            unrealized_df.loc[flags, 'q'] = 0

            csum = unrealized_df.q.cumsum()
            flags = csum >= -q_sum
            i = csum[flags].index[0]

            unrealized_df.loc[:i, 'q'] = 0.0
            unrealized_df.loc[i, 'q'] = csum.iat[i] + q_sum
        else:
            flags = unrealized_df.q > 0
            q_sum = unrealized_df[flags].q.sum()
            unrealized_df.loc[flags, 'q'] = 0

            csum = unrealized_df.q.cumsum()
            flags = csum <= -q_sum
            i = csum[flags].index[0]

            unrealized_df.loc[:i, 'q'] = 0.0
            unrealized_df.loc[i, 'q'] = csum.iat[i] + q_sum

        realized_df = df.copy()
        realized_df.q = df.q - unrealized_df.q

        realized_df = realized_df[realized_df.q != 0]
        unrealized_df = unrealized_df[unrealized_df.q != 0]

    return realized_df, unrealized_df


def pnl_calc(df, price=None):
    '''
    :param df:  Trades data frame
    :return: profit or loss
    '''
    if df.empty:
        return 0

    pnl = -(df.q * df.p).sum()
    if price:
        pnl += df.q.sum() * price

    cs = df.cs.iloc[0]
    pnl *= cs

    return pnl


def pnl(df, price=0):
    """
    Calculate FIFO PnL

    :param df: Pandas dataframe with single account and ticker
    :param price:     Closing price if there are unrealized trades
    :return:          realized pnl, unrealized pnl, total

    IMPORTANT NOTE: The default value for price of zero is only useful when there is no open position.
    """
    realized_df, unrealized_df = separate_trades(df)
    realized_pnl = pnl_calc(realized_df)
    unrealized_pnl = pnl_calc(unrealized_df)
    total = realized_pnl + unrealized_pnl

    return realized_pnl, unrealized_pnl, total


def wap_calc(df):

    _, df = separate_trades(df)

    if df.empty:
        return 0

    qp = df.q * df.p
    wap = qp.sum() / df.q.sum()

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


def stocks_traded(trades_df, year):
    # Find any stock sells this year
    t1 = day_start(date(year, 1, 1))
    t2 = day_start_next_day(date(year, 12, 31))
    mask = (trades_df['dt'] >= t1) & (trades_df['dt'] < t2)
    traded_df = trades_df.loc[mask]
    return traded_df


def realized_gains(trades_df, year):
    traded_df = stocks_traded(trades_df, year)
    traded_df = traded_df.loc[:, ['a', 't']]
    traded_df = traded_df.drop_duplicates()

    # get only trades for a/t combos that had sold anything in the given year
    df = pd.merge(trades_df, traded_df, how='inner', on=['a', 't'])

    if df.empty:
        pnl = pd.DataFrame(columns=['a', 't', 'realized'])
    else:
        pnl = df.groupby(['a', 't']).apply(realized_gains_one, year).reset_index(name="realized")

        # Eliminate zeros
        pnl = pnl.loc[pnl.realized != 0]
        pnl.reset_index(drop=True, inplace=True)

    return pnl
