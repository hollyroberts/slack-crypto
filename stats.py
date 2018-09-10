class Stats:
    @staticmethod
    def sma(data, window):
        if len(data) < window:
            return None
        return sum(data[-window:]) / float(window)

    @classmethod
    def ema(cls, data, window):
        if len(data) < 2 * window:
            raise ValueError("data is too short")
        c = 2.0 / (window + 1)
        current_ema = cls.sma(data[-window * 2: -window], window)
        for value in data[-window:]:
            current_ema = (c * value) + ((1 - c) * current_ema)
        return current_ema

"""Data class to calculate stats from basic input data"""
class HourData:
    def __init__(self, price_data, ema_num_hours, offset: int = 0):
        if offset > 0:
            price_data = price_data[offset:]

        cur_price = price_data[0]
        ema = Stats.ema(price_data[::-1], ema_num_hours)

        diff = cur_price - ema
        percent_diff = diff / ema
        percent_diff *= 100

        # Set local variables to self variables
        self.cur_price = cur_price
        self.ema = ema
        self.ema_percent_diff = percent_diff
        self.ema_percent_diff_positive = abs(percent_diff)
        self.diff = diff
        self.is_diff_positive = diff > 0

    def formatted_info(self):
        return f"{self.cur_price:.0f}/{self.ema:.0f} - {self.ema_percent_diff_positive:.1f}%"
