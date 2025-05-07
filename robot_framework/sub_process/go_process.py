"""Functions for working with the GetOrganized API."""

import json
from urllib.parse import urljoin

from requests import Session
from requests_ntlm import HttpNtlmAuth
from robot_framework import config


def create_session(username: str, password: str) -> Session:
    """Create a session for accessing GetOrganized API.

    Args:
        username: Username for login.
        password: Password for login.

    Returns:
        Return the session object
    """
    session = Session()
    session.headers.setdefault("Content-Type", "application/json")
    session.auth = HttpNtlmAuth(username, password)
    return session


def create_case(session: Session, title: str) -> str:
    """Create a case in GetOrganized.

    Args:
        session: Session object to access API.
        title: Title of the case being created.

    Returns:
        Return the CaseID of the created case.
    """
    url = urljoin(config.GO_API, "/_goapi/Cases/")
    payload = {
        'CaseTypePrefix': "GEO",
        'MetadataXml': f'<z:row xmlns:z="#RowsetSchema" ows_Title="{title}" ows_CaseStatus="Åben" ows_CaseCategory="Åben for alle" ows_Afdeling="916;#Backoffice - Drift og Økonomi" ows_KLENummer="318;#25.02.00 Ejendomsbeskatning i almindelighed"/>',
        'ReturnWhenCaseFullyCreated': False
    }
    response = session.post(url, data=json.dumps(payload), timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    return response.json()['CaseID']


def upload_document(*, file: bytearray, case: str, filename: str, agent_name: str | None = None, date_string: str | None = None, session: Session, doc_category: str | None = None) -> str:
    """Upload a document to Get Organized.

    Args:
        session: Session token for request.
        file: Bytearray of file to upload.
        case: Case name already present in GO.
        filename: Name of file when saved in GO.
        agent_name: Agent name, used for creating a folder in GO. Defaults to None.
        date_string: A date to add as metadata to GetOrganized. Defaults to None.

    Returns:
        Return response text and session token.
    """
    url = config.GO_API + "/_goapi/Documents/AddToCase"
    payload = {
        "Bytes": list(file),
        "CaseId": case,
        "SiteUrl": urljoin(config.GO_API, f"/cases/EMN/{case}"),
        "ListName": "Dokumenter",
        "FolderPath": agent_name,
        "FileName": filename,
        "Metadata": f"<z:row xmlns:z='#RowsetSchema' ows_Dato='{date_string}' ows_Kategori='{doc_category}'/>",
        "Overwrite": True
    }
    response = session.post(url, data=json.dumps(payload), timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    return response.text


def find_case(case_title: str, session: Session) -> str | None:
    """Search for an existing case in GO with the given case title.
    The search finds any case that contains the given title in its title.

    Args:
        case_title: The title to search for.
        session: Session object to access the API.

    Raises:
        LookupError: If more than one case was found.

    Returns:
        The case id of the found case if any.
    """
    url = config.GO_API + "/_goapi/Cases/FindByCaseProperties"
    payload = {
        "FieldProperties": [
            {
                "InternalName": "ows_Title",
                "Value": case_title,
                "ComparisonType": "Contains",
            },
            {
                "InternalName": "ows_KLENummer",
                "Value": "318;#25.02.00 Ejendomsbeskatning i almindelighed",
                "ComparisonType": "Equals",
            }
        ],
        "CaseTypePrefixes": ["GEO"],
        "LogicalOperator": "AND",
        "ExcludeDeletedCases": True,
        "ReturnCasesNumber": 2
    }
    response = session.post(url, data=json.dumps(payload), timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    cases = response.json()['CasesInfo']

    if len(cases) == 0:
        return None
    if len(cases) == 1:
        return cases[0]['CaseID']

    raise LookupError(f"Multiple cases matched the search criteria: {case_title}")
