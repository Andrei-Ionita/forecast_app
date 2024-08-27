import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta

# =============================================================== Rendering the Indisponibility database for Solina=========================================================
def get_connection():
    """Get a connection to the SQLite database."""
    return sqlite3.connect('indisponibility.db')

def create_table():
    """Create the indisponibility table if it does not exist."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS indisponibility_Solina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            Interval_from INT NOT NULL,
            Interval_to INT NOT NULL,
            limitation_percentage REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_indisponibility_to_db(limitation_type, start_date, end_date, interval_from, interval_to, percentage):
    """Add indisponibility data to the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO indisponibility_Solina (type, start_date, end_date, interval_from, interval_to, limitation_percentage)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (limitation_type, start_date, end_date, interval_from, interval_to, percentage))
    conn.commit()
    conn.close()

def delete_indisponibility_from_db(entry_id):
    """Delete indisponibility data from the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        DELETE FROM indisponibility_Solina WHERE id = ?
    ''', (entry_id,))
    conn.commit()
    conn.close()

def render_indisponibility_db_Solina():
    """Render and manage the indisponibility database for Solina client."""
    create_table()

    # Widget for Grid Limitation
    st.subheader("Grid Limitation")
    grid_start_date = st.date_input("Grid Limitation Start Date", value=date.today())
    grid_end_date = st.date_input("Grid Limitation End Date", value=date.today())
    grid_limitation_percentage = st.number_input("Grid Limitation Percentage", min_value=0.0, max_value=100.0, value=50.0)
    grid_interval_from = st.number_input("Interval From (Grid)", min_value=0, max_value=24, value=1)
    grid_interval_to = st.number_input("Interval To (Grid)", min_value=0, max_value=24, value=24)

    if st.button("Add Grid Limitation"):
        add_indisponibility_to_db("Grid Limitation", grid_start_date, grid_end_date, grid_interval_from, grid_interval_to, grid_limitation_percentage)
        st.success("Grid Limitation added successfully!")

    # Widget for Asset Limitation
    st.subheader("Asset Limitation")
    asset_start_date = st.date_input("Asset Limitation Start Date", value=date.today())
    asset_end_date = st.date_input("Asset Limitation End Date", value=date.today())
    asset_limitation_percentage = st.number_input("Asset Limitation Percentage", min_value=0.0, max_value=100.0, value=50.0)
    asset_interval_from = st.number_input("Interval From (Asset)", min_value=0, max_value=24, value=1)
    asset_interval_to = st.number_input("Interval To (Asset)", min_value=0, max_value=24, value=24)

    if st.button("Add Asset Limitation"):
        add_indisponibility_to_db("Asset Limitation", asset_start_date, asset_end_date, asset_interval_from, asset_interval_to, asset_limitation_percentage)
        st.success("Asset Limitation added successfully!")

    # Retrieve and display the stored indisponibility data from the database
    conn = get_connection()
    indisponibility_df = pd.read_sql_query("SELECT * FROM indisponibility_Solina", conn)
    st.subheader("Indisponibility Data")
    st.dataframe(indisponibility_df)
    conn.close()

    # Widget to select and remove an entry
    st.subheader("Remove an Entry")
    entry_id_to_delete = st.selectbox("Select Entry ID to Delete", indisponibility_df['id'])

    if st.button("Delete Selected Entry"):
        delete_indisponibility_from_db(entry_id_to_delete)
        st.success(f"Entry ID {entry_id_to_delete} deleted successfully!")
        st.experimental_rerun()  # Rerun to refresh the displayed data

    # Calculate tomorrow's date
    tomorrow = date.today() + timedelta(days=1)

    # Query the database for any indisponibility scheduled for tomorrow
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT Interval_from, Interval_to, limitation_percentage 
        FROM indisponibility_Solina 
        WHERE start_date <= ? AND end_date >= ?
    ''', (tomorrow, tomorrow))

    # Fetch the result
    result = c.fetchone()
    conn.close()

    # Assign the values to variables if there is an indisponibility for tomorrow
    if result:
        interval_from, interval_to, limitation_percentage = result
        return interval_from, interval_to, limitation_percentage

    return None

# Initialize the database connection
# conn = sqlite3.connect('indisponibility.db')
# c = conn.cursor()

# # Function to get all table names
# def get_all_tables():
#     c.execute("SELECT name FROM sqlite_master WHERE type='table';")
#     tables = c.fetchall()
#     return [table[0] for table in tables]

# # Function to delete a selected table
# def delete_table(table_name):
#     c.execute(f"DROP TABLE IF EXISTS {table_name}")
#     conn.commit()

# # Retrieve and display all table names
# st.header("Database Tables")
# tables = get_all_tables()

# if tables:
#     st.subheader("Available Tables")
#     st.write(tables)

#     # Widget to select and delete a table
#     st.subheader("Delete a Table")
#     table_to_delete = st.selectbox("Select a Table to Delete", tables)

#     if st.button("Delete Selected Table"):
#         delete_table(table_to_delete)
#         st.success(f"Table '{table_to_delete}' deleted successfully!")
#         st.experimental_rerun()  # Rerun to refresh the list of tables
# else:
#     st.warning("No tables found in the database.")

# # Close the database connection when done
# conn.close()

# =============================================================== Rendering the Indisponibility database for Astro=========================================================
def render_indisponibility_db_Astro():
    # Initialize the database connection
    conn = sqlite3.connect('indisponibility.db')
    c = conn.cursor()

    # Create the table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS indisponibility_Astro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            Interval_from INT NOT NULL,
            Interval_to INT NOT NULL,
            limitation_percentage REAL NOT NULL
        )
    ''')
    conn.commit()

    # Function to add indisponibility data to the database
    def add_indisponibility_to_db(limitation_type, start_date, end_date, interval_from, interval_to, percentage):
        c.execute('''
            INSERT INTO indisponibility_Astro (type, start_date, end_date, interval_from, interval_to, limitation_percentage)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (limitation_type, start_date, end_date, interval_from, interval_to, percentage))
        conn.commit()

    # Function to delete indisponibility data from the database
    def delete_indisponibility_from_db(entry_id):
        c.execute('''
            DELETE FROM indisponibility_Astro WHERE id = ?
        ''', (entry_id,))
        conn.commit()
    # Widget for Grid Limitation
    st.subheader("Grid Limitation")
    grid_start_date = st.date_input("Grid Limitation Start Date", value=date.today())
    grid_end_date = st.date_input("Grid Limitation End Date", value=date.today())
    grid_limitation_percentage = st.number_input("Grid Limitation Percentage", min_value=0.0, max_value=100.0, value=50.0)
    grid_interval_from = st.number_input("Interval From (Grid)", min_value=0, max_value=24, value=1)
    grid_interval_to = st.number_input("Interval To (Grid)", min_value=0, max_value=24, value=24)

    if st.button("Add Grid Limitation"):
        add_indisponibility_to_db("Grid Limitation", grid_start_date, grid_end_date, grid_interval_from, grid_interval_to, grid_limitation_percentage)
        st.success("Grid Limitation added successfully!")

    # Widget for Asset Limitation
    st.subheader("Asset Limitation")
    asset_start_date = st.date_input("Asset Limitation Start Date", value=date.today())
    asset_end_date = st.date_input("Asset Limitation End Date", value=date.today())
    asset_limitation_percentage = st.number_input("Asset Limitation Percentage", min_value=0.0, max_value=100.0, value=50.0)
    asset_interval_from = st.number_input("Interval From (Asset)", min_value=0, max_value=24, value=1)
    asset_interval_to = st.number_input("Interval To (Asset)", min_value=0, max_value=24, value=24)

    if st.button("Add Asset Limitation"):
        add_indisponibility_to_db("Asset Limitation", asset_start_date, asset_end_date, asset_interval_from, asset_interval_to, asset_limitation_percentage)
        st.success("Asset Limitation added successfully!")

    # Retrieve and display the stored indisponibility data from the database
    st.subheader("Indisponibility Data")
    indisponibility_df = pd.read_sql_query("SELECT * FROM indisponibility_Astro", conn)
    st.dataframe(indisponibility_df)

    # Widget to select and remove an entry
    st.subheader("Remove an Entry")
    entry_id_to_delete = st.selectbox("Select Entry ID to Delete", indisponibility_df['id'])

    if st.button("Delete Selected Entry"):
        delete_indisponibility_from_db(entry_id_to_delete)
        st.success(f"Entry ID {entry_id_to_delete} deleted successfully!")
        st.experimental_rerun()  # Rerun to refresh the displayed data

    # Calculate tomorrow's date
    tomorrow = date.today() + timedelta(days=1)

    # Query the database for any indisponibility scheduled for tomorrow
    c.execute('''
        SELECT Interval_from, Interval_to, limitation_percentage 
        FROM indisponibility_Astro 
        WHERE start_date <= ? AND end_date >= ?
    ''', (tomorrow, tomorrow))

    # Fetch the result
    result = c.fetchone()

    # Assign the values to variables if there is an indisponibility for tomorrow
    if result:
        interval_from, interval_to, limitation_percentage = result
        limitation_percentage = result[2]
        interval_from = result[0]
        interval_to = result[1]
        # st.write(f"Indisponibility found for tomorrow: Interval from {interval_from} to {interval_to}, Limitation percentage: {limitation_percentage}%")
    else:
        pass
        # st.write("No indisponibility scheduled for tomorrow.")

    # Close the database connection when done
    conn.close()
    if result:
        return interval_from, interval_to, limitation_percentage

#=============================================================== Rendering the Indisponibility database for Imperial=========================================================
def render_indisponibility_db_Imperial():
    # Initialize the database connection
    conn = sqlite3.connect('indisponibility.db')
    c = conn.cursor()

    # Create the table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS indisponibility_Imperial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            Interval_from INT NOT NULL,
            Interval_to INT NOT NULL,
            limitation_percentage REAL NOT NULL
        )
    ''')
    conn.commit()

    # Function to add indisponibility data to the database
    def add_indisponibility_to_db(limitation_type, start_date, end_date, interval_from, interval_to, percentage):
        c.execute('''
            INSERT INTO indisponibility_Imperial (type, start_date, end_date, interval_from, interval_to, limitation_percentage)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (limitation_type, start_date, end_date, interval_from, interval_to, percentage))
        conn.commit()

    # Function to delete indisponibility data from the database
    def delete_indisponibility_from_db(entry_id):
        c.execute('''
            DELETE FROM indisponibility_Imperial WHERE id = ?
        ''', (entry_id,))
        conn.commit()
    # Widget for Grid Limitation
    st.subheader("Grid Limitation")
    grid_start_date = st.date_input("Grid Limitation Start Date", value=date.today())
    grid_end_date = st.date_input("Grid Limitation End Date", value=date.today())
    grid_limitation_percentage = st.number_input("Grid Limitation Percentage", min_value=0.0, max_value=100.0, value=50.0)
    grid_interval_from = st.number_input("Interval From (Grid)", min_value=0, max_value=24, value=1)
    grid_interval_to = st.number_input("Interval To (Grid)", min_value=0, max_value=24, value=24)

    if st.button("Add Grid Limitation"):
        add_indisponibility_to_db("Grid Limitation", grid_start_date, grid_end_date, grid_interval_from, grid_interval_to, grid_limitation_percentage)
        st.success("Grid Limitation added successfully!")

    # Widget for Asset Limitation
    st.subheader("Asset Limitation")
    asset_start_date = st.date_input("Asset Limitation Start Date", value=date.today())
    asset_end_date = st.date_input("Asset Limitation End Date", value=date.today())
    asset_limitation_percentage = st.number_input("Asset Limitation Percentage", min_value=0.0, max_value=100.0, value=50.0)
    asset_interval_from = st.number_input("Interval From (Asset)", min_value=0, max_value=24, value=1)
    asset_interval_to = st.number_input("Interval To (Asset)", min_value=0, max_value=24, value=24)

    if st.button("Add Asset Limitation"):
        add_indisponibility_to_db("Asset Limitation", asset_start_date, asset_end_date, asset_interval_from, asset_interval_to, asset_limitation_percentage)
        st.success("Asset Limitation added successfully!")

    # Retrieve and display the stored indisponibility data from the database
    st.subheader("Indisponibility Data")
    indisponibility_df = pd.read_sql_query("SELECT * FROM indisponibility_Imperial", conn)
    st.dataframe(indisponibility_df)

    # Widget to select and remove an entry
    st.subheader("Remove an Entry")
    entry_id_to_delete = st.selectbox("Select Entry ID to Delete", indisponibility_df['id'])

    if st.button("Delete Selected Entry"):
        delete_indisponibility_from_db(entry_id_to_delete)
        st.success(f"Entry ID {entry_id_to_delete} deleted successfully!")
        st.experimental_rerun()  # Rerun to refresh the displayed data

    # Calculate tomorrow's date
    tomorrow = date.today() + timedelta(days=1)

    # Query the database for any indisponibility scheduled for tomorrow
    c.execute('''
        SELECT Interval_from, Interval_to, limitation_percentage 
        FROM indisponibility_Imperial 
        WHERE start_date <= ? AND end_date >= ?
    ''', (tomorrow, tomorrow))

    # Fetch the result
    result = c.fetchone()

    # Assign the values to variables if there is an indisponibility for tomorrow
    if result:
        interval_from, interval_to, limitation_percentage = result
        limitation_percentage = result[2]
        interval_from = result[0]
        interval_to = result[1]
        # st.write(f"Indisponibility found for tomorrow: Interval from {interval_from} to {interval_to}, Limitation percentage: {limitation_percentage}%")
    else:
        pass
        # st.write("No indisponibility scheduled for tomorrow.")

    # Close the database connection when done
    conn.close()
    if result:
        return interval_from, interval_to, limitation_percentage