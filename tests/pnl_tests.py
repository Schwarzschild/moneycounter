
from test_base import TradesBaseTest
from src.moneycounter.pnl import unrealized, wap_calc, pnl_calc, split_adjust, fifo_remove, pnl


class PnLTests(TradesBaseTest):

    def test_pnl(self):
        for a, t, r, u in (('ACCNT1', 'TICKER1', 700, -3090),
                           ('ACCNT1', 'TICKER3', -199.0, 1836),
                           ('ACCNT1', 'TICKER4', 10, -26910),
                           ('ACCNT1', 'TICKER5', -330, 0),
                           ('ACCNT2', 'TICKER1', 800, 0),
                           ('ACCNT2', 'TICKER2', 207, -3670),
                           ('ACCNT3', 'TICKER6', 996.42857, -251.42857),
                           ('ACCNT4', 'TICKER6', -84749.716, -27871.153846),
                           ('ACCNT5', 'CASE1', -1468.788, -3490.0484),
                           ('ACCNT5', 'CASE2', 0, -1378.0),
                           ('ACCNT5', 'CASE3', 133.84999, 7679.9688),
                           ('ACCNT5', 'CASE4', -1660.8076, 1858.6712),
                           ('ACCNT5', 'CASE5', 2040.51, -1289.1176)):

            df, _ = self.get_df(a=a, t=t, year=2025)
            realized_pnl, unrealized_pnl, total = pnl(df, 1.0)
            print(a, t, realized_pnl, unrealized_pnl)
            self.assertAlmostEqual(realized_pnl, r, places=3, msg=f"{a} {t}")
            self.assertAlmostEqual(unrealized_pnl, u, places=3, msg=f"{a} {t}")

    def test_wap(self):

        for a, t, wap_expected in (('ACCNT1', 'TICKER1', 310),
                                   ('ACCNT1', 'TICKER3', 307),
                                   ('ACCNT1', 'TICKER4', 300),
                                   ('ACCNT1', 'TICKER5', 0),
                                   ('ACCNT2', 'TICKER1', 0),
                                   ('ACCNT2', 'TICKER2', 306.83333),
                                   ('ACCNT3', 'TICKER6', 13.571),
                                   ('ACCNT4', 'TICKER6', 112.4846),
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
        q_sum_before = df.q.sum()

        unrealized_df = unrealized(df)

        q_sum_after = unrealized_df.q.sum()

        self.assertAlmostEqual(q_sum_before, q_sum_after, msg='Check sum preservation.')

        u = pnl_calc(unrealized_df, p)

        wap = wap_calc(df)
        self.assertAlmostEqual(wap, expected, places=3)

        u_wap = df.q.sum() * (p - wap)
        self.assertAlmostEqual(u_wap, u, places=3, msg='wap_with_split() pnl error.')

    def test_wap_with_split(self):
        """
         6 750
         6   0  (Split 2:1)
        -1 300
        """

        self.wap_with_split(a='ACCNT5', expected=22.5)
        self.wap_with_split(a='ACCNT6', expected=0.25)
        self.wap_with_split(a='ACCNT7', expected=112.259)
        self.wap_with_split(a='ACCNT8', expected=68.4940528)

    def fifo_remove_helper(self, a):
        df, _ = self.get_df(a=a, t='FIFO')
        position_before = df.q.sum()
        df = fifo_remove(df)
        position_after = df.q.sum()

        self.assertAlmostEqual(position_before, position_after)

        if position_before > 0:
            flag = df.q <= 0
        else:
            flag = df.q >= 0
        flag = flag.any()
        self.assertFalse(flag, msg='Make sure closed trades were removed.')

    def test_fifo_remove(self):
        self.fifo_remove_helper('ACCNT7')
        self.fifo_remove_helper('ACCNT8')
