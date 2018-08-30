import requests
import json

class Slack:
    @classmethod
    def post_to_slack(cls, name, icon, text, attachments, slack_url, channel=""):
        slack_data = {"username": name, "icon_url": icon, "text": text, "attachments": attachments, "channel": channel}
        response = "null"

        try:
            response = requests.post(slack_url, data=json.dumps(slack_data), headers={"content-type": "application/json"})
            if response.status_code != requests.codes.ok:
                cls.slack_error_msg(response, slack_data)
                return -1
        except requests.exceptions.ConnectionError as e:
            print("Connection refused")
            cls.slack_error_msg(response, slack_data)
            return -1
        except Exception as e:
            print("An exception occurred:")
            print(e)
            cls.slack_error_msg(response, slack_data)
            return -1

    @classmethod
    def slack_error_msg(cls, response, slack_data):
        print("An error occurred posting to slack")
        print("Response given:")
        print(response)
        print("Data sent:")
        print(slack_data)
