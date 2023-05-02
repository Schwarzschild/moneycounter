import os
import unittest
from datetime import datetime
import numpy as np
import pandas as pd
from tbgutils.dt import our_localize


def fake_trades(n=100):
    df = pd.DataFrame(columns=['dt', 'q', 'p', 'cs', 't', 'a'])

    df['dt'] = pd.to_datetime(np.arange(1, n * 1e9, 1e9))
    df['q'] = np.random.randint(-1, 2, size=n)
    df['p'] = 100 + np.random.random(size=n) * 30
    df['cs'] = np.full(n, 1)
    df['t'] = np.full(n, 'TICKER')
    df['a'] = np.full(n, 'ACCOUNT')

    return df


class TradesBaseTest(unittest.TestCase):
    def setUp(self, a=None, t=None):
        fn = os.path.join(os.path.dirname(__file__), 'trades.csv')
        df = pd.read_csv(fn, parse_dates=['dt'])

        self.df = df

    def get_df(self, year=2022, a=None, t=None):
        dt = our_localize(datetime(year, 1, 1))
        eoy = our_localize(datetime(year, 12, 31, 23, 59, 59))
        # dt = pd.Timestamp(dt, tz='UTC')
        df = self.df
        if a is not None:
            df = df[df.a == a]
        if t is not None:
            df = df[df.t == t]

        df = df[df.dt <= eoy]
        df.reset_index(drop=True, inplace=True)
        df = df.sort_values(by=['dt'], ascending=True, ignore_index=True)
        return df, dt
