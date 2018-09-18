import logging

from src.stats import HourData
from src.history import History

class Analysis:
    @staticmethod
    def should_post(history: History, stats: HourData, prices: list, threshold: float):
        if history.rising != stats.is_diff_positive:
            logging.info(f"Last change was in the opposite direction")
            return True

        # Hour change must reflect EMA change
        risen_hour = stats.cur_price > prices[1]
        if risen_hour != stats.is_diff_positive:
            logging.info("Hourly change does not agree with EMA change")
            return False

        if history.ema_reset:
            return True

        # Allow if increase is greater again
        logging.info("Price has not gone back within the EMA threshold since the last post")
        if history.rising:
            required_perc_diff = (1 + threshold / 100)
            threshold_sign_str = "above"
        else:
            required_perc_diff = (1 - threshold / 100)
            threshold_sign_str = "below"

        new_threshold = history.price * required_perc_diff
        logging.info(f"To post again the current price must be {threshold_sign_str}: {new_threshold:.0f}")
        if (history.rising and stats.cur_price > new_threshold) or \
                (not history.rising and stats.cur_price < new_threshold):
            logging.info(f"Beats new threshold price ({stats.cur_price:.0f}/{new_threshold:.0f})")
            return True
        else:
            logging.info(f"Does not beat new threshold price: ({stats.cur_price:.0f}/{new_threshold:.0f})")
            return False

    @staticmethod
    def ema_checks(stats: HourData, history: History, ema_threshold: float, reset_perc: float):
        if stats.ema_percent_diff_positive > ema_threshold:
            logging.info(f"Current price is outside threshold difference ({stats.formatted_info()})")
            return False

        logging.info(f"Current price not outside threshold ({stats.formatted_info()})")

        # If EMA hasn't been reset then check whether we should reset it
        if not history.ema_reset:
            if history.rising:
                target = history.price * (1 - reset_perc / 100)
                should_reset = stats.ema < target
            else:
                target = history.price * (1 + reset_perc / 100)
                should_reset = stats.ema > target

            if should_reset:
                logging.info("Resetting EMA")
                history.ema_reset = True
                history.save()

        return True
