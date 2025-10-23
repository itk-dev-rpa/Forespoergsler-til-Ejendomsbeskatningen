"""This module is responsible for interaction with the structura software."""

import re
import time
from dataclasses import dataclass
import subprocess
import os
import difflib
from datetime import datetime, timedelta

import uiautomation
from uiautomation import Keys, WindowVisualState


@dataclass
class Property:
    """A dataclass representing a property."""
    property_number: str
    location: str


@dataclass
class FrozenDebt:
    """A dataclass representing frozen debt."""
    cpr: str
    name: str
    date_: str
    amount: str
    status: str


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
    # The button needs to be clicked since it stalls on errors
    search_view.ButtonControl(AutomationId="soegBtn").Click(simulateMove=False)

    # Check for error popup
    error_popup = structura.WindowControl(Name="Fejl", searchDepth=1)
    if error_popup.Exists(maxSearchSeconds=2):
        if error_popup.TextControl().Name != "Ingen data opfylder søgekriteriet":
            raise RuntimeError("Unknown error popup")

        error_popup.ButtonControl(Name="OK").GetInvokePattern().Invoke()
        return []

    # Get results
    result = []

    tree = structura.TreeControl(AutomationId="treeView", searchDepth=6).TreeItemControl(1, 0.5)
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
    street, number, floor, door, _, _ = _deconstruct_address(address)
    regex_pattern = fr"{street} {number}[ ,.]*?{floor.upper() if floor else ''}[ ,.]*?{door.upper() if door else ''},\w*?,"
    matches = re.findall(regex_pattern, result)
    return len(matches) == 1


def get_owners(property_number: str, owners: list[str]) -> list[tuple[str, str]]:
    """Get the cpr numbers and names of the owners of the given property.

    Args:
        property_number: The property to look up.
        owners: The list of owner names to search for.

    Returns:
        A list of tuples of cpr numbers and names.
    """
    _search_property(property_number)

    structura = uiautomation.WindowControl(RegexName="KMD", AutomationId="MainForm", searchDepth=1)
    tree = structura.TreeControl(AutomationId="treeView", searchDepth=6)

    # Find owners
    owners_group = tree.TreeItemControl(Name="Aktuelle ejere")
    owners_group.GetExpandCollapsePattern().Expand()
    owner_elements: list[uiautomation.TreeItemControl] = owners_group.GetChildren()

    owners_group = tree.TreeItemControl(Name="Historiske Ejere")
    owners_group.GetExpandCollapsePattern().Expand()
    owner_elements += owners_group.GetChildren()

    # Get all names on the list
    names = [owner_element.Name.split(",")[0] for owner_element in owner_elements]

    owners_result = []

    for owner in owners:
        owner_matches = difflib.get_close_matches(owner, names, n=1)
        if not owner_matches:
            continue

        index = names.index(owner_matches[0])
        owner_element = owner_elements[index]
        owner_element.GetSelectionItemPattern().Select()
        cpr = structura.EditControl(AutomationId="textBoxCprCvr").GetValuePattern().Value
        name = structura.EditControl(AutomationId="textBoxNavn").GetValuePattern().Value
        owners_result.append((cpr, name))

    return owners_result


def get_frozen_debt(property_number: str, owner_cprs: list[str]) -> list[FrozenDebt]:
    """Gets the frozen debt on the given property.

    Args:
        property_number: The number of the property.
        owner_cprs: A list of the owners cpr numbers.

    Returns:
        A list of FrozenDebt objects.
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

    tab_pane = structura.TabControl(AutomationId="LaanesagTabControl", searchDepth=10)
    sag_tab = tab_pane.TabItemControl(Name="Lånesag", searchDepth=1)
    move_tab = tab_pane.TabItemControl(Name="Lånebevægelser", searchDepth=1)

    data = []

    for item in result_items:
        if (any(t in item.Name for t in ("(Accepteret med indefrysning)", "(Indfriet)"))
                and any(cpr in item.Name for cpr in owner_cprs)):
            item.GetSelectionItemPattern().Select()

            sag_tab.GetSelectionItemPattern().Select()
            cpr = tab_pane.EditControl(AutomationId="textBoxLaanansoegerCpr").GetValuePattern().Value
            name = tab_pane.EditControl(AutomationId="textBoxLaaneansoegerNavn").GetValuePattern().Value

            move_tab.GetSelectionItemPattern().Select()
            structura.ComboBoxControl(AutomationId="comboBoxLaanebevaegelserFilter").SendKey(Keys.VK_UP)

            row = structura.TableControl(AutomationId="gridControlLaanebevaegelser").CustomControl(Name="Row 1")
            row.SendKey(Keys.VK_HOME)
            date_ = row.DataItemControl(Name="Forfaldsdato row0").GetValuePattern().Value
            row.SendKey(Keys.VK_END)
            amount = row.DataItemControl(Name="Saldo row0").GetValuePattern().Value

            if "(Accepteret med indefrysning)" in item.Name:
                status = "Accepteret med indefrysning"
            else:
                status = row.DataItemControl(Name="Tekst row0").GetValuePattern().Value

            data.append(FrozenDebt(cpr, name, date_, amount, status))
    return data


def should_skip_due_to_frozen_debt(frozen_debt_list: list[FrozenDebt]) -> bool:
    """Return true if any of the frozen debt is sent to 'Indfrielse' within the last 3 days.
    Debt might not have been transfered to the correct systems yet and
    the task should be postponed to another day.

    Args:
        frozen_debt_list: The list of FrozenDebt objects to check.

    Returns:
        True if the task should be skipped for now.
    """
    today = datetime.today()
    three_days_ago = today - timedelta(days=3)
    pattern = re.compile(r"Indfrielse pr. (\d{2}\.\d{2}\.\d{4})")

    for frozen_debt in frozen_debt_list:
        re_match = pattern.match(frozen_debt.status)

        if re_match:
            date_string = re_match.group(1)
            indfrielse_date = datetime.strptime(date_string, "%d.%m.%Y")
            if three_days_ago < indfrielse_date:
                return True

    return False


def get_tax_data(property_number: str) -> list[tuple[str, str]]:
    """Search for the given property number and get all tax contributions.
    Also calculate the sum and add it to the result list.

    Args:
        property_number: The number of the property.

    Returns:
        A list of tuples containing [text, amount].
    """
    _search_property(property_number)

    structura = uiautomation.WindowControl(RegexName="KMD", AutomationId="MainForm", searchDepth=1)
    tree = structura.TreeControl(AutomationId="treeView", searchDepth=6)

    # Expand 'Skatter' and select latest element in the current year
    tax_group = tree.TreeItemControl(Name="Skatter")
    tax_group.GetExpandCollapsePattern().Expand()
    tax_elements: list[uiautomation.TreeItemControl] = tax_group.GetChildren()
    current_year = datetime.today().year
    for tax_element in reversed(tax_elements):
        if tax_element.Name.startswith(str(current_year)):
            tax_element.GetSelectionItemPattern().Select()
            break

    # Read tax table
    data = []

    tax_table = structura.TableControl(AutomationId="dataGridViewBidrag", searchDepth=13)
    for row in range(tax_table.GetGridPattern().RowCount):
        text = tax_table.EditControl(Name=f"Tekst Række {row}").GetValuePattern().Value
        if text == ".":
            break
        amount = tax_table.EditControl(Name=f"Ydelse Række {row}").GetValuePattern().Value
        data.append((text, amount))

    # Calculate sum
    total = 0
    for _, amount in data:
        total += float(amount.replace(".", "").replace(",", "."))
    total = round(total, 2)
    data.append(("Sum", f"{total:.2f}".replace(".", ",")))

    return data


def _search_property(property_number: str):
    """Search for a property and click 'Hent alle oplysninger'."""
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


def open_structura(username: str, password: str):
    """Open and login in to KMD Structura.

    Args:
        username: The username to use.
        password: The password to use.

    Raises:
        RuntimeError: If KMD Structura failed to maximize.
    """
    subprocess.Popen(r"C:\Program Files (x86)\KMD\KMD.JO.Structura\KMD.JO.Structura.exe", cwd=r"C:\Program Files (x86)\KMD\KMD.JO.Structura")  # pylint: disable=consider-using-with

    kmd_logon = uiautomation.WindowControl(AutomationId="MainLogonWindow", searchDepth=1)

    # Wait for logon window to load
    for _ in range(5):
        if len(kmd_logon.ComboBoxControl(AutomationId="UserPwComboBoxCics").GetSelectionPattern().GetSelection()) == 1:
            break
        time.sleep(1)

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
        except Exception:  # pylint: disable=broad-exception-caught
            pass
    else:
        raise RuntimeError("Couldn't maximize Structura")


def kill_structura():
    """Kill KMD Logon and KMD Structura."""
    os.system("taskkill /f /im KMD.JO.Structura.exe")
    os.system("taskkill /f /im KMD.YH.Security.Logon.Desktop.exe")
