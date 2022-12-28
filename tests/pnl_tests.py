
from test_base import TradesBaseTest
from src.moneycounter.pnl import pnl


class PnLTests(TradesBaseTest):

    def test_pnl(self):
        year = 2023


        price = 305
        for a, t, expected_total, expected_realized in [['ACCNT1', 'TICKER4', 460, 10],
                                                        ['ACCNT1', 'TICKER1', 650, 700],
                                                        ['ACCNT2', 'TICKER1', 800, 800],
                                                        ['ACCNT2', 'TICKER2', 185, 207],
                                                        ['ACCNT1', 'TICKER3', -187, 199]]:
            expected_unrealized = expected_total - expected_realized
            df, dt = self.get_df(year, a=a, t=t)
            realized, unrealized, total = pnl(df, price=price)

            self.assertAlmostEqual(realized, expected_realized)
            self.assertAlmostEqual(unrealized, expected_unrealized)
            self.assertAlmostEqual(total, expected_total)
