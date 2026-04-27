"""This module is responsible for the Doc2Archive MSSQL database."""
import pyodbc


PROPERTIES_TABLE = "dbo.ejendomsskat_properties"
REPORTS_TABLE = "dbo.ejendomsskat_reports"


class DocDatabase:
    """A proxy class for the database."""
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._create_tables()

    def _create_tables(self):
        """Create the needed database tables if they don't exist."""
        connection = pyodbc.connect(self.connection_string)

        connection.execute(
            f"""
            IF OBJECT_ID(N'{REPORTS_TABLE}', N'U') IS NULL
            CREATE TABLE {REPORTS_TABLE}
            (
                id INT IDENTITY(1,1) PRIMARY KEY,
                report_date NVARCHAR(50),
                tax_year NVARCHAR(50)
            )
            """
        )

        connection.execute(
            f"""
            IF OBJECT_ID(N'{PROPERTIES_TABLE}', N'U') IS NULL
            CREATE TABLE {PROPERTIES_TABLE}
            (
                id INT IDENTITY(1,1) PRIMARY KEY,
                property_number NVARCHAR(50),
                report_id INT REFERENCES {REPORTS_TABLE} (id)
            )
            """
        )

        connection.execute(
            f"""
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE name = 'property_number_index'
                AND object_id = OBJECT_ID(N'{PROPERTIES_TABLE}')
            )
            CREATE INDEX property_number_index ON {PROPERTIES_TABLE} (property_number)
            """
        )

        connection.commit()

    def add_report_data(self, report_date: str, tax_year: str, property_list: list[str]):
        """Add new report data to the database.

        Args:
            report_date: The date of the report.
            tax_year: The tax year of the report.
            property_list: The list of properties in the report table.
        """
        connection = pyodbc.connect(self.connection_string)

        cursor = connection.cursor()

        cursor.execute(
            f"""
            INSERT INTO {REPORTS_TABLE} (report_date, tax_year)
            OUTPUT INSERTED.id
            VALUES (?, ?)
            """,
            report_date, tax_year
        )

        report_id = cursor.fetchone()[0]

        for property_ in property_list:
            cursor.execute(
                f"""
                INSERT INTO {PROPERTIES_TABLE} (property_number, report_id)
                VALUES (?, ?)
                """,
                property_, report_id
            )

        connection.commit()

    def is_report_in_database(self, report_date: str, tax_year: str) -> bool:
        """Check if a given report is already stored in the database.

        Args:
            report_date: The date of the report.
            tax_year: The tax year of the report.

        Returns:
            True if the report is in the database.
        """
        connection = pyodbc.connect(self.connection_string)

        cursor = connection.execute(
            f"SELECT 1 FROM {REPORTS_TABLE} WHERE report_date = ? AND tax_year = ?",
            report_date, tax_year
        )
        return cursor.fetchone() is not None

    def search_property(self, property_number: str) -> list[dict[str, str]]:
        """Search for a property number in the doc database.

        Args:
            property_number: The property number to search for.

        Returns:
            A list of dictionaries describing the results.
        """
        connection = pyodbc.connect(self.connection_string)

        cursor = connection.execute(
            f"""
            SELECT * FROM {PROPERTIES_TABLE}
            JOIN {REPORTS_TABLE} ON {PROPERTIES_TABLE}.report_id = {REPORTS_TABLE}.id
            WHERE property_number = ?
            """,
            property_number
        )
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
