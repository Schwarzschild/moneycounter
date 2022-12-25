
from test_base import TradesBaseTest
from src.moneycounter.pnl import pnl


class PnLTests(TradesBaseTest):

    def test_pnl(self):
        year = 2023
        df, dt = self.get_df(year, a='ACCNT1', t='TICKER3')
        realized, unrealized, wap, total = pnl(df, price=300)
        self.assertAlmostEqual(realized, -1942.0)
        self.assertAlmostEqual(unrealized, 2347.0)
