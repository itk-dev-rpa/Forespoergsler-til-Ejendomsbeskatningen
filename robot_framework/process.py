"""This module contains the main process of the robot."""
import json
import os

from dataclasses import dataclass
from datetime import date

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from itk_dev_shared_components.sap import multi_session
from itk_dev_shared_components.graph import authentication as graph_authentication
from itk_dev_shared_components.graph.authentication import GraphAccess
from itk_dev_shared_components.graph import mail as graph_mail
from bs4 import BeautifulSoup

from robot_framework import config
from robot_framework.sub_process import structura_process, sap_process, mail_process, go_process, doc2archive_process
from robot_framework.sub_process.sqlite_process import DocDatabase


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")
    arguments = json.loads(orchestrator_connection.process_arguments)

    graph_creds = orchestrator_connection.get_credential(config.GRAPH_API)
    graph_access = graph_authentication.authorize_by_username_password(graph_creds.username, **json.loads(graph_creds.password))

    doc_database = DocDatabase(arguments["doc_database_path"])
    doc2archive_process.update_doc_database(doc_database, orchestrator_connection)

    tasks = get_email_tasks(graph_access)
    if not tasks:
        orchestrator_connection.log_info("No tasks in email folder.")
        return

    orchestrator_connection.log_info(f"Number of email tasks: {len(tasks)}")

    sap_session = multi_session.get_all_sap_sessions()[0]
    receivers = arguments["receivers"]

    # Initialize GO session
    go_creds = orchestrator_connection.get_credential(config.GO_CREDENTIALS)
    go_session = go_process.create_session(go_creds.username, go_creds.password)

    for task in tasks:
        handle_task(
            task=task,
            receivers=receivers,
            orchestrator_connection=orchestrator_connection,
            go_session=go_session,
            sap_session=sap_session,
            graph_access=graph_access,
            doc_database=doc_database
        )


@dataclass
class Task:
    """A dataclass representing an email task."""
    address: str
    owners: list[str]
    requested_data: list[str]
    mail: graph_mail.Email


def handle_task(*, task: Task, receivers: list[str], orchestrator_connection: OrchestratorConnection, go_session, sap_session,
                graph_access: GraphAccess, doc_database: DocDatabase):
    """Handle a single task from start to finish.

    Args:
        task: The task to handle.
        receivers: The list of email receivers.
        orchestrator_connection: The connection to Orchestrator.
        go_session: The GO session.
        sap_session: The SAP session.
        graph_access: The GraphAccess object.
        doc_database: The DocDatabase object.
    """
    orchestrator_connection.log_info(f"Searching info on {task.address}")
    properties = structura_process.find_property(task.address)
    orchestrator_connection.log_error(f"Properties found: {len(properties)}")

    if not properties:
        orchestrator_connection.log_info(f"No properties found on {task.address}")
        mail_process.send_no_properties_email(receivers, task.address)
        graph_mail.delete_email(task.mail, graph_access)
        return

    html_div_list = []

    for property_ in properties:
        orchestrator_connection.log_info(f"Searching on property {property_.property_number}")
        owners = structura_process.get_owners(property_.property_number, task.owners)
        owner_cprs = [p[0] for p in owners]

        frozen_debt = structura_process.get_frozen_debt(property_.property_number, owner_cprs)
        if structura_process.should_skip_due_to_frozen_debt(frozen_debt):
            return

        tax_data = structura_process.get_tax_data(property_.property_number)
        missing_payments = [sap_process.get_property_debt(sap_session, cpr, name, property_.property_number) for cpr, name in owners]
        tax_adjustments = doc_database.search_property(property_.property_number)

        # Format results as two html divs
        # Raw data format
        html_div = mail_process.format_results(
            property_=property_,
            owners=owners,
            frozen_debt=frozen_debt,
            tax_data=tax_data,
            missing_payments=missing_payments,
            tax_adjustments=tax_adjustments
        )
        html_div_list.append(html_div)
        # Nice format
        html_div = mail_process.pretty_template(
            address=property_.location,
            frozen_debt=frozen_debt,
            missing_payments=missing_payments,
            tax_data=tax_data,
            tax_adjustments=tax_adjustments,
            requested_data=task.requested_data
        )
        html_div_list.append(html_div)

    # Find/Create GO case and upload incoming request
    go_case_id = go_process.find_case(task.address, go_session)
    if not go_case_id:
        case_title = f"{task.address}, {' - '.join(p.property_number for p in properties)}"
        go_case_id = go_process.create_case(go_session, case_title)

    go_process.upload_document(session=go_session, file=graph_mail.get_email_as_mime(task.mail, graph_access).getvalue(), case=go_case_id, filename=f"Forespørgsel {task.address} {date.today()}.eml")
    orchestrator_connection.log_info(f"GO case created: {go_case_id}")

    # Join all result html divs and send as email
    html_body = mail_process.join_email_divs(html_div_list)
    mail_process.send_email(receivers, task.address, "go_case_id", html_body)
    orchestrator_connection.log_info("Email sent")

    # Upload mail to GO
    go_process.upload_document(session=go_session, file=bytearray(html_body, encoding="utf-8"), case=go_case_id, filename=f"Email fra RPA - Ejendomsoplysning {task.address} {date.today()}.html")

    # Delete task from mail queue
    graph_mail.delete_email(task.mail, graph_access)


def get_email_tasks(graph_access: GraphAccess) -> list[Task]:
    """Get tasks from emails.

    Args:
        graph_access: The graph authentication object.

    Returns:
        A list of Task object based on the found emails.
    """
    mails = graph_mail.get_emails_from_folder("itk-rpa@mkb.aarhus.dk", "Indbakke/Ejendomsbeskatning", graph_access)
    mails = [mail for mail in mails if mail.sender == 'noreply@aarhus.dk' and 'Forespørgsler til Ejendomsbeskatning' in mail.subject]
    mails.reverse()

    tasks = []

    for mail in mails:
        soup = BeautifulSoup(mail.body, "html.parser")
        paragraphs = [p.get_text(separator="$").split('$') for p in soup.find_all('p')]
        values = {p[0]: p[1] for p in paragraphs if len(p) == 2}

        if values["Jeg kan ikke finde adressen i udsøgningen"] == "Valgt":
            graph_mail.delete_email(mail, graph_access)

        address = values["Indtast sagens adresse"]

        if values["Drejer sagen sig om privatpersoner eller virksomhed?"] == "Privatpersoner":
            names = [li.get_text(separator="$").split('$') for li in soup.find_all('li')]
            names = [
                " ".join([item.split(":")[1].strip() for item in name])
                for name in names
            ]
        else:
            names = [values["Indtast virksomhedens navn"]]

        requested_data = values["Hvilke oplysninger efterspørges?"].split(", ")

        tasks.append(Task(address, names, requested_data, mail))

    return tasks


if __name__ == '__main__':
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Ejendomsbeskatning Test", conn_string, crypto_key, '{"receivers": ["ghbm@aarhus.dk"]}')
    process(oc)
