import os
import unittest
from datetime import datetime
import pandas as pd
from src.moneycounter.dt import our_localize


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
