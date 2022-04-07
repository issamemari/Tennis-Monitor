import yagmail
import yaml


class Emailer:
    def __init__(self, config_file):
        with open(config_file, "r") as f:
            self.config = yaml.safe_load(f)

    def send_email(self, subject, body):
        for subscriber in self.config["subscribers"]:
            with yagmail.SMTP(self.config["user"], self.config["password"]) as yag:
                yag.send(subscriber, subject, body)
