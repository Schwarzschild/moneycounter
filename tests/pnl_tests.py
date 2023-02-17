import pandas as pd
from test_base import TradesBaseTest
from src.moneycounter.pnl import pnl, wap_calc


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

    def test_wap(self):
        df, dt = self.get_df()
        expected = pd.DataFrame({'a': ['ACCNT1', 'ACCNT1', 'ACCNT1', 'ACCNT1',
                                       'ACCNT2', 'ACCNT2', 'ACCNT3', 'ACCNT4'],
                                 't': ['TICKER1', 'TICKER3', 'TICKER4', 'TICKER5',
                                       'TICKER1', 'TICKER2', 'TICKER6', 'TICKER6'],
                                 'wap': [307.6667, 306.5, 300.0, 300.0,
                                         300.5909, 306.5, 23.75, 291.1494]})

        wap = df.groupby(['a', 't']).apply(lambda x: wap_calc(x.reset_index())).reset_index(name="wap")
        print(f"Wap = {wap}")
        pd.testing.assert_frame_equal(wap, expected)

    def test_wap_with_split(self):
        df, dt = self.get_df(2022, a='ACCNT3', t='TICKER6')
        wap = wap_calc(df)
        self.assertAlmostEqual(wap, 23.75, places=4)
