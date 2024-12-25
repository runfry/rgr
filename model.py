import psycopg2
from datetime import datetime
import random
import string
import time
from typing import List, Tuple, Dict, Optional, Any


class Model:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname='postgres',
                user='postgres',
                password='8962',
                host='localhost',
                port=5432
            )
            self.conn.autocommit = False
        except psycopg2.Error as e:
            raise Exception(f"Database connection failed: {e}")

    def get_all_tables(self) -> List[Tuple]:
        """Get all tables from the database."""
        c = self.conn.cursor()
        try:
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            return c.fetchall()
        except psycopg2.Error as e:
            print(f"Error fetching tables: {e}")
            return []
        finally:
            c.close()

    def get_all_columns(self, table_name: str) -> List[Tuple]:
        """Get all columns for a specific table."""
        c = self.conn.cursor()
        try:
            c.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            return c.fetchall()
        except psycopg2.Error as e:
            print(f"Error fetching columns: {e}")
            return []
        finally:
            c.close()

    def search_data(self, criteria: Dict[str, Any]) -> Tuple[List[Tuple], float]:
        """Perform a comprehensive search across all related tables with complete information."""
        start_time = time.time()
        c = self.conn.cursor()

        try:
            # Build query to show all information from all tables
            base_query = """
                SELECT DISTINCT
                    -- Sorting columns (needed for ORDER BY with DISTINCT)
                    COALESCE(o.order_id, 0) as sort_order_id,
                    COALESCE(s.supplier_id, 0) as sort_supplier_id,
                    COALESCE(sp.sparepart_id, 0) as sort_sparepart_id,
                    COALESCE(w.warehouse_id, 0) as sort_warehouse_id,

                    -- Order information
                    o.order_id,

                    -- Supplier information
                    s.supplier_id,
                    s.supplier_name,
                    s.available_quantity AS supplier_quantity,
                    s.phone_supplier,

                    -- Sparepart information
                    sp.sparepart_id,
                    sp.sparepart_name,

                    -- Warehouse information
                    w.warehouse_id,
                    w.warehouse_phone,
                    w.available_spareparts

                FROM sparepart sp
                FULL OUTER JOIN "order" o ON sp.sparepart_id = o.sparepart_id
                FULL OUTER JOIN supplier s ON o.supplier_id = s.supplier_id
                FULL OUTER JOIN warehouse w ON o.warehouse_id = w.warehouse_id
                WHERE 1=1
            """

            conditions = []
            params = []

            # Build search conditions
            if 'supplier_name' in criteria and criteria['supplier_name']:
                conditions.append("""
                    (LOWER(s.supplier_name) LIKE LOWER(%s))
                """)
                params.append(f"%{criteria['supplier_name']}%")

            if 'sparepart_name' in criteria and criteria['sparepart_name']:
                conditions.append("""
                    (LOWER(sp.sparepart_name) LIKE LOWER(%s))
                """)
                params.append(f"%{criteria['sparepart_name']}%")

            if 'quantity_range' in criteria:
                min_qty, max_qty = criteria['quantity_range']
                if min_qty is not None:
                    conditions.append("(s.available_quantity >= %s OR w.available_spareparts >= %s)")
                    params.extend([min_qty, min_qty])
                if max_qty is not None:
                    conditions.append("(s.available_quantity <= %s OR w.available_spareparts <= %s)")
                    params.extend([max_qty, max_qty])

            if 'warehouse_id' in criteria and criteria['warehouse_id']:
                conditions.append("(w.warehouse_id = %s)")
                params.append(criteria['warehouse_id'])

            if 'available_spareparts' in criteria and criteria['available_spareparts']:
                conditions.append("""
                    (w.available_spareparts >= %s OR 
                     s.available_quantity >= %s)
                """)
                params.extend([criteria['available_spareparts'], criteria['available_spareparts']])

            # Add WHERE conditions if any exist
            if conditions:
                base_query += " AND (" + " OR ".join(conditions) + ")"

            # Add ordering using the sort columns we included in SELECT
            base_query += """
                ORDER BY 
                    sort_order_id,
                    sort_supplier_id,
                    sort_sparepart_id,
                    sort_warehouse_id
            """

            # Execute the query
            c.execute(base_query, params)
            results = c.fetchall()

            # Remove the sorting columns before returning results
            # (skip first 4 columns which were added for sorting)
            results = [row[4:] for row in results]

            execution_time = (time.time() - start_time) * 1000
            return results, execution_time

        except psycopg2.Error as e:
            print(f"Search error: {e}")
            return [], 0
        finally:
            c.close()

    def generate_random_data(self, table_name: str, count: int) -> Tuple[bool, str]:
        """Generate random data using PostgreSQL functions."""
        c = self.conn.cursor()
        try:
            # First, find the maximum existing ID for the table
            id_column = f"{table_name}_id"
            c.execute(f"""
                SELECT COALESCE(MAX({id_column}), 0)
                FROM "{table_name}";
            """)
            max_id = c.fetchone()[0]

            if table_name == 'supplier':
                c.execute("""
                    INSERT INTO supplier (supplier_id, available_quantity, phone_supplier, supplier_name)
                    SELECT 
                        s.id,
                        floor(random() * 1000 + 1)::integer,
                        floor(random() * 900000000 + 100000000)::integer,
                        'Sup_' || substr(md5(random()::text), 1, 20)
                    FROM generate_series(%s, %s) AS s(id)
                    RETURNING supplier_id;
                """, [max_id + 1, max_id + count])

            elif table_name == 'warehouse':
                c.execute("""
                    INSERT INTO warehouse (warehouse_id, warehouse_phone, available_spareparts)
                    SELECT 
                        s.id,
                        floor(random() * 900000000 + 100000000)::integer,
                        floor(random() * 1000 + 1)::integer
                    FROM generate_series(%s, %s) AS s(id)
                    RETURNING warehouse_id;
                """, [max_id + 1, max_id + count])

            elif table_name == 'sparepart':
                c.execute("""
                    INSERT INTO sparepart (sparepart_id, sparepart_name)
                    SELECT 
                        s.id,
                        'Part_' || substr(md5(random()::text), 1, 20)
                    FROM generate_series(%s, %s) AS s(id)
                    RETURNING sparepart_id;
                """, [max_id + 1, max_id + count])

            elif table_name == 'order':
                # First check if we have enough related records
                c.execute("SELECT COUNT(*) FROM supplier")
                supplier_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM sparepart")
                sparepart_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM warehouse")
                warehouse_count = c.fetchone()[0]

                if supplier_count == 0:
                    return False, "No suppliers found. Please add suppliers first."
                if sparepart_count == 0:
                    return False, "No spareparts found. Please add spareparts first."
                if warehouse_count == 0:
                    return False, "No warehouses found. Please add warehouses first."

                # Generate orders with random related IDs for each order
                c.execute("""
                    WITH order_data AS (
                        SELECT 
                            s.id as order_id,
                            (SELECT supplier_id FROM supplier ORDER BY random() LIMIT 1) as supplier_id,
                            (SELECT sparepart_id FROM sparepart ORDER BY random() LIMIT 1) as sparepart_id,
                            (SELECT warehouse_id FROM warehouse ORDER BY random() LIMIT 1) as warehouse_id
                        FROM generate_series(%s, %s) AS s(id)
                    )
                    INSERT INTO "order" (order_id, supplier_id, sparepart_id, warehouse_id)
                    SELECT 
                        order_id,
                        supplier_id,
                        sparepart_id,
                        warehouse_id
                    FROM order_data
                    RETURNING order_id;
                """, [max_id + 1, max_id + count])

            else:
                return False, f"Random data generation not implemented for table {table_name}"

            self.conn.commit()
            return True, f"Successfully generated {count} records for {table_name}"

        except psycopg2.Error as e:
            self.conn.rollback()
            return False, f"Data generation failed: {e}"
        finally:
            c.close()

    def add_data(self, table_name: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Add new data to specified table."""
        c = self.conn.cursor()
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders}) RETURNING *;'

            c.execute(query, list(data.values()))
            result = c.fetchone()

            self.conn.commit()
            return True, f"Data added successfully with ID: {result[0]}"

        except psycopg2.Error as e:
            self.conn.rollback()
            return False, f"Failed to add data: {e}"
        finally:
            c.close()

    def update_data(self, table_name: str, id_column: str, id_value: Any, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update existing record."""
        c = self.conn.cursor()
        try:
            set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
            query = f'UPDATE "{table_name}" SET {set_clause} WHERE {id_column} = %s RETURNING *;'

            values = list(data.values()) + [id_value]
            c.execute(query, values)

            if c.rowcount == 0:
                self.conn.rollback()
                return False, f"No record found with {id_column} = {id_value}"

            self.conn.commit()
            return True, "Data updated successfully"

        except psycopg2.Error as e:
            self.conn.rollback()
            return False, f"Update failed: {e}"
        finally:
            c.close()

    def delete_data(self, table_name: str, id_column: str, id_value: Any) -> Tuple[bool, str]:
        """Delete record with dependency checking."""
        c = self.conn.cursor()
        try:
            # First check for foreign key dependencies
            c.execute("""
                SELECT COUNT(*) 
                FROM information_schema.table_constraints tc 
                JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = %s 
                AND ccu.column_name = %s;
            """, (table_name, id_column))

            if c.fetchone()[0] > 0:
                # Check for actual dependent records
                c.execute(f'SELECT EXISTS (SELECT 1 FROM "{table_name}" WHERE {id_column} = %s);', [id_value])
                if c.fetchone()[0]:
                    return False, "Cannot delete: record has dependent entries"

            c.execute(f'DELETE FROM "{table_name}" WHERE {id_column} = %s RETURNING *;', [id_value])

            if c.rowcount == 0:
                self.conn.rollback()
                return False, f"No record found with {id_column} = {id_value}"

            self.conn.commit()
            return True, "Record deleted successfully"

        except psycopg2.Error as e:
            self.conn.rollback()
            return False, f"Deletion failed: {e}"
        finally:
            c.close()

    def __del__(self):
        """Ensure database connection is closed."""
        if hasattr(self, 'conn'):
            self.conn.close()