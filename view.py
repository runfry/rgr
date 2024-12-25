import time
from typing import Tuple, List, Optional


class View:
    def show_menu(self) -> str:
        """Display main menu and get user choice."""
        while True:
            print("\n=== Database Management System ===")
            print("1. View Tables")
            print("2. View Table Columns")
            print("3. Add Data")
            print("4. Update Data")
            print("5. Delete Data")
            print("6. Generate Random Data")
            print("7. Search Data")
            print("8. Exit")

            choice = input("\nEnter your choice (1-8): ")
            if choice in ('1', '2', '3', '4', '5', '6', '7', '8'):
                return choice

            self.show_error("Invalid choice. Please try again.")

    def show_message(self, message: str, error: bool = False) -> None:
        """Display a message with appropriate formatting."""
        if error:
            print(f"\nERROR: {message}")
        else:
            print(f"\nINFO: {message}")
        time.sleep(1)

    def show_error(self, message: str) -> None:
        """Display error message."""
        self.show_message(message, error=True)

    def show_tables(self, tables: List[Tuple]) -> None:
        """Display available tables."""
        print("\n=== Available Tables ===")
        for i, (table,) in enumerate(tables, 1):
            print(f"{i}. {table}")

    def show_columns(self, columns: List[Tuple]) -> None:
        """Display table columns with their data types."""
        print("\n=== Column Information ===")
        print("Name".ljust(30) + "Type".ljust(20) + "Nullable")
        print("-" * 60)
        for column_name, data_type, nullable in columns:
            print(f"{column_name.ljust(30)}{data_type.ljust(20)}{nullable}")

    def get_table_name(self) -> str:
        """Get table name from user."""
        return input("\nEnter table name: ").strip().lower()

    def get_data_input(self, columns: List[Tuple]) -> dict:
        """Get data input for each column."""
        data = {}
        print("\nEnter values for each column (press Enter to skip optional fields):")

        for column_name, data_type, nullable in columns:
            while True:
                value = input(f"{column_name} ({data_type}): ").strip()

                if not value:
                    if nullable == 'NO':
                        print("This field is required!")
                        continue
                    break

                data[column_name] = value
                break

        return data

    def get_search_criteria(self) -> dict:
        """Get search criteria from user with expanded options."""
        criteria = {}
        print("\n=== Search Criteria ===")
        print("Enter search criteria (press Enter to skip):")

        # Supplier name search
        supplier_name = input("Supplier name (or part of it): ").strip()
        if supplier_name:
            criteria['supplier_name'] = supplier_name

        # Sparepart name search
        sparepart_name = input("Sparepart name (or part of it): ").strip()
        if sparepart_name:
            criteria['sparepart_name'] = sparepart_name

        # Quantity range
        try:
            min_qty = input("Minimum available quantity (or Enter to skip): ").strip()
            max_qty = input("Maximum available quantity (or Enter to skip): ").strip()
            if min_qty or max_qty:
                criteria['quantity_range'] = (
                    int(min_qty) if min_qty else None,
                    int(max_qty) if max_qty else None
                )
        except ValueError:
            self.show_error("Invalid quantity range - skipping")

        # Warehouse ID
        warehouse_id = input("Warehouse ID (or Enter to skip): ").strip()
        if warehouse_id.isdigit():
            criteria['warehouse_id'] = int(warehouse_id)

        # Available spareparts minimum
        try:
            min_parts = input("Minimum available spareparts in warehouse (or Enter to skip): ").strip()
            if min_parts:
                criteria['available_spareparts'] = int(min_parts)
        except ValueError:
            self.show_error("Invalid spareparts number - skipping")

        return criteria

    def show_search_results(self, results: List[Tuple], execution_time: float) -> None:
        """Display search results and execution time with strict single-line formatting."""
        print("\n=== Search Results ===")
        if not results:
            print("No results found.")
            return

        # Define headers with strict column widths
        headers = [
            ("Order ID", 12),
            ("Supplier ID", 25),
            ("Supplier Name", 50),
            ("Available Qty", 15),
            ("Phone Supplier", 15),
            ("Sparepart ID", 15),
            ("Sparepart Name", 15),
            ("Warehouse ID", 18),
            ("Warehouse Phone", 18),
        ]

        # Create separator line
        separator = "+"
        for _, width in headers:
            separator += "-" * width + "+"

        # Print table header
        print(separator)
        header_line = "|"
        for header, width in headers:
            header_line += f"{header:^{width}}|"  # Center-align headers
        print(header_line)
        print(separator)

        # Print data rows - ensuring single line formatting
        for row in results:
            data_line = "|"
            for i, (value, (_, width)) in enumerate(zip(row, headers)):
                # Handle None values and ensure they stay on the same line
                value_str = str(value) if value is not None else "None"
                # Remove any newlines or carriage returns that might exist in the data
                value_str = value_str.replace('\n', '').replace('\r', '')

                # Right-align numeric values, left-align text
                if isinstance(value, (int, float)) or (value_str.replace('-', '').isdigit()):
                    data_line += f"{value_str:>{width}}|"
                else:
                    data_line += f"{value_str:<{width}}|"
            print(data_line)

        print(separator)
        print(f"\nQuery execution time: {execution_time:.2f} ms")
        print(f"Total results: {len(results)}")

    def get_data_generation_params(self) -> Tuple[str, int]:
        """Get parameters for data generation."""
        table_name = self.get_table_name()
        while True:
            try:
                count = int(input("Enter number of rows to generate: "))
                if count <= 0:
                    raise ValueError
                return table_name, count
            except ValueError:
                self.show_error("Please enter a valid positive number")