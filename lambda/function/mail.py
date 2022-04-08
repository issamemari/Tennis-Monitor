import yagmail
import yaml
import boto3

import email.message


class Emailer:
    def __init__(self, config_file):
        with open(config_file, "r") as f:
            self.config = yaml.safe_load(f)
        self.ses_client = boto3.client('ses')

    def send_email(self, subject, body):
        msg = email.message.EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.config["user"]
        msg.set_content(body)

        self.ses_client.send_raw_email(
            Source=self.config["user"],
            Destinations=self.config["subscribers"],
            RawMessage={'Data': msg.as_string()},
        )
