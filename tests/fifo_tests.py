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

        expected = pd.DataFrame({'a': ['ACCNT1', 'ACCNT1', 'ACCNT1', 'ACCNT2', 'ACCNT2'],
                                 't': ['TICKER1', 'TICKER3', 'TICKER5', 'TICKER1', 'TICKER2'],
                                 'realized': [90.0, 60.0, 0.0, 190.00, 63.0]})
        print(pnl.to_string())
        print(pnl.dtypes)
        print(expected.to_string())
        print(expected.dtypes)
        pd.testing.assert_frame_equal(pnl, expected)


if __name__ == '__main__':
    unittest.main()
