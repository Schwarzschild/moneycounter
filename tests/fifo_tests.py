import unittest
import pandas as pd
from test_base import TradesBaseTest
from src.moneycounter import fifo, realized_gains


class FifoTests(TradesBaseTest):

    def test_fifo(self):
        year = 2022
        df, dt = self.get_df(year, a='ACCNT1', t='TICKER1')
        pnl = fifo(df, dt)
        self.assertAlmostEqual(pnl, 90)

    def test_realized(self):
        year = 2022
        df, _ = self.get_df(year)
        pnl = realized_gains(df, year)

        x = [(-20, 300), (10, 301), (-100, 300), (110, 301), (-7, 306), (7, 315)]
        a1t3 = sum([-i[0] * i[1] for i in x])

        expected = pd.DataFrame({'a': ['ACCNT1', 'ACCNT1', 'ACCNT2', 'ACCNT2'],
                                 't': ['TICKER1', 'TICKER3', 'TICKER1', 'TICKER2'],
                                 'realized': [90.0, a1t3, 190.0, 63.0]})
        pd.testing.assert_frame_equal(pnl, expected)


if __name__ == '__main__':
    unittest.main()
