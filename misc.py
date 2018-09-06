from datetime import datetime

from constants import SlackColourThresholds
from stats import HourData
from coinbase import Currency
from history import History

class Misc:
    @staticmethod
    def should_post(history: History, stats: HourData, threshold: float):
        if history.rising != stats.is_diff_positive:
            print(f"Last change was in the opposite direction")
            return True

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

    @staticmethod
    def format_stat(stat: HourData, stats: HourData, text_pretext: str, pretext=None):
        diff = stats.cur_price - stat.cur_price
        diff /= stat.cur_price
        diff *= 100

        if diff > SlackColourThresholds.GOOD:
            colour = "good"
        elif diff > SlackColourThresholds.NEUTRAL:
            colour = ""
        elif diff > SlackColourThresholds.WARNING:
            colour = "warning"
        else:
            colour = "danger"

        text = f"{text_pretext}{Currency.SECONDARY_CURRENCY_SYMBOL}{stat.cur_price:,.0f} ({diff:+.2f}%)"
        attachment = {"fallback": "some price changes", "text": text, "color": colour}
        if pretext is not None:
            attachment['pretext'] = pretext

        return attachment

    @staticmethod
    def cur_time_hours():
        cur_time = datetime.utcnow()
        return cur_time.replace(minute=0, second=0, microsecond=0)
