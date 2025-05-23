"""This module is responsible for sending results as emails."""

from htpy import html, body, h3, p, ul, li, Element, div  # pylint: disable=no-name-in-module

from itk_dev_shared_components.smtp import smtp_util

from robot_framework import config
from robot_framework.sub_process.sap_process import MissingPaymentPerson
from robot_framework.sub_process.structura_process import Property, FrozenDebt


def join_email_divs(div_list: list[str]) -> str:
    """Join multiple div to a single html document string."""
    html_body = html[body[[[div[s] for s in div_list]]]]
    return str(html_body)


def format_results(property_: Property, owners: list[tuple[str, str]], frozen_debt: list[FrozenDebt], tax_data: list[tuple[str, str]], missing_payments: list[MissingPaymentPerson]) -> str:
    """Format inputs as a neat html div.

    Args:
        property: The property object.
        owners: A list of owners as tuples of cpr and names.
        frozen_debt: Frozen debt as a list FrozenDebt objects.
        tax_data: A list of tuples of text and amount.
        missing_payments: A list of Person objects.
        go_case_id: The id of the created case in Get Organised.

    Returns:
        A string containing the html div.
    """
    body_div = div[
        h3["Beliggenhed"],
        p[property_.location],

        h3["Ejendomsnummer"],
        p[property_.property_number],

        h3["Ejere"],
        (p[" | ".join(owner)] for owner in owners),

        h3["I-Lån"],
        _format_frozen_debt(frozen_debt),

        h3["Skattebidrag"],
        _create_list(tax_data),

        h3["Udeståender i SAP"],
        _format_missing_payments(missing_payments)
    ]

    return str(body_div)


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


def _format_frozen_debt(frozen_debt: list[FrozenDebt]) -> Element:
    """Helper function for creating a list of frozen debt."""
    if not frozen_debt:
        return _create_list(["Ingen poster"])
    frozen_debt_list = [[f.cpr, f.name, f.date_, f.amount, f.status] for f in frozen_debt]
    return _create_list(frozen_debt_list)


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


def send_email(receivers: list[str], address: str, go_case_id: str, html_body: str):
    """Send an email to the given list of receivers.

    Args:
        receivers: The receivers of the email.
        address: The relevant street address for the subject line.
        html_body: The html body of the email.
    """
    smtp_util.send_email(
        receiver=receivers,
        sender="itk-rpa@mkb.aarhus.dk",
        subject=f"Ejendomsoplysning: {address}, {go_case_id}",
        body=html_body,
        html_body=True,
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT
    )
