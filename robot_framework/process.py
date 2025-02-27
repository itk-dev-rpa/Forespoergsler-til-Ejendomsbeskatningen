"""This module contains the main process of the robot."""

from dataclasses import dataclass
import json
import os

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from itk_dev_shared_components.sap import multi_session
from itk_dev_shared_components.graph import authentication as graph_authentication
from itk_dev_shared_components.graph import mail as graph_mail
from bs4 import BeautifulSoup

from robot_framework import config
from robot_framework.sub_process import structura_process, sap_process, mail_process, go_process


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    graph_creds = orchestrator_connection.get_credential(config.GRAPH_API)
    graph_access = graph_authentication.authorize_by_username_password(graph_creds.username, **json.loads(graph_creds.password))

    tasks = get_email_tasks(graph_access)
    if not tasks:
        return

    session = multi_session.get_all_sap_sessions()[0]
    receivers = json.loads(orchestrator_connection.process_arguments)["receivers"]

    for task in tasks:
        properties = structura_process.find_property(task.address)
        for property_ in properties:
            owners = structura_process.get_owners(property_.property_number, task.search_words)
            frozen_debt = structura_process.get_frozen_debt(property_.property_number)
            missing_payments = [sap_process.get_property_debt(session, cpr, name, property_.property_number) for cpr, name in owners]

            body = mail_process.format_results(
                property_=property_,
                owners=owners,
                frozen_debt=frozen_debt,
                missing_payments=missing_payments
            )

            mail_process.send_email(receivers, task.address, body)

            go_login, go_password = orchestrator_connection.get_credential(config.GO_CREDENTIALS)
            file_bytearray = bytearray(body)
            session = go_process.create_session(go_login, go_password)
            case, session = go_process.create_case(config.GO_API, "title", session, "GEO")
            go_process.upload_document(session=session, apiurl=config.GO_API, file=file_bytearray, case=case.title, filename="Svar_på_forespørgsel.txt")

        graph_mail.delete_email(task.mail, graph_access)


@dataclass
class Task:
    """A dataclass representing an email task."""
    address: str
    search_words: list[str]
    mail: graph_mail.Email


def get_email_tasks(graph_access) -> list[Task]:
    """Get tasks from emails.

    Args:
        graph_access: The graph authentication object.

    Returns:
        A list of Task object based on the found emails.
    """
    mails = graph_mail.get_emails_from_folder("itk-rpa@mkb.aarhus.dk", "Indbakke/Ejendomsbeskatning", graph_access)
    mails = [mail for mail in mails if mail.sender == 'noreply@aarhus.dk' and mail.subject == 'Forespørgsler til Ejendomsbeskatning (fra Selvbetjening.aarhuskommune.dk)']

    tasks = []

    for mail in mails:
        soup = BeautifulSoup(mail.body, "html.parser")
        address = soup.find_all('p')[1].get_text(separator="$").split('$')[1]
        owner_1 = soup.find_all('p')[3].get_text(separator="$").split('$')[1]
        owner_2 = soup.find_all('p')[4].get_text(separator="$").split('$')[1]

        search_words = owner_1.split() + owner_2.split()

        tasks.append(Task(address, search_words, mail))

    return tasks


if __name__ == '__main__':
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Ejendomsbeskatning Test", conn_string, crypto_key, '{"receivers": []}')
    process(oc)
