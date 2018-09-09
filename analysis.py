from stats import HourData
from history import History

class Analysis:
    @staticmethod
    def should_post(history: History, stats: HourData, prices: list, threshold: float):
        if history.rising != stats.is_diff_positive:
            print(f"Last change was in the opposite direction")
            return True

        # Hour change must reflect EMA change
        risen_hour = stats.cur_price > prices[1]
        if risen_hour != stats.is_diff_positive:
            print("Hourly change does not agree with EMA change")
            return False

        if history.ema_reset:
            return True

        # Allow if increase is greater again
        print("Price has not gone back within the EMA threshold since the last post")
        if history.rising:
            required_perc_diff = (1 + threshold / 100)
            threshold_sign_str = "above"
        else:
            required_perc_diff = (1 - threshold / 100)
            threshold_sign_str = "below"

        new_threshold = history.price * required_perc_diff
        print(f"To post again the current price must be {threshold_sign_str}: {new_threshold:.0f}")
        if (history.rising and stats.cur_price > new_threshold) or \
                (not history.rising and stats.cur_price < new_threshold):
            print(f"Beats new threshold price ({stats.cur_price:.0f}/{new_threshold:.0f})")
            return True
        else:
            print(f"Does not beat new threshold price: ({stats.cur_price:.0f}/{new_threshold:.0f})")
            return False
