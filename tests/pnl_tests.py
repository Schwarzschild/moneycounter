import pandas as pd
from test_base import TradesBaseTest
from src.moneycounter.pnl import pnl, divide_trades, wap_calc


class PnLTests(TradesBaseTest):

    def test_pnl(self):
        year = 2023
        price = 305
        for a, t, expected_total, expected_realized in [['ACCNT1', 'TICKER4', 460, 10],
                                                        ['ACCNT1', 'TICKER1', 650, 700],
                                                        ['ACCNT2', 'TICKER1', 800, 800],
                                                        ['ACCNT2', 'TICKER2', 185, 207],
                                                        ['ACCNT1', 'TICKER3', -187, -199],
                                                        ['ACCNT1', 'TICKER5', -330.0, -330.0]]:

            expected_unrealized = expected_total - expected_realized
            df, dt = self.get_df(year, a=a, t=t)
            realized, unrealized, total = pnl(df, price=price)

            self.assertAlmostEqual(realized, expected_realized)
            self.assertAlmostEqual(unrealized, expected_unrealized)
            self.assertAlmostEqual(total, expected_total)

    def test_divide_trades(self):

        expected_realized_q = [2, -2, 6, -5, 0, 0 - 1]
        expected_unrealized_q = [4, 0, 2, 1, 0]

        df, _ = self.get_df(a='ACCNT5', t='TICKER7')
        realized_df, unrealized_df = divide_trades(df)
        realized_df_q = list(realized_df.q)
        unrealized_df_q = list(unrealized_df.q)

        self.assertListEqual(realized_df_q, expected_realized_q)
        self.assertListEqual(unrealized_df_q, expected_unrealized_q)

        # df, _ = self.get_df(a='ACCNT5', t='TICKER8')


    def test_wap(self):

        for a, t in (('ACCNT1', 'TICKER1'),
                     ('ACCNT1', 'TICKER3'),
                     ('ACCNT1', 'TICKER4'),
                     ('ACCNT1', 'TICKER5'),
                     ('ACCNT2', 'TICKER1'),
                     ('ACCNT2', 'TICKER2'),
                     ('ACCNT3', 'TICKER6'),
                     ('ACCNT4', 'TICKER6')):

            df, _ = self.get_df(a=a, t=t)

            position = df.q.sum()

            _, pl_expected, _ = pnl(df, 1.0)

            wap = wap_calc(df)

            pl_calculated = position * (1.0 - wap)

            self.assertAlmostEqual(pl_expected, pl_calculated)
