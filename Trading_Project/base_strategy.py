import backtrader as bt


class BaseStrategy(bt.Strategy):

    def __init__(self, debug=True):
        """
        final signal: 1 -> long, 0 -> neutral ->, -1 sell
        """
        # To keep track of pending orders and buy price/commission
        self.countBuy = 0
        self.countSell = 0
        self.final_signal = None
        self.debug = debug

    def log(self, txt, dt=None):
        """Logging function fot this strategy"""
        if self.debug:
            dt_day = self.datas[0].datetime.date(0)
            dt_value = dt or self.datas[0].datetime.time(0)
            print("%sT%s, %s" % (dt_day, dt_value.isoformat(), txt))
        else:
            pass

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                if self.countSell > 0:
                    info_trade = "CLOSE SELL"
                    self.countSell -= 1
                else:
                    info_trade = "BUY EXECUTED"
                    self.countBuy += 1
                self.log(
                    f"{info_trade}, Price: %.2f, Cost: %.2f, Comm %.2ff"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                    )
                )
            else:
                if self.countBuy > 0:
                    info_trade = "CLOSE BUY"
                    self.countBuy -= 1
                else:
                    info_trade = "SELL EXECUTED"
                    self.countSell += 1
                self.log(
                    f"{info_trade}, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                    )
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None

    def execute(self) -> int:
        """
        Return final signal: 1 -> long, 0 -> neutral ->, -1 sell
        None if execute do not have any signal yet.
        """
        raise NotImplementedError

    def next(self):
        # cur_time = self.data.datetime.time(0)
        # if cur_time.hour < 10 or cur_time.hour >= 15:
        #     # Only trade after 9am
        #     return
        # if cur_time.hour == 12:
        #     # Sleep time
        #     return

        # if cur_time.hour == 14 and cur_time.minute >= 25:
        #     # Close end of the day
        #     if self.position:
        #         self.order = self.close()
        #     return
        # self.log('Close, %.2f' % self.dataclose[0])
        self.final_signal = self.execute()
        if self.final_signal is None:
            return

        if self.final_signal > 0:
            if self.position:
                if self.countSell:
                    self.order = self.close()
            else:
                self.order = self.buy()
                
        elif self.final_signal < 0:
            if self.position:
                if self.countBuy:
                    self.order = self.close()
            else:
                self.order = self.sell()



