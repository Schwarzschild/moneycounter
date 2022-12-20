import unittest
import datetime
from datetime import date
import pandas as pd
from src.pnl import fifo


class FifoTests(unittest.TestCase):
    def setUp(self):
        d = [date(2020, 3, 22),
             date(2020, 4, 25),
             date(2021, 10, 22),
             date(2021, 10, 25),
             date(2021, 10, 26),
             date(2022, 1, 6),
             date(2022, 2, 6),
             date(2022, 3, 6),
             date(2023, 2, 9),
             date(2023, 3, 7)]

        self.df = pd.DataFrame({'d': d,
                                'q': [100, -10, 100, -190, 10, 10, -10.0, 10.0, -1, -9],
                                'p': [300, 301, 300, 301, 306, 307, 315, 310, 330, 350],
                                'cs': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]})

    def test_fifo(self):
        year = 2022
        dt = datetime.datetime(year, 1, 1)
        eoy = datetime.date(year, 12, 31)
        dt = pd.Timestamp(dt, tz='UTC')
        df = self.df
        df = df[df.d <= eoy]
        pnl = fifo(df, dt.date())
        self.assertAlmostEqual(pnl, 90)


if __name__ == '__main__':
    unittest.main()
