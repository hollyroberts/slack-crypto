from datetime import datetime

from notifier import SlackColourThresholds
from stats import TimeIntervalData
from coinbase import Currency

def format_stat(stat: TimeIntervalData, stats: TimeIntervalData, text_pretext: str, pretext=None):
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

def cur_time_hours():
    cur_time = datetime.utcnow()
    return cur_time.replace(minute=0, second=0, microsecond=0)
