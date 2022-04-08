import os
import logging
import jsonpickle
import boto3
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

from monitor import scan_next_week, format_timeslots
from mail import Emailer

logger = logging.getLogger()
logger.setLevel(logging.INFO)
patch_all()

client = boto3.client("lambda")
client.get_account_settings()


def lambda_handler(event, context):
    logger.info("## ENVIRONMENT VARIABLES\r" + jsonpickle.encode(dict(**os.environ)))
    logger.info("## EVENT\r" + jsonpickle.encode(event))
    logger.info("## CONTEXT\r" + jsonpickle.encode(context))

    timesolts = scan_next_week(20, 12)
    logger.info("## TIMESLOTS\r" + jsonpickle.encode(timesolts))

    emailer = Emailer("mail_config.yml")
    emailer.send_email(
        "Hurray! Tennis courts are available!", format_timeslots(timesolts)
    )
    logger.info("## EMAIL SENT")

    response = client.get_account_settings()
    return response["AccountUsage"]
