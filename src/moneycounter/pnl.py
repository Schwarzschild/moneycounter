from datetime import date, datetime
import pandas as pd
from .dt import our_localize
from .dt import day_start_next_day, day_start
from .str_utils import is_near_zero


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
    realized_df = realized_trades(df)
    realized_pnl = pnl_calc(realized_df)
    total = pnl_calc(df, price=price)
    unrealized_pnl = total - realized_pnl

    return realized_pnl, unrealized_pnl, total


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


def divide_trades(df):
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
         q     csum   realized    unrealized
        +10    10       10            0
        -5      5       -5            0
     i -11     -6       -11           0
        -4    -10       -4            0
        -5    -15       -2           -3
       +12     -3       12            0
        -1     -4        0           -1

    To find unrealized:

    Copy df to df_unrealized
    Find i at last csum sign change
    Set all q before i to zero
    Let Q_pos = sum(positive trades after i), or negative values if position is positive.
    Set all positive q after i to zero
    Find csum
    Subtract Q from all csum entries
    Set q at i to csum at i: i.e. the -5 becomes a -3

    df_realized = df - df_unrealized

    Remove all records where q=0 from both df_realized and df_unrealized

    """
    pos = df.q.sum()

    if is_near_zero(pos):
        unrealized_df = df.head(0)
        realized_df = df
    else:

        unrealized_df = df.copy()
        csum, pos, i = find_sign_change(df)
        unrealized_df.q[:i] = 0
        flags = unrealized_df.q > 0
        if pos >= 0:
            q_neg = unrealized_df[flags].q.sum()
            unrealized_df[flags].q = 0
            unrealized_df[~flags].q -= q_neg
        else:
            q_pos = unrealized_df[~flags].q.sum()
            unrealized_df[~flags].q = 0
            unrealized_df[flags].q -= q_pos

        unrealized_df.loc[i, 'q'] = csum.iat[i]

        realized_df = df.copy()
        realized_df.q = df.q - unrealized_df.q

        realized_df = realized_df[realized_df.q != 0]
        unrealized_df = unrealized_df[unrealized_df.q != 0]

    return realized_df, unrealized_df


def remove_old_trades(df):
    """
    Remove all trades before the last time the position changed sign.


    :param df:
    :return:
    """
    qsum = df.q.cumsum()
    pos = qsum.iat[-1]

    if is_near_zero(pos):
        df = df.head(0)
    else:
        try:
            # Eliminate all rows since the last time the pos was negative.
            if pos > 0:
                i = df[qsum <= 0][-1:].index[0]
            else:
                i = df[qsum >= 0][-1:].index[0]

            if is_near_zero(qsum[i]):
                i += 1

            df = df[i:]
            df.reset_index(drop=True, inplace=True)

            qsum = qsum[i:]

            # df.loc[0, 'q'] = df.loc[0, 'qsum']
            df.loc[0, 'q'] = qsum.iat[0]
        except IndexError:
            # Nothing to eliminate
            pass

    return df


def wap_calc(df):
    """
    Calculated the Weighted Average Price
    Assumption: df is in chronological order.

    :param df:
    :return wap:

    Calculate equivalent entry price for the current position such that the
    PnL can be calculated with this formula:

    PnL = position * contract_size * (price - wap)

    where:
        position is the current position
        contract_size is the number of shares per contract, typically 1 for stocks
        price is the current price
        wap is the weighted average price calculated by this method.


    """

    position = df.q.sum()
    if is_near_zero(position):
        return 0.0

    cs = df.loc[0, 'cs']
    df = df[['q', 'p', 'cs']]
    df = remove_old_trades(df)
    _, pl, _ = pnl(df, price=1.0)
    wap = 1.0 - pl / position / cs

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
