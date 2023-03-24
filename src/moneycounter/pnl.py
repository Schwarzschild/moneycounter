from datetime import date
import numpy as np
import pandas as pd
from tbgutils.dt import day_start_next_day, day_start
from tbgutils.str import is_near_zero


def split_adjust(df):
    """
    :param df:
    :return df:

    Adjust quantities and prices to account for split trades.
    Splits are identified by p=0
    Do this process on all trades before calling separate_trades()
    Better to add it to the beginning of separate_trades()

    Only adjust trades since the last zero position because if there is a gap in position
    there could have been more splits not recorded during that gap.  Without those the
    earlier adjustments would be incorrect.

    Note that if you use unrealized trades only you'll be sure not to include any trades before
    the last zero position.
    """

    df = df.copy()

    # Find location i of last split, spits are identified by p=0
    split_trades_flags = df.p <= 1e-10
    if not split_trades_flags.any():
        return df

    df['csum'] = df.q.cumsum()

    split_trades = df[split_trades_flags]

    for index, row in split_trades.iterrows():
        denominator = row.csum - row.q
        factor = row.csum / denominator
        df.iloc[:index].q *= factor
        df.iloc[:index].p /= factor

    df = df[~split_trades_flags]
    df.drop(['csum'], axis=1)

    df.reset_index(drop=True, inplace=True)

    return df


def fifo_remove(df):
    """
    Remove all trades that are closed out.
    Assume the input df position, i.e. cumsum, is always the same sign and not zero.
    i.e. All previous realized trades are removed.

    :param df:
    :return:

    Example:

    q    csum      q_new

    10    10
     5    15
   -12     3
    17    20
    10    30         10
   -20    10
    5     15          5

    The sum(q) = sum(q_new) = 15
    Left with only three rows

    """

    position = df.q.sum()
    if is_near_zero(position):
        df = df.head(0)
        return df

    if position < 0:
        df.q *= -1

    csum = df.q.cumsum()

    sells = df[df.q < 0]

    for index, row in sells.iterrows():
        q = -row.q
        flags = csum > q
        i = df[flags].index[0]
        df.q.iloc[:i] = 0
        residual = csum.iloc[i] - q
        if not is_near_zero(residual):
            df.at[i, 'q'] = residual
        df.at[index, 'q'] = 0

        csum = df.q.cumsum()

    df = df[df.q > 0]

    df.reset_index(drop=True, inplace=True)

    if position < 0:
        df.q *= -1

    return df


def find_sign_change(df, csum=None):
    """
    Calculate csum and find the last sign change.

    :param df:
    :return:

    raises IndexError if there are no sign changes.
    """

    if csum is None:
        csum = df.q.cumsum()

    pos = csum.iat[-1]

    if pos > 0:
        flags = csum <= 0
    else:
        flags = csum >= 0

    i = df[flags][-1:].index[0] + 1

    return csum, pos, i


def eliminate_before_sign_change(df):
    """
    Find last time csum pass through zero and remove all previous realized trades.
    :param df:
    :return:

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

    """

    # Step 1

    try:
        csum, pos, i = find_sign_change(df)
    except IndexError:
        return df

    df = df.copy()

    df.loc[:i, 'q'] = 0.0
    df.loc[i, 'q'] = csum.loc[i]

    df = df[df.q.abs() > 1e-10]

    df.reset_index(drop=True, inplace=True)

    return df


def unrealized(df):
    """
    Return a dataframe of split adjusted unrealized trades

    :param df:
    :return realized_df, unrealized_df:

    """

    pos = df.q.sum()

    if is_near_zero(pos):
        return df.head(0)

    unrealized_df = eliminate_before_sign_change(df)
    unrealized_df = split_adjust(unrealized_df)
    unrealized_df = fifo_remove(unrealized_df)

    unrealized_df = unrealized_df[unrealized_df.q != 0]

    return unrealized_df


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

    total = pnl_calc(df, price=price)
    unrealized_df = unrealized(df)
    unrealized_pnl = pnl_calc(unrealized_df, price=price)
    realized_pnl = total - unrealized_pnl

    return realized_pnl, unrealized_pnl, total


def wap_calc(df):

    df = unrealized(df)

    if df.empty:
        return 0

    qp = df.q * df.p
    wap = qp.sum() / df.q.sum()

    return wap


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
