import re
import csv
from datetime import datetime, timedelta
import uuid
import os
from dataclasses import dataclass
import subprocess

import pypdf
import uiautomation
from uiautomation import Keys
import win32clipboard
from itk_dev_shared_components.misc import file_util
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework.sub_process.sqlite_process import DocDatabase


def open_doc2archive():
    """Start doc2archive and choose the correct folder to open.
    This function assumes that KMD Logon is already running and logged in.
    """
    subprocess.Popen("C:\Program Files (x86)\KMD\KMD doc2archive\KMD.ZP.KMDDoc2archive.Client.Shell.exe", cwd="C:\Program Files (x86)\KMD\KMD doc2archive")
    folder_popup = uiautomation.WindowControl(Name="KMD doc2archive", searchDepth=1).WindowControl(Name="Åbn mappe", searchDepth=1)
    folder_popup.ListItemControl(Name="Esr-afstem").GetSelectionItemPattern().Select()
    folder_popup.ButtonControl(Name="Åbn").GetInvokePattern().Invoke()


def kill_doc2archive():
    """Kill the Doc2Archive process."""
    os.system("taskkill /f /im KMD.ZP.KMDDoc2archive.Client.Shell.exe")


@dataclass
class DocumentMetaData:
    """A dataclass holding metadata for a document
    in the Doc2Archive document list.
    """
    report_type: str
    report_date: str
    tax_year: str


def extract_page_values(page: pypdf.PageObject) -> list[list[str]]:
    """Read a single page of a doc2archive pdf with table data.
    The function assumes that the page contains 7 columns of data.

    Args:
        page: The pypdf page object to read.

    Returns:
        A 2d list of the table data.
    """
    result = []
    t = page.extract_text()
    t = t.split("Kommunal ejd.")[1]
    t = t.split("-------")[0]
    v = re.findall(r"-?[\d\.]+(?:,\d\d)?", t)

    # Make sure that the correct number of columns are read
    assert len(v) % 7 == 0
    # Make sure everything except spaces is read
    assert (len(t) - sum(len(s) for s in v)) == t.count(" ")

    # Split into rows
    for i in range(0, len(v), 7):
        result.append(v[i:i+7])

    return result


def extract_pdf_values(pdf_path: str) -> list[list[str]]:
    """Extract data from all pages of the given pdf.

    Args:
        pdf_path: The path to the pdf file.

    Returns:
        A 2d list of the table data from all pages combined.
    """
    pdf_reader = pypdf.PdfReader(pdf_path)

    result = []

    for p in pdf_reader.pages:
        page_values = extract_page_values(p)
        result.extend(page_values)

    return result


def convert_pdf_to_csv(pdf_path: str, csv_path: str) -> None:
    """Convert a doc2archive pdf with table data to a csv file.

    Args:
        pdf_path: The path to the pdf file.
        csv_path: The path to save the csv file to.
    """
    with open(csv_path, "w", newline="") as file:
        w = csv.writer(file)
        for row in extract_pdf_values(pdf_path):
            w.writerow(row)


def read_document_list() -> list[DocumentMetaData]:
    """Read all text in the document overview table.

    Returns:
        A list of DocumentMetaData objects.
    """
    doc2arcive = uiautomation.WindowControl(Name="KMD doc2archive", searchDepth=1)
    table = doc2arcive.PaneControl(AutomationId="table")
    table.SendKey(Keys.VK_HOME)

    # Select entire table (max 300 rows)
    uiautomation.PressKey(Keys.VK_SHIFT)
    for _ in range(300):
        table.SendKey(Keys.VK_DOWN, waitTime=0)
    uiautomation.ReleaseKey(Keys.VK_SHIFT)

    clear_clipboard()
    table.SendKeys("{CTRL}C")
    text = get_clipboard_text()

    rows = text.split("\n")
    rows = [parse_document_data(t) for t in rows if t]
    return rows


def get_clipboard_text() -> str:
    """Get the text currently on the clipboard.
    If no text is on the clipboard an empty string is returned.

    Returns:
        The text currently on the clipboard.
    """
    win32clipboard.OpenClipboard()
    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
        data = win32clipboard.GetClipboardData()
    else:
        data = ""
    win32clipboard.CloseClipboard()
    return data


def clear_clipboard():
    """Clear the clipboard."""
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.CloseClipboard()


def parse_document_data(data_str: str) -> DocumentMetaData:
    """Parse copied text from the document table.

    Args:
        data_str: The raw text copied from the document table.

    Returns:
        A tuple of: report id, report date and tax year.
    """
    data = data_str.split("\t")[:-1]
    report_id = data[1]
    report_date = data[2]
    tax_year = data[6]
    return DocumentMetaData(report_id, report_date, tax_year)



def save_document(document_data: DocumentMetaData, document_index: int) -> str:
    """Save the document as a pdf in the current working dir.

    Args:
        document_title: A tuple of report id, report date and tax year.
        document_index: The documents index on the document list.

    Raises:
        RuntimeError: If the document couldn't be found.

    Returns:
        The absolute path to the saved document.
    """
    doc2arcive = uiautomation.WindowControl(Name="KMD doc2archive", searchDepth=1)
    table = doc2arcive.PaneControl(AutomationId="table")

    for _ in range(3):
        scroll_to_document(document_index)

        # Check for correct document
        clear_clipboard()
        table.SendKeys("{CTRL}C")
        text = get_clipboard_text()
        doc_data = parse_document_data(text)
        if doc_data == document_data:
            break
    else:
        raise RuntimeError(f"Couldn't scroll to the correct document: Index: {document_index} - Title: {document_data}")

    doc2arcive.ButtonControl(AutomationId="DanPdfButton").Click(simulateMove=False)

    folder = os.path.join(os.getcwd(), "reports")
    os.makedirs(folder, exist_ok=True)
    file_name = str(uuid.uuid4())
    path = os.path.join(folder, file_name) + ".pdf"

    file_util.handle_save_dialog(path)
    file_util.wait_for_download(folder, file_name, ".pdf")

    return path


def scroll_to_document(document_index: int):
    """Use keyboard shortcuts to scroll to the specified document index.

    Args:
        document_index: The index to scroll to.
    """
    doc2arcive = uiautomation.WindowControl(Name="KMD doc2archive", searchDepth=1)
    table = doc2arcive.PaneControl(AutomationId="table")
    table.SendKey(Keys.VK_HOME)
    for _ in range(document_index):
        table.SendKey(Keys.VK_DOWN, waitTime=0)


def search_for_documents(days: int) -> list[DocumentMetaData]:
    """Search for documents from today and the given amount of days in the past.

    Args:
        days: The number of days to look back from today.

    Raises:
        RuntimeError: If an unknown popup is shown when searching.

    Returns:
        A list of DocumentMetaData objects.
    """
    date_string = (datetime.now() - timedelta(days=days)).strftime("%d-%m-%Y")

    doc2arcive = uiautomation.WindowControl(Name="KMD doc2archive", searchDepth=1)
    doc2arcive.PaneControl(AutomationId="Fradato").EditControl(AutomationId="inputControl").GetValuePattern().SetValue(date_string)
    doc2arcive.ButtonControl(AutomationId="SoegButton").Click(simulateMove=False)

    popup = doc2arcive.WindowControl(Name="KMD doc2archive", searchDepth=1)
    if popup.Exists():
        if popup.TextControl().Name == "Ingen dokumenter opfylder søgekriterierne.":
            popup.ButtonControl(Name="OK").GetInvokePattern().Invoke()
            return []
        else:
            raise RuntimeError("Unknown popup shown.")

    rows = read_document_list()
    assert len(rows) > 0
    return rows


def update_doc_database(doc_database: DocDatabase, orchestrator_connection: OrchestratorConnection):
    """Search for new tax adjustments for the last 14 days and add it to the doc database.

    Args:
        doc_database: The DocDatabase object to add the new data to.
        orchestrator_connection: The connection to Orchestrator.
    """
    documents = search_for_documents(14)
    for i, doc in enumerate(documents):
        if doc.report_type == "EAENDR" and not doc_database.is_report_in_database(doc.report_date, doc.tax_year):
            path = save_document(doc, i)
            table_data = extract_pdf_values(path)
            property_list = [row[0] for row in table_data]
            doc_database.add_report_data(doc.report_date, doc.tax_year, property_list)
            orchestrator_connection.log_info(f"Added report to doc database: {doc.report_date} - {doc.tax_year} - {len(property_list)}")
