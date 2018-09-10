class SlackColourThresholds:
    GOOD = 1
    NEUTRAL = 0
    WARNING = -1

class SlackImages:
    UP = "https://i.imgur.com/2PVZ0l1.png"
    DOWN = "https://i.imgur.com/21sDn3D.png"

    @classmethod
    def get_image(cls, up: bool):
        return cls.UP if up else cls.DOWN
