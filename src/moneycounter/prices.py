import pandas as pd


def remove_closed_out_trades(trades_df):
    mask = trades_df.q.cumsum() == 0
    i = trades_df[mask].index[-1] + 1
    trades_df = trades_df[i:]
    trades_df.reset_index(drop=True, inplace=True)

    buys_df = trades_df[trades_df.q >= 0]
    total_buy_q = buys_df.q.sum()

    sells_df = trades_df[trades_df.q < 0]
    total_sell_q = -sells_df.q.sum()

    if total_buy_q > total_sell_q:
        mask = buys_df.q.cumsum() <= total_sell_q
        delta = buys_df[mask].q.sum()
        total_sell_q -= delta
        buys_df = buys_df[~mask]
        buys_df.reset_index(drop=True, inplace=True)
        if len(buys_df):
            buys_df.loc[0, 'q'] -= total_sell_q
        df = buys_df
    elif total_buy_q < total_sell_q:
        mask = sells_df.q.cumsum() <= -total_buy_q
        delta = sells_df[mask].q.sum()
        total_buy_q += delta
        sells_df = sells_df[~mask]
        sells_df.reset_index(drop=True, inplace=True)
        if len(sells_df):
            sells_df.loc[0, 'q'] += total_buy_q
        df = sells_df
    else:
        df = pd.DataFrame(columns=trades_df.columns)

    return df


def wap(trades_df):
    df = remove_closed_out_trades(trades_df)

    if df.empty:
        return None
    else:
        wap = (df.q * df.p).sum() / df.q.sum()

    return wap