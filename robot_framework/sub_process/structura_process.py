import re
import time
from dataclasses import dataclass
import subprocess
import os

import uiautomation
from uiautomation import Keys, WindowVisualState


@dataclass
class Property:
    property_number: str
    location: str


def find_property(address: str) -> list[Property]:
    """Find the properties that match the given address.
    It's important the address i properly formatted according to Danish standards.
    https://danmarksadresser.dk/om-adresser/saadan-gengives-en-adresse

    Args:
        address: The address to search for.

    Raises:
        LookupError: If the address couldn't be found.

    Returns:
        A list of Properties that match the given address.
    """
    street, number, floor, door, _, _ = _deconstruct_address(address)

    structura = uiautomation.WindowControl(RegexName="KMD", AutomationId="MainForm", searchDepth=1)
    structura.ButtonControl(Name="ESR", searchDepth=6).GetInvokePattern().Invoke()
    structura.ButtonControl(Name="Ny Søgning", searchDepth=2).GetInvokePattern().Invoke()

    search_view = structura.PaneControl(AutomationId="SoegningView", searchDepth=7)

    # Fill in search terms
    ejendom_pane = search_view.PaneControl(AutomationId="collapsGroupEjendom")
    ejendom_pane.EditControl(AutomationId="textBoxVejnavn", searchDepth=1).GetValuePattern().SetValue(street)
    ejendom_pane.EditControl(AutomationId="textBoxHusNummerFra", searchDepth=1).GetValuePattern().SetValue(number)
    ejendom_pane.EditControl(AutomationId="textBoxEtage", searchDepth=1).GetValuePattern().SetValue(floor)
    ejendom_pane.EditControl(AutomationId="textBoxSideDoerNr", searchDepth=1).GetValuePattern().SetValue(door)

    # Search
    search_view.ButtonControl(AutomationId="soegBtn").GetInvokePattern().Invoke()

    # Get results
    result = []

    tree = structura.TreeControl(AutomationId="treeView", searchDepth=6).GetChildren()[0]
    children: list[uiautomation.TreeItemControl] = tree.GetChildren()
    for c in children:
        if _match_address_result(address, c.Name):
            c.GetSelectionItemPattern().Select()
            info_pane = structura.PaneControl(AutomationId="rightPanel", searchDepth=6).PaneControl(AutomationId="groupBoxGenerelleOplysninger", searchDepth=4)
            property_number = info_pane.EditControl(AutomationId="textBoxEjendomsnummer").GetValuePattern().Value
            location = info_pane.EditControl(AutomationId="textBoxBeliggenhed").GetValuePattern().Value
            result.append(Property(property_number, location))


    if not result:
        raise LookupError(f"No property number found for the address: {address}")

    return result


def _deconstruct_address(address: str) -> tuple[str | None, ...]:
    """Deconstruct an address string to its parts.
    street, number, floor, door, zip, city

    Args:
        address: The address to deconstruct. Formatted by Danish standards.

    Returns:
        A tuple of the parts: street, number, floor, door, zip, city.
    """
    matches = re.match(r"^(.+?) (\d{1,3}[a-zA-Z]?)(?:, )?(\w+)?\.? ?(\w+?)?, (\d{4}) (.+)$", address)
    return matches.groups()


def _match_address_result(address: str, result: str) -> bool:
    """Match an address string against a result string from Structura.

    Args:
        address: The address string to match.
        result: The result string to match.

    Returns:
        True if a match is found.
    """
    street, number, floor, door, zip, city = _deconstruct_address(address)
    regex_pattern = f"{street} {number}.+?{floor.upper() if floor else ''}.+?{door.upper() if door else ''}"
    matches = re.findall(regex_pattern, result)
    return len(matches) == 1


def get_owners(property_number: str, search_words: list[str]) -> list[tuple[str, str]]:
    """Get the cpr numbers and names of the owners of the given property on the given date.

    Args:
        property_number: The property to look up.
        check_date: The date which to look for ownership.

    Raises:
        LookupError: If no owners could be found on the given date.

    Returns:
        A list of tuples of cpr numbers and names.
    """
    # New search
    structura = uiautomation.WindowControl(RegexName="KMD", AutomationId="MainForm", searchDepth=1)
    structura.ButtonControl(Name="ESR", searchDepth=6).GetInvokePattern().Invoke()
    structura.ButtonControl(Name="Ny Søgning", searchDepth=2).GetInvokePattern().Invoke()

    # Search
    search_view = structura.PaneControl(AutomationId="SoegningView", searchDepth=7)
    ejendom_pane = search_view.PaneControl(AutomationId="collapsGroupEjendom")
    ejendom_pane.EditControl(AutomationId="textBoxEjdNr", searchDepth=1).GetValuePattern().SetValue(property_number)
    search_view.ButtonControl(AutomationId="soegBtn").GetInvokePattern().Invoke()

    # Get info
    tree = structura.TreeControl(AutomationId="treeView", searchDepth=6)
    tree.TreeItemControl(RegexName=f"0*{property_number},").GetSelectionItemPattern().Select()
    structura.ButtonControl(Name="Hent alle oplysninger", searchDepth=2).GetInvokePattern().Invoke()

    owners = []

    owners_group = tree.TreeItemControl(Name="Aktuelle ejere")
    owners_group.GetExpandCollapsePattern().Expand()
    owner_elements: list[uiautomation.TreeItemControl] = owners_group.GetChildren()

    owners_group = tree.TreeItemControl(Name="Historiske Ejere")
    owners_group.GetExpandCollapsePattern().Expand()
    owner_elements += owners_group.GetChildren()

    for owner_element in owner_elements:
        if any(word.lower() in owner_element.Name.lower() for word in search_words):
            owner_element.GetSelectionItemPattern().Select()
            cpr = structura.EditControl(AutomationId="textBoxCprCvr").GetValuePattern().Value
            name = structura.EditControl(AutomationId="textBoxNavn").GetValuePattern().Value
            owners.append((cpr, name))

    return owners


def get_frozen_debt(property_number: str) -> list[tuple[str, str, str, str]]:
    """Gets the frozen debt on the given property.

    Args:
        property_number: The number of the property.

    Returns:
        A list of tuples containing [cpr, name, date, amount].
    """
    # New search
    structura = uiautomation.WindowControl(RegexName="KMD", AutomationId="MainForm", searchDepth=1)
    structura.ButtonControl(Name="I-lån", searchDepth=6).GetInvokePattern().Invoke()
    structura.ButtonControl(Name="Søgning...", searchDepth=2).GetInvokePattern().Invoke()

    # Search
    ejendom_group = structura.GroupControl(AutomationId="groupBoxEjendom")
    ejendom_group.EditControl(AutomationId="textBoxEjendomsnummerEt").GetValuePattern().SetValue(property_number)
    structura.ButtonControl(AutomationId="buttonSoeg").GetInvokePattern().Invoke()

    # Wait for result
    tree = structura.TreeControl(AutomationId="treeView")
    result = tree.TreeItemControl(RegexName=f".*{property_number.lstrip('0')}", searchDepth=1)
    result_items: list[uiautomation.TreeItemControl] = result.GetChildren()

    tabPane = structura.TabControl(AutomationId="LaanesagTabControl", searchDepth=10)
    sag_tab = tabPane.TabItemControl(Name="Lånesag", searchDepth=1)
    move_tab = tabPane.TabItemControl(Name="Lånebevægelser", searchDepth=1)

    data = []

    for item in result_items:
        if "(Accepteret med indefrysning)" in item.Name:
            item.GetSelectionItemPattern().Select()

            sag_tab.GetSelectionItemPattern().Select()
            cpr = tabPane.EditControl(AutomationId="textBoxLaanansoegerCpr").GetValuePattern().Value
            name = tabPane.EditControl(AutomationId="textBoxLaaneansoegerNavn").GetValuePattern().Value

            move_tab.GetSelectionItemPattern().Select()
            structura.ComboBoxControl(AutomationId="comboBoxLaanebevaegelserFilter").SendKey(Keys.VK_UP)

            row = structura.TableControl(AutomationId="gridControlLaanebevaegelser").CustomControl(Name="Row 1")
            date_ = row.DataItemControl(Name="Forfaldsdato row0").GetValuePattern().Value
            amount = row.DataItemControl(Name="Saldo row0").GetValuePattern().Value

            data.append((cpr, name, date_, amount))

    return data


def open_structura(username: str, password: str):
    """Open and login in to KMD Structura.

    Args:
        username: The username to use.
        password: The password to use.

    Raises:
        RuntimeError: If KMD Structura failed to maximize.
    """
    subprocess.Popen(r"C:\Program Files (x86)\KMD\KMD.JO.Structura\KMD.JO.Structura.exe", cwd=r"C:\Program Files (x86)\KMD\KMD.JO.Structura")

    kmd_logon = uiautomation.WindowControl(AutomationId="MainLogonWindow", searchDepth=1)
    kmd_logon.EditControl(AutomationId="UserPwTextBoxUserName").GetValuePattern().SetValue(username)
    kmd_logon.EditControl(AutomationId="UserPwPasswordBoxPassword").GetValuePattern().SetValue(password)
    kmd_logon.ButtonControl(AutomationId="UserPwLogonButton").GetInvokePattern().Invoke()

    select_window = uiautomation.WindowControl(AutomationId="SelectAdmEnhed", searchDepth=1)
    select_window.ComboBoxControl(AutomationId="_comboAdministrativEnhed").GetValuePattern().SetValue("Aarhus Kommune")
    select_window.ButtonControl(AutomationId="_buttonOK").GetInvokePattern().Invoke()

    structura = uiautomation.WindowControl(RegexName="KMD", AutomationId="MainForm", searchDepth=1)
    # Try maximizing the window a few times until it succeeds
    for _ in range(10):
        time.sleep(1)
        try:
            if not structura.GetWindowPattern().SetWindowVisualState(WindowVisualState.Maximized):
                continue
            break
        except Exception:
            pass
    else:
        raise RuntimeError("Couldn't maximize Structura")


def kill_structura():
    """Kill KMD Logon and KMD Structura."""
    os.system("taskkill /f /im KMD.JO.Structura.exe")
    os.system("taskkill /f /im KMD.YH.Security.Logon.Desktop.exe")

