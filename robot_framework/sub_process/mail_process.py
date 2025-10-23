"""This module is responsible for sending results as emails."""

from datetime import date

from htpy import html, body, h3, p, ul, li, Element, div, a, table, th, tr, td, style, hr  # pylint: disable=no-name-in-module

from itk_dev_shared_components.smtp import smtp_util

from robot_framework import config
from robot_framework.sub_process.sap_process import MissingPaymentPerson
from robot_framework.sub_process.structura_process import Property, FrozenDebt


def join_email_divs(div_list: list[str]) -> str:
    """Join multiple div to a single html document string."""
    elements = []
    for s in div_list:
        elements.append(div[s])
        elements.append(hr)
    elements.pop()

    html_body = html[body[[elements]]]
    return str(html_body)


def format_results(*, property_: Property, owners: list[tuple[str, str]], frozen_debt: list[FrozenDebt], tax_data: list[tuple[str, str]],
                   missing_payments: list[MissingPaymentPerson], tax_adjustments: list[dict[str, str]]) -> str:
    """Format inputs as a neat html div.

    Args:
        property: The property object.
        owners: A list of owners as tuples of cpr and names.
        frozen_debt: Frozen debt as a list FrozenDebt objects.
        tax_data: A list of tuples of text and amount.
        missing_payments: A list of Person objects.
        tax_adjustments: A list of tax adjustments.

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
        _format_missing_payments(missing_payments),

        h3["Efterreguleringer af ejendomsskat"],
        _format_tax_adjustments(tax_adjustments)
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


def _format_tax_adjustments(tax_adjustments: list[dict[str, str]]) -> Element:
    """Helper function for creating a list of tax adjustments."""
    if tax_adjustments:
        adjustment_list = [[ta["property_number"], ta["tax_year"], ta["report_date"]] for ta in tax_adjustments]
        return _create_list(adjustment_list)

    return p["Ingen justeringer i databasen."]


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


def send_no_properties_email(receivers: list[str], address: str):
    """Send an email about the given address not being found.

    Args:
        receivers: The list of email receivers.
        address: The address in question.
    """
    smtp_util.send_email(
        receiver=receivers,
        sender="itk-rpa@mkb.aarhus.dk",
        subject=f"Ejendomsoplysning: {address} ikke fundet",
        body=f"Adressen '{address}' kunne ikke findes i Structura.\nVenlig hilsen\nRobotten",
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT
    )


def pretty_template(*, address: str, frozen_debt: list[FrozenDebt], missing_payments: list[MissingPaymentPerson], tax_data: list[tuple[str, str]],
                    tax_adjustments: list[dict[str, str]], requested_data: list[str]) -> str:
    """Format the data in a prettier template that can be sent to the requesters.

    Args:
        address: The address of the property.
        frozen_debt: A list of frozen debt.
        missing_payments: A list of missing payments.
        tax_data: A list of tax data.
        tax_adjustments: A list of tax adjustments.
        requested_data: The list of data that has been requested in the form.

    Returns:
        The pretty template as an HTML string.
    """

    current_date = date.today().strftime("%d/%m %Y")

    # Top text
    div_text = div[
        p["Hej"],
        p[f"Oplysningerne herunder er fra {current_date} og er svar på en henvendelse lavet via: ", a(href="https://selvbetjening.aarhuskommune.dk/da/content/forespoergsler-til-ejendomsbeskatning")["Forespørgsler til Ejendomsbeskatning | Selvbetjening.aarhuskommune.dk"]],
        p["Læs her mere om, hvordan du hurtigst og nemmest får ejendomsoplysninger som mægler eller anden tredjepart: ", a(href="https://aarhus.dk/virksomhed/byggeri-og-grunde/er-du-en-ejendomsmaegler-som-oensker-oplysninger-om-en-ejendom")["Er du en ejendomsmægler, som ønsker oplysninger om en ejendom?"]],
    ]

    # Frozen debt
    if frozen_debt:
        content = table[
            th(width="300px")["Navn"], th(width="200px")["Beløb"],
            (
                tr[td[debt.name], td[f"{debt.amount} kr."]]
                for debt in frozen_debt
            )
        ]
    else:
        content = p["Ingen indefrossent grundskyld."]

    div_frozen_debt = div[
        h3[f"Indefrosset grundskyld for skatteårene til og med 2023 for {address}."],
        content
    ]

    # Missing payments
    missing_payments_list = []
    for person in missing_payments:
        for case_ in person.cases:
            for entry in case_.entries:
                missing_payments_list.append(tr[td[f"{entry.title} for {person.name}"], td[f"{entry.amount} kr"]])

    if not missing_payments_list:
        missing_payments_list = [tr[td["Restance"], td["0 kr"]]]

    div_missing_payments = div[
        h3[f"Restancer for {address}."],
        table[
            th(width="300px")["Post"], th(width="200px")["Beløb"],
            missing_payments_list,
            tr[td(colspan="2")[
                "Restancer kan betales via ", a(href="https://aarhus.dk/borger/borgerservice/oekonomi-og-pension/betaling-af-regninger-og-gaeld-til-kommunen")["Betaling af regninger og gæld til kommunen"], " og ellers:",
                p(".centered")["Reg.nr.: 2211"],
                p(".centered")["Kontonr.: 6446462022"],
                p(".centered")["Tekst: Sælgers CPR nr. + ejendom"]
            ]]
        ]
    ]

    # Tax
    if tax_data:
        content = table[
            th(width="300px")["Post"], th(width="200px")["Beløb"],
            (
                tr[td[text], td[f"{amount} kr."]]
                for text, amount in tax_data
            )
        ]
    else:
        content = p["Ingen skattedata tilgængeligt for ejendommen."]

    div_tax = div[
        h3[f"Ejendomsbidrag for {address}."],
        p["(Hvis ikke andet fremgår af tabellen vedr. restancer, er nedenstående beløb betalt)."],
        content
    ]

    # Property tax adjustment
    if not tax_adjustments:
        text = p["Der har pt. ikke været en efterregulering pba. af en 2020-vurdering."]
    else:
        # Group adjustments by report date
        reports = {}
        for ta in tax_adjustments:
            report_date = _format_report_date(ta["report_date"])
            tax_year = ta['tax_year']
            if report_date not in reports:
                reports[report_date] = []
            reports[report_date].append(tax_year)
            reports[report_date].sort()

        text = [p[f"Der er d. {report_date} oprettet nye skattebilletter for skatteåret {', '.join(tax_years)} pba. en ny vurdering. De blev sendt til daværende ejer(e)."] for report_date, tax_years in reports.items()]

    div_tax_adjustments = div[
        h3[f"Efterreguleringer af ejendomsskat for {address}"],
        text
    ]

    # Collect it all
    div_list = []
    if "Indefrosset grundskyld" in requested_data:
        div_list.append(div_frozen_debt)
    if "Restancer" in requested_data:
        div_list.append(div_missing_payments)
    if "Ejendomsbidrag" in requested_data:
        div_list.append(div_tax)
    if "Efterregulering" in requested_data:
        div_list.append(div_tax_adjustments)

    html_el = html[
        style[
            "table, th, td {border: 1px solid; border-collapse: collapse; padding: 3px}",
            ".centered {text-align: center; margin: 0.3rem}",
            "th {text-align: left}"
        ],
        body[
            div_text,
            div_list
        ]
    ]

    return str(html_el)


def _format_report_date(report_date: str) -> str:
    """Change a date string from 'yyyy-mm-dd' to 'dd/mm yyyy'."""
    return f"{report_date[8:12]}/{report_date[5:7]} {report_date[0:4]}"
