import json

class History:
    def __init__(self, file: str,):
        self.file_name = file
        print("Loading script history data")

        try:
            with open(file, "r") as file:
                # Read file
                data = json.loads(file.read())
                last_post = data['last_post']

                self.ema_reset = data['ema_reset']

                self.price = last_post['price']
                self.rising = last_post['rising']
                self.rising_str = "rising" if self.rising else "falling"

                self.loaded = True
        except IOError:
            print("Couldn't load file, using default values")
            self.ema_reset = True
            self.price = None
            self.rising = True
            self.rising_str = "ERR"
            self.loaded = False

    def save(self):
        print(f"Updating {self.file_name}")

        new_data = {
            'ema_reset': self.ema_reset,
            'last_post': {
                'price': self.price,
                'rising': self.rising
            }
        }

        with open(self.file_name, "w") as f:
            json.dump(new_data, f, indent=4)
