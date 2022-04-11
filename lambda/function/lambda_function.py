import os
import logging
import jsonpickle
import boto3
import zipfile
import io

from botocore.exceptions import ClientError

from monitor import scan_next_week, format_timeslots
from mail import Emailer


logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("lambda")
client.get_account_settings()


def contains_new_court(last_email: str, email: str) -> bool:
    email_set = set(email.splitlines())
    last_email_set = set(last_email.splitlines())
    new_lines = email_set.difference(last_email_set)
    if len(new_lines) > 0:
        return True
    return False


def lambda_handler(event, context):
    logger.info("## EVENT\r" + jsonpickle.encode(event))
    logger.info("## CONTEXT\r" + jsonpickle.encode(context))

    try:
        with open("last_email.txt") as f:
            last_email = f.read().strip()
    except FileNotFoundError:
        logging.info("## NO last_email.txt FOUND, ASSUMING FIRST RUN")
        last_email = ""

    timesolts = scan_next_week(20, 12)
    logger.info("## TIMESLOTS\r" + jsonpickle.encode(timesolts))

    email = format_timeslots(timesolts)

    emailer = Emailer("mail_config.yml")

    if not contains_new_court(last_email, email):
        logger.info("## NO EMAIL SENT, NO NEW COURTS")
        return

    try:
        emailer.send_email("Hurray! Tennis courts are available!", email)
        logger.info("## EMAIL SENT")
    except ClientError as e:
        logger.exception("## EMAIL SEND FAILED")
        return

    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as zipf:
        # Write Python files into the zip
        for filename in os.listdir("."):
            if filename != "last_email.txt":
                zipf.write(filename)

        info = zipfile.ZipInfo("last_email.txt")
        info.external_attr = 0o644 << 16
        zipf.writestr(info, email)

    client.update_function_code(
        FunctionName="monitor-tennis", ZipFile=bio.getvalue(),
    )
    logger.info("## FUNCTION UPDATED")


def main() -> int:
    lambda_handler(None, None)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
