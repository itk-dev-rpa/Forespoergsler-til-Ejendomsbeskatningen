
from htpy import html, body, h3, p, ul, li, Element

from itk_dev_shared_components.smtp import smtp_util

from robot_framework import config
from robot_framework.sub_process.sap_process import MissingPaymentPerson, MissingPaymentCase, MissingPaymentEntry
from robot_framework.sub_process.structura_process import Property


def format_results(property: Property, owners: list[tuple[str, str]], frozen_debt: list[tuple[str, str, str, str]], missing_payments: list[MissingPaymentPerson]) -> str:
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
            p[property.location],

            h3["Ejendomsnummer"],
            p[property.property_number],

            h3["Ejere"],
            _create_list(owners),

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
        sender="robot@friend.dk",
        subject=f"Ejendomsoplysning: {address}",
        body=html_body,
        html_body=True,
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT
    )


if __name__ == '__main__':
    raw_result = '814186,7230,Skejbygårdsvej 46, 3.   TH,,8240,777159,0,Mumle bumle humle'
    property_number = '814186'
    owners = [
        ('1234567891', 'Mumle bumle humle'),
        ('2345678954', 'Ibii tippe dibbi')
    ]
    frozen_debt = [
        ("hej", "med", "dig", "du")
    ]
    missing_payments = [
        MissingPaymentPerson(
            name='Mumle bumle humle',
            cpr='1234567891',
            cases=[
                MissingPaymentCase(
                    title='EJEN E...418608 Skejbygårdsvej 46 0',
                    entries=[
                        MissingPaymentEntry(
                            title="Renter",
                            status="Fucking betalt",
                            amount=500.23
                        ),
                        MissingPaymentEntry(
                            title="Blabla geybur",
                            status="Noget andet",
                            amount=123
                        )
                    ]
                ),
                MissingPaymentCase(
                    title='EJEN E...418608 Skejbygårdsvej 46 0',
                    entries=[
                        MissingPaymentEntry(
                            title="Renter",
                            status="Fucking betalt",
                            amount=500.23
                        ),
                        MissingPaymentEntry(
                            title="Blabla geybur",
                            status="Noget andet",
                            amount=123
                        )
                    ]
                )
            ]
        ),
        MissingPaymentPerson(
            name='Mumle bumle humle',
            cpr='1234567891',
            cases=[
                MissingPaymentCase(
                    title='EJEN E...418608 Skejbygårdsvej 46 0',
                    entries=[
                        MissingPaymentEntry(
                            title="Renter",
                            status="Fucking betalt",
                            amount=500.23
                        ),
                        MissingPaymentEntry(
                            title="Blabla geybur",
                            status="Noget andet",
                            amount=123
                        )
                    ]
                ),
                MissingPaymentCase(
                    title='EJEN E...418608 Skejbygårdsvej 46 0',
                    entries=[
                        MissingPaymentEntry(
                            title="Renter",
                            status="Fucking betalt",
                            amount=500.23
                        ),
                        MissingPaymentEntry(
                            title="Blabla geybur",
                            status="Noget andet",
                            amount=123
                        )
                    ]
                )
            ]
        )
    ]

    html_body = format_results(
        raw_result=raw_result,
        property_number=property_number,
        owners=owners,
        frozen_debt=frozen_debt,
        missing_payments=missing_payments
    )

    with open("test.html", 'w') as file:
        file.write(str(html_body))
