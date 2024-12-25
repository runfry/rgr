from model import Model
from view import View
from typing import Optional
import sys


class Controller:
    def __init__(self):
        self.view = View()
        try:
            self.model = Model()
            self.view.show_message("Successfully connected to database")
        except Exception as e:
            self.view.show_error(f"Database connection failed: {e}")
            sys.exit(1)

    def run(self):
        """Main application loop."""
        while True:
            try:
                choice = self.view.show_menu()
                if choice == '1':
                    self.view_tables()
                elif choice == '2':
                    self.view_columns()
                elif choice == '3':
                    self.add_data()
                elif choice == '4':
                    self.update_data()
                elif choice == '5':
                    self.delete_data()
                elif choice == '6':
                    self.generate_data()
                elif choice == '7':
                    self.search_data()
                elif choice == '8':
                    self.view.show_message("Goodbye!")
                    break
            except Exception as e:
                self.view.show_error(f"An unexpected error occurred: {e}")

    def view_tables(self):
        """Display all tables in the database."""
        tables = self.model.get_all_tables()
        if tables:
            self.view.show_tables(tables)
        else:
            self.view.show_error("No tables found or error occurred")

    def view_columns(self):
        """Display columns for a specified table."""
        table_name = self.view.get_table_name()
        columns = self.model.get_all_columns(table_name)
        if columns:
            self.view.show_columns(columns)
        else:
            self.view.show_error(f"Table '{table_name}' not found or error occurred")

    def add_data(self):
        """Add new data to a table."""
        table_name = self.view.get_table_name()
        columns = self.model.get_all_columns(table_name)

        if not columns:
            self.view.show_error(f"Table '{table_name}' not found")
            return

        data = self.view.get_data_input(columns)
        if data:
            success, message = self.model.add_data(table_name, data)
            if success:
                self.view.show_message(message)
            else:
                self.view.show_error(message)
        else:
            self.view.show_error("No data provided")

    def update_data(self):
        """Update existing data in a table."""
        table_name = self.view.get_table_name()
        columns = self.model.get_all_columns(table_name)

        if not columns:
            self.view.show_error(f"Table '{table_name}' not found")
            return

        # Get primary key column (assuming first column is primary key)
        id_column = columns[0][0]
        id_value = input(f"Enter {id_column} of record to update: ")

        # Get new values
        print("\nEnter new values (press Enter to skip fields you don't want to update):")
        data = {}
        for column_name, data_type, nullable in columns:
            if column_name != id_column:  # Skip the ID column
                value = input(f"{column_name} ({data_type}): ").strip()
                if value:  # Only include fields that were filled in
                    data[column_name] = value

        if data:
            success, message = self.model.update_data(table_name, id_column, id_value, data)
            if success:
                self.view.show_message(message)
            else:
                self.view.show_error(message)
        else:
            self.view.show_error("No update data provided")

    def delete_data(self):
        """Delete data from a table."""
        table_name = self.view.get_table_name()
        columns = self.model.get_all_columns(table_name)

        if not columns:
            self.view.show_error(f"Table '{table_name}' not found")
            return

        # Get primary key column (assuming first column is primary key)
        id_column = columns[0][0]
        id_value = input(f"Enter {id_column} of record to delete: ")

        # Confirm deletion
        confirm = input("Are you sure you want to delete this record? (y/n): ")
        if confirm.lower() == 'y':
            success, message = self.model.delete_data(table_name, id_column, id_value)
            if success:
                self.view.show_message(message)
            else:
                self.view.show_error(message)

    def generate_data(self):
        """Generate random test data."""
        table_name, count = self.view.get_data_generation_params()
        success, message = self.model.generate_random_data(table_name, count)
        if success:
            self.view.show_message(message)
        else:
            self.view.show_error(message)

    def search_data(self):
        """Search data across tables."""
        criteria = self.view.get_search_criteria()
        if criteria:
            results, execution_time = self.model.search_data(criteria)
            self.view.show_search_results(results, execution_time)
        else:
            self.view.show_error("No search criteria provided")