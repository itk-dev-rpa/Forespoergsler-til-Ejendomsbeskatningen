"""This module contains the main process of the robot."""
import json
import os

from dataclasses import dataclass

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
        orchestrator_connection.log_info("No tasks in email folder.")
        return

    orchestrator_connection.log_info(f"Number of email tasks: {len(tasks)}")

    sap_session = multi_session.get_all_sap_sessions()[0]
    receivers = json.loads(orchestrator_connection.process_arguments)["receivers"]

    # Initialize GO session
    go_creds = orchestrator_connection.get_credential(config.GO_CREDENTIALS)
    go_session = go_process.create_session(go_creds.username, go_creds.password)

    for task in tasks:
        orchestrator_connection.log_info(f"Searching info on {task.address}")
        properties = structura_process.find_property(task.address)

        # Create GO case and upload incoming request
        go_case = go_process.create_case(go_session, f"{task.address}, {" - ".join(p.property_number for p in properties)}")
        go_case_id = json.loads(go_case)['CaseID']
        go_process.upload_document(session=go_session, file=graph_mail.get_email_as_mime(task.mail, graph_access).getvalue(), case=go_case_id, filename=f"{task.address}.eml")
        orchestrator_connection.log_info(f"GO case created: {go_case_id}")

        html_div_list = []

        for property_ in properties:
            orchestrator_connection.log_info(f"Searching on property {property_.property_number}")
            owners = structura_process.get_owners(property_.property_number, task.search_words)
            frozen_debt = structura_process.get_frozen_debt(property_.property_number)
            missing_payments = [sap_process.get_property_debt(sap_session, cpr, name, property_.property_number) for cpr, name in owners]

            # Format results as an html div
            html_div = mail_process.format_results(
                property_=property_,
                owners=owners,
                frozen_debt=frozen_debt,
                missing_payments=missing_payments,
                go_case_id=go_case_id
            )
            html_div_list.append(html_div)

        # Join all result html divs and send as email
        html_body = mail_process.join_email_divs(html_div_list)
        mail_process.send_email(receivers, task.address, html_body)
        orchestrator_connection.log_info("Email sent")

        # Upload mail to GO
        go_process.upload_document(session=go_session, file=bytearray(html_body, encoding="utf-8"), case=go_case_id, filename=f"Email fra RPA - Ejendomsoplysning {task.address}.html")
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
    mails = [mail for mail in mails if mail.sender == 'noreply@aarhus.dk' and 'Forespørgsler til Ejendomsbeskatning' in mail.subject]

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
    oc = OrchestratorConnection("Ejendomsbeskatning Test", conn_string, crypto_key, '{"receivers": ["ejendomsskat@aarhus.dk"]}')
    process(oc)
