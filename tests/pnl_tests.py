
from test_base import TradesBaseTest
from src.moneycounter.pnl import separate_trades, wap_calc, pnl_calc


class PnLTests(TradesBaseTest):

    def _assert_lists_almost_equal(self, a, b):
        self.assertEqual(len(a), len(b))
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y)

    def test_divide_trades(self):

        expected = [['CASE1', [4, 2, 1], [2, -2, 6, -5, -1]],
                    ['CASE2', [2], []],
                    ['CASE3', [-10, -1, -2], [10, -5, -10, 5]],
                    ['CASE4', [-3, -1], [10, -5, -11, -4, -2, 12]],
                    ['CASE5', [3, 1], [-10, 5, 11, 4, 2, -12]]]

        for case, expected_unrealized_q, expected_realized_q in expected:
            df, _ = self.get_df(a='ACCNT5', t=case)
            realized_df, unrealized_df = separate_trades(df)
            realized_df_q = list(realized_df.q)
            unrealized_df_q = list(unrealized_df.q)
            try:
                self._assert_lists_almost_equal(realized_df_q, expected_realized_q)
            except AssertionError:
                raise AssertionError(f"AssertionError {case} {realized_df_q} not equal to {expected_realized_q}")

            try:
                self._assert_lists_almost_equal(unrealized_df_q, expected_unrealized_q)
            except AssertionError:
                raise AssertionError(f"AssertionError {unrealized_df_q} not equal to {expected_unrealized_q}")

    def test_pnl(self):
        for a, t in (('ACCNT1', 'TICKER1'),
                     ('ACCNT1', 'TICKER3'),
                     ('ACCNT1', 'TICKER4'),
                     ('ACCNT1', 'TICKER5'),
                     ('ACCNT2', 'TICKER1'),
                     ('ACCNT2', 'TICKER2'),
                     ('ACCNT3', 'TICKER6'),
                     ('ACCNT4', 'TICKER6'),
                     ('ACCNT5', 'CASE1'),
                     ('ACCNT5', 'CASE2'),
                     ('ACCNT5', 'CASE3'),
                     ('ACCNT5', 'CASE4'),
                     ('ACCNT5', 'CASE5')):

            df, _ = self.get_df(a=a, t=t, year=2025)
            realized_df, unrealized_df = separate_trades(df)
            r = pnl_calc(realized_df)
            u = pnl_calc(unrealized_df, 1.0)
            t = pnl_calc(df, 1.0)
            total = r + u
            self.assertAlmostEqual(t, total, places=3, msg=f"{a} {t}")

    def test_wap(self):

        for a, t, wap_expected in (('ACCNT1', 'TICKER1', 310),
                                   ('ACCNT1', 'TICKER3', 307),
                                   ('ACCNT1', 'TICKER4', 300),
                                   ('ACCNT1', 'TICKER5', 0),
                                   ('ACCNT2', 'TICKER1', 0),
                                   ('ACCNT2', 'TICKER2', 306.83333),
                                   ('ACCNT3', 'TICKER6', 75.0),
                                   ('ACCNT4', 'TICKER6', 26.3695),
                                   ('ACCNT5', 'CASE1', 499.578342),
                                   ('ACCNT5', 'CASE2', 690),
                                   ('ACCNT5', 'CASE3', 591.766830),
                                   ('ACCNT5', 'CASE4', 465.6678),
                                   ('ACCNT5', 'CASE5', 323.2794),
                                   ):

            df, _ = self.get_df(a=a, t=t, year=2025)

            wap = wap_calc(df)
            # print(f"{a} {t} {wap} {wap_expected}")
            self.assertAlmostEqual(wap, wap_expected, places=3, msg=f"{a} {t}")

    def wap_with_split(self, a, t='SPLIT', expected=0):
        p = 1.0

        df, _ = self.get_df(a=a, t=t)
        _, unrealized_df = separate_trades(df)
        u = pnl_calc(unrealized_df, p)

        wap = wap_calc(df)
        self.assertAlmostEqual(wap, expected, places=3)

        u_wap = df.q.sum() * (p - wap)
        self.assertAlmostEqual(u_wap, u, places=3)

    def test_wap_with_split(self):
        """
         6 750
         6   0  (Split 2:1)
        -1 300
        """

        self.wap_with_split(a='ACCNT5', expected=11.25)
        self.wap_with_split(a='ACCNT6', expected=0.25)
        self.wap_with_split(a='ACCNT7', expected=158.315)
        self.wap_with_split(a='ACCNT8', expected=111.821)
