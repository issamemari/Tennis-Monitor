import os
import logging
import jsonpickle
import boto3
import contextlib
import zipfile
import io

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

from monitor import scan_next_week, format_timeslots
from mail import Emailer

logger = logging.getLogger()
logger.setLevel(logging.INFO)
patch_all()

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
        last_email = ""

    timesolts = scan_next_week(20, 12)
    logger.info("## TIMESLOTS\r" + jsonpickle.encode(timesolts))

    email = format_timeslots(timesolts)

    emailer = Emailer("mail_config.yml")

    if contains_new_court(last_email, email):
        emailer.send_email(
            "Hurray! Tennis courts are available!", email,
        )
        logger.info("## EMAIL SENT")
    else:
        logger.info("## NO EMAIL SENT")

    with contextlib.suppress(OSError):
        with open("last_email.txt", "w") as f:
            f.write(email)
    logger.info("## NEW EMAIL SAVED")

    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as zipf:
        info = zipfile.ZipInfo("last_email.txt")
        info.external_attr = 0o644 << 16
        zipf.writestr(info, email)

        for file in os.listdir("."):
            zipf.write(file)

    client.update_function_code(
        FunctionName="monitor-tennis", ZipFile=bio.getvalue(),
    )
    logger.info("## FUNCTION UPDATED")

    response = client.get_account_settings()
    return response["AccountUsage"]
