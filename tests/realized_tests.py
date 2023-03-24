
import pandas as pd
from test_base import TradesBaseTest
from src.moneycounter.pnl import realized_gains


class Realized(TradesBaseTest):

    # def test_fifo(self):
    #     year = 2022
    #     df, dt = self.get_df(year, a='ACCNT1', t='TICKER1')
    #     pnl = fifo(df, dt)
    #     self.assertAlmostEqual(pnl, 90)

    def test_realized(self):
        year = 2022

        expected = pd.DataFrame({'a': ['ACCNT1', 'ACCNT1', 'ACCNT2', 'ACCNT2'],
                                 't': ['TICKER1', 'TICKER3', 'TICKER1', 'TICKER2'],
                                 'realized': [90.0, -60.0, 190.00, 63.0]})

        df, _ = self.get_df()
        df = df[df.a.isin(['ACCNT1', 'ACCNT2'])]
        pnl = realized_gains(df, year)
        pd.testing.assert_frame_equal(pnl, expected)

    def test_realized_none(self):
        year = 2025
        df, _ = self.get_df()
        pnl = realized_gains(df, year)
        self.assertTrue(pnl.empty)
