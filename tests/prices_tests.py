from test_base import TradesBaseTest
from src.moneycounter.prices import wap


class PricesTests(TradesBaseTest):
    def test_wap(self):
        df, _ = self.get_df(year=2023, a='ACCNT1', t='TICKER1')
        p = wap(df)
        self.assertAlmostEqual(p, 310)

        df, _ = self.get_df(year=2023, a='ACCNT2', t='TICKER1')
        p = wap(df)
        self.assertIsNone(p)

        df, _ = self.get_df(year=2023, a='ACCNT2', t='TICKER2')
        p = wap(df)
        self.assertAlmostEqual(p, 306.8333333333333)

        df, _ = self.get_df(year=2023, a='ACCNT1', t='TICKER3')
        p = wap(df)
        self.assertAlmostEqual(p, 306.8333333333333)
