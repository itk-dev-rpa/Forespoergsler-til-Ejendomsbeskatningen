"""Functions for working with the GetOrganized API."""

import json
from urllib.parse import urljoin
from typing import Literal

from requests import Session
from requests_ntlm import HttpNtlmAuth
from robot_framework import config


def create_session(username: str, password: str) -> Session:
    """Create a session for accessing GetOrganized API.

    Args:
        apiurl: URL for the API.
        username: Username for login.
        password: Password for login.

    Returns:
        Return the session object
    """
    session = Session()
    session.headers.setdefault("Content-Type", "application/json")
    session.auth = HttpNtlmAuth(username, password)
    return session


def upload_document(*, apiurl: str, file: bytearray, case: str, filename: str, agent_name: str | None = None, date_string: str | None = None, session: Session, doc_category: str | None = None) -> tuple[str, Session]:
    """Upload a document to Get Organized.

    Args:
        apiurl: Base url for API.
        session: Session token for request.
        file: Bytearray of file to upload.
        case: Case name already present in GO.
        filename: Name of file when saved in GO.
        agent_name: Agent name, used for creating a folder in GO. Defaults to None.
        date_string: A date to add as metadata to GetOrganized. Defaults to None.

    Returns:
        Return response text and session token.
    """
    url = apiurl + "/_goapi/Documents/AddToCase"
    payload = {
        "Bytes": list(file),
        "CaseId": case,
        "SiteUrl": urljoin(apiurl, f"/cases/EMN/{case}"),
        "ListName": "Dokumenter",
        "FolderPath": agent_name,
        "FileName": filename,
        "Metadata": f"<z:row xmlns:z='#RowsetSchema' ows_Dato='{date_string}' ows_Kategori='{doc_category}'/>",
        "Overwrite": True
    }
    response = session.post(url, data=json.dumps(payload), timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    return response.text, session


def delete_document(apiurl: str, document_id: int, session: Session) -> tuple[str, Session]:
    """Delete a document from GetOrganized.

    Args:
        apiurl: Url of the GetOrganized API.
        session: Session object used for logging in.
        document_id: ID of the document to delete.

    Returns:
        Return the response and session objects
    """
    url = urljoin(apiurl, "/_goapi/Documents/ByDocumentId")
    payload = {
        "DocId": document_id
    }
    response = session.delete(url, data=json.dumps(payload), timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    return response.text, session


def create_case(session: Session, apiurl: str, title: str, case_type: str = Literal["EMN", "GEO"]) -> tuple[str, Session]:
    """Create a case in GetOrganized.

    Args:
        apiurl: Url for the GetOrganized API.
        session: Session object to access API.
        title: Title of the case being created.

    Returns:
        Return the response and session objects.
    """
    url = urljoin(apiurl, "/_goapi/Cases/")
    payload = {
        'CaseTypePrefix': case_type,
        'MetadataXml': f'<z:row xmlns:z="#RowsetSchema" ows_Title="{title}" ows_CaseStatus="Åben" ows_CaseCategory="Åben for alle" ows_Afdeling="916;#Backoffice - Drift og Økonomi" ows_KLENummer="318;#25.02.00 Ejendomsbeskatning i almindelighed"/>',
        'ReturnWhenCaseFullyCreated': False
    }
    # 'ows_ke006386ddf64c16a8479586f364650a=\\"Backoffice - Drift og Økonomi|5072f71c-28e3-4c7e-8e7f-f65b4d454d9e\\" ows_TaxCatchAll=\\"916;#c/pi+qQGP02sMEwRnL1L1w==|zKfFYm/rBEeob8V2xL68yg==|HPdyUOMofkyOf/ZbTUVNng==|4QSKkOkDGkaOCvq2uWQRdA==|ltoZYhLtHkSYMJMldMoKjw==|TghtvxHyIkOVqkDzDw5tOw==;#18;#c/pi+qQGP02sMEwRnL1L1w==|5sVser1uDkWZqL5iSsyfVw==|6lG4WoPw60yRNuxKk/Og5Q==|Sk5E054vKUa0Z5UkRpoMmg==;#318;#c/pi+qQGP02sMEwRnL1L1w==|2AWQEvSHR06vgQycVe+viw==|XLz69E7hnEmdNjgpzJ6QoA==|diRq4JTorkazWZAF0hUFxQ==|1gdbosLfE06NiNpIkAvQdQ==;#939;#c/pi+qQGP02sMEwRnL1L1w==|hTQCuyVpRU2KVPnywM0/sA==|uE/FNoXJdEG0cd2NsNEPyA==|s+o9sRZGv0S9Y4lEzJdI9Q==\\" ows_SupplerendeAfdelinger=\\"\\" ows_SupplerendeSagsbehandlere=\\"\\" ows_KLENummer=\\"318;#25.02.00 Ejendomsbeskatning i almindelighed\\" ows_ha72d8e6a0014a358177ca2216130612=\\"25.02.00 Ejendomsbeskatning i almindelighed|f4fabc5c-e14e-499c-9d36-3829cc9e90a0\\" ows_Facet=\\"18;#G01 Generelle sager\\" ows_h2650a0f25734385b340a75333c3334f=\\"G01 Generelle sager|5ab851ea-f083-4ceb-9136-ec4a93f3a0e5\\" ows_Modtaget=\\"2025-02-25 00:00:00\\" ows_CCMDestinationItemMoved=\\"0\\" ows_GISUpdate=\\"0\\" ows_GISUpdateExisting=\\"0\\" ows_Sagsprofil_GEO=\\"939;#MKB Basis\\" ows_da1ababf108e4b33a775ee114426bb53=\\"MKB Basis|36c54fb8-c985-4174-b471-dd8db0d10fc8\\" ows_CCMMustBeOnPostList=\\"0\\" ows_DepartmentInheritance=\\"0\\" ows_Lukket=\\"2025-02-25 14:56:05\\" ows_CCMHasRelations=\\"0\\" ows_LastModifiedBy=\\"6548;#Sebastian Wolf(az79644)\\" ows_LastModifiedDate=\\"2025-02-25 14:55:22\\" ows_CCMCaseTransferFrom=\\"\\" ows_CCMCaseTransferTo=\\"\\" ows_PostListDepartment=\\"MKB-Borgerservice og Biblioteker/Borgerservice/Backoffice - Drift og Økonomi\\" ows_TaxCatchAllLabel=\\"916;#Backoffice - Drift og Økonomi#І|;#18;#G01 Generelle sager#І|;#318;#25.02.00 Ejendomsbeskatning i almindelighed#І|;#939;#MKB Basis#І|\\" ows_Restricted=\\"1437;#\\" ows_ContentVersion=\\"1437;#0\\" ows_ServerRedirected=\\"0\\" ows_IsShared=\\"1\\" />","Attributes":null}'
    response = session.post(url, data=json.dumps(payload), timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    return response.text, session


def case_metadata(session: Session, apiurl: str, case_id: str):
    url = urljoin(apiurl, f"/_goapi/Cases/Metadata/{case_id}")
    response = session.get(url, timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    return response.text, session


def close_case(apiurl: str, case_number: str, session: Session) -> tuple[str, Session]:
    """Close a case in GetOrganized.

    Args:
        apiurl: Url for the GetOrganized API.
        session: Session object to access API.
        case_number: Case number of case to be closed.

    Returns:
        Return the response and session objects.
    """
    url = urljoin(apiurl, "/_goapi/Cases/CloseCase")
    payload = {"CaseId": case_number}
    response = session.post(url, data=payload, timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    return response.text, session


def finalize_document(apiurl: str, doc_id: int, session: Session) -> tuple[str, Session]:
    """Finalize a document in GetOrganized.

    Args:
        apiurl: URL for GetOrganized API.
        doc_id: ID of document to journalize.
        session: Session token for connection.

    Returns:
        Response text and updated session token.
    """
    url = urljoin(apiurl, "/_goapi/Documents/Finalize/ByDocumentId")
    payload = {"DocId": doc_id}
    response = session.post(url, data=payload, timeout=config.GO_TIMEOUT)
    response.raise_for_status()
    return response.text, session
