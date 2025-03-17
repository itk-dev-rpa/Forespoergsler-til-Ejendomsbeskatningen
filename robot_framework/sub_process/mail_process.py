"""This module is responsible for sending results as emails."""

from htpy import html, body, h3, p, ul, li, Element  # pylint: disable=no-name-in-module

from itk_dev_shared_components.smtp import smtp_util

from robot_framework import config
from robot_framework.sub_process.sap_process import MissingPaymentPerson
from robot_framework.sub_process.structura_process import Property


def format_results(property_: Property, owners: list[tuple[str, str]], frozen_debt: list[tuple[str, str, str, str]], missing_payments: list[MissingPaymentPerson]) -> str:
    """Format inputs as a neat html body.

    Args:
        property: The property object.
        owners: A list of owners as tuples of cpr and names.
        frozen_debt: Frozen debt as a list of string tuples.
        missing_payments: A list of Person objects.

    Returns:
        A string containing the full html body.
    """
    html_body = html[
        body[
            h3["Beliggenhed"],
            p[property_.location],

            h3["Ejendomsnummer"],
            p[property_.property_number],

            h3["Ejere"],
            (p[" | ".join(owner)] for owner in owners),

            h3["Indefrossen grundskyld"],
            _create_list(frozen_debt) if frozen_debt else p["Ingen poster"],

            h3["Udeståender i SAP"],
            _format_missing_payments(missing_payments)
        ]
    ]

    return str(html_body)


def _create_list(content: list) -> Element:
    """Helper function to create an html list of the given content.
    If the content list contains other lists or tuples they are prettified.
    """
    result = []
    for v in content:
        if type(v) in (tuple, list):
            s = " | ".join(v)
        else:
            s = str(v)
        result.append(li[s])
    return ul[result]


def _format_missing_payments(missing_payments: list[MissingPaymentPerson]) -> Element:
    """Helper function to create nested lists based on a list of Person objects.

    Args:
        missing_payments: A list of Person objects.

    Returns:
        A nested html list.
    """
    return ul[
        (
            li[
                p.name,
                ul[
                    (
                        li[
                            c.title,
                            _create_list(c.entries) if c.entries else _create_list(["Ingen poster"]),
                        ]
                        for c in p.cases)
                ]
            ]
            for p in missing_payments)
    ]


def send_email(receivers: list[str], address: str, html_body: str):
    """Send an email to the given list of receivers.

    Args:
        receivers: The receivers of the email.
        address: The relevant street address for the subject line.
        html_body: The html body of the email.
    """
    smtp_util.send_email(
        receiver=receivers,
        sender="itk-rpa@mkb.aarhus.dk",
        subject=f"Ejendomsoplysning: {address}",
        body=html_body,
        html_body=True,
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT
    )
