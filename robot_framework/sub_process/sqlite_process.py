
import sqlite3


class DocDatabase:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._create_tables()

    def _create_tables(self):
        """Create the needed database tables if the don't exist."""
        connection = sqlite3.connect(self.database_path)

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports
            (
                report_date,
                tax_year
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS properties
            (
                property_number,
                report_id REFERENCES reports (rowid)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS property_number_index ON properties (property_number)
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
        connection = sqlite3.connect(self.database_path)

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO reports
            (report_date, tax_year)
            VALUES
            (?, ?)
            """,
            (report_date, tax_year)
        )

        report_id = cursor.lastrowid

        for property in property_list:
            cursor.execute(
                """
                INSERT INTO properties
                (property_number, report_id)
                VALUES
                (?, ?)
                """,
                (property, report_id)
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
        connection = sqlite3.connect(self.database_path)

        cursor = connection.execute("SELECT * FROM reports WHERE report_date = ? AND tax_year = ?", (report_date, tax_year))
        return len(cursor.fetchall()) > 0


    def search_property(self, property_number: str) -> list[dict[str, str]]:
        """Search for a property number in the doc database.

        Args:
            property_number: The property number to search for.

        Returns:
            A list of dictionaries describing the results.
        """
        connection = sqlite3.connect(self.database_path)

        def dict_factory(cursor, row):
            """Factory function to convert rows to dictionaries."""
            fields = [column[0] for column in cursor.description]
            return {key: value for key, value in zip(fields, row)}

        connection.row_factory = dict_factory

        cursor = connection.execute(
            """
            SELECT * FROM properties
            JOIN reports ON properties.report_id = reports.rowid
            WHERE property_number = ?
            """,
            (property_number,)
        )
        return cursor.fetchall()


if __name__ == '__main__':

    import os
    os.remove("test_db.db")

    db = DocDatabase("test_db.db")
    db._create_tables()
    db.add_report_data(
        "123456", 
        "2021", 
        [chr(i) for i in range(65, 75)]
    )
    db.add_report_data(
        "ahdbdhe", 
        "2022", 
        [chr(i) for i in range(65, 75)]
    )

    result = db.search_property("A")
    print(result)