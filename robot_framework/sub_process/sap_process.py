
from dataclasses import dataclass, field

from itk_dev_shared_components.sap import fmcacov, gridview_util


@dataclass
class MissingPaymentEntry:
    """A dataclass representing a single entry in a case."""
    title: str
    status: str
    amount: float

    def __repr__(self):
        return f"{self.title} | {self.status} | {self.amount:.2f} kr"


@dataclass
class MissingPaymentCase:
    """A dataclass representing a case with multiple entries."""
    title: str
    entries: list[MissingPaymentEntry] = field(default_factory=list)

    def append_entry(self, new_entry: MissingPaymentEntry):
        """Append an entry to the case. If an entry with the same
        title and status already exists, add their amounts and only
        keep one.
        """
        for old_entry in self.entries:
            if old_entry.title == new_entry.title and old_entry.status == new_entry.status:
                old_entry.amount += new_entry.amount
                return

        self.entries.append(new_entry)


@dataclass
class MissingPaymentPerson:
    """A dataclass representing a person with multiple cases."""
    name: str
    cpr: str
    cases: list[MissingPaymentCase] = field(default_factory=list)


def get_property_debt(session, cpr: str, name: str, property_number: str) -> MissingPaymentPerson:
    """Find the property debt on the given person and property.

    Args:
        session: The SAP session object.
        cpr: Cpr number of the person.
        name: Name of the person.
        property_number: The property number.

    Returns:
        A Person object describing the missing payments.
    """
    person = MissingPaymentPerson(name, cpr)

    fmcacov.open_forretningspartner(session, cpr)
    tree = session.findById("wnd[0]/shellcont/shell", False)

    if not tree:
        # In case the person can't be found in SAP
        return person

    node_items = _find_tree_items(tree, property_number)

    for key, text in node_items:
        case = MissingPaymentCase(text)

        tree.selectNode(key)
        tree.nodeContextMenu(key)
        tree.selectContextMenuItem("CON")

        postliste = session.findById("wnd[0]/usr/tabsDATA_DISP/tabpDATA_DISP_FC1/ssubDATA_DISP_SCA:RFMCA_COV:0202/cntlRFMCA_COV_0100_CONT5/shellcont/shell")
        gridview_util.scroll_entire_table(postliste, True)

        for row in range(postliste.RowCount - 1):
            status = postliste.GetCellTooltip(row, "AMPEL")
            row_text = postliste.GetCellValue(row, "TXTU2")
            amount = _convert_str_to_float(postliste.GetCellValue(row, "BETRW"))

            entry = MissingPaymentEntry(row_text, status, amount)
            case.append_entry(entry)

        person.cases.append(case)

    return person


def _find_tree_items(tree, property_number: str) -> list[str]:
    """Find all tree items that contains the given property number
    in their text.
    """
    items = []

    for key in tree.GetAllNodeKeys():
        text = tree.GetItemText(key, "Column2")

        if property_number in text:
            items.append((key, text))

    return items


def _convert_str_to_float(amount: str) -> float:
    """Convert a string amount to a float.
    Format: "1.234,56-"

    Args:
        amount: The string amount to convert.

    Returns:
        The amount as a float value
    """
    s = amount.replace(".", "").replace(",", ".")
    sign = -1 if s.endswith("-") else 1
    s = s.replace("-", "")

    return float(s) * sign
