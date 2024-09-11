import streamlit as st
import psycopg2
import pandas as pd
from datetime import date, timedelta

# Heroku PostgreSQL connection details
DB_URL = "postgresql://u6vgnrtb422bju:p593a702cae233b84c4a2a29ad9f8f13116fa3a407ea6b2ed91d97280a5e17d9c@c8lj070d5ubs83.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d67n79bcvb33fq"

# Establish a connection to the PostgreSQL database
def get_connection():
    try:
        conn = psycopg2.connect(DB_URL, sslmode='require')
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

# Load data from the PostgreSQL table
def load_data(table_name):
    conn = get_connection()
    if conn:
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    else:
        return pd.DataFrame()

# Save the DataFrame back to the PostgreSQL table
def save_data(table_name, df):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name};")
        for index, row in df.iterrows():
            cursor.execute(
                f"INSERT INTO {table_name} (id, type, start_date, end_date, interval_from, interval_to, limitation_percentage) "
                f"VALUES (%s, %s, %s, %s, %s, %s, %s);",
                (row['id'], row['type'], row['start_date'], row['end_date'], row['Interval_from'], row['Interval_to'], row['limitation_percentage'])
            )
        conn.commit()
        cursor.close()
        conn.close()
    else:
        st.error("Failed to connect to the database.")

# Add a new indisponibility entry to the database
def add_indisponibility_to_postgres(table_name, limitation_type, start_date, end_date, interval_from, interval_to, percentage):
    df = load_data(table_name)
    
    # Generate a new ID (assuming IDs are integers and incrementing by 1)
    if df.empty:
        new_id = 1
    else:
        new_id = df['id'].max() + 1
    
    new_entry = pd.DataFrame({
        "id": [new_id],
        "type": [limitation_type],
        "start_date": [start_date],
        "end_date": [end_date],
        "Interval_from": [interval_from],
        "Interval_to": [interval_to],
        "limitation_percentage": [percentage]
    })
    
    df = pd.concat([df, new_entry], ignore_index=True)
    save_data(table_name, df)
    st.success(f"New {limitation_type} entry added successfully!")

# Check for indisponibilities scheduled for tomorrow and return relevant values
def check_tomorrow_indisponibilities(table_name):
    df = load_data(table_name)

    # Debugging: Print the columns in the DataFrame
    # st.write("Columns in the DataFrame:", df.columns)

    # Convert start_date and end_date to datetime objects
    df['start_date'] = pd.to_datetime(df['start_date']).dt.date
    df['end_date'] = pd.to_datetime(df['end_date']).dt.date

    # Calculate tomorrow's date
    tomorrow = date.today() + timedelta(days=1)

    # Filter for indisponibilities that are active tomorrow
    upcoming = df[(df['start_date'] <= tomorrow) & (df['end_date'] >= tomorrow)]

    # Initialize the variables with default values
    interval_from = interval_to = limitation_percentage = None

    if not upcoming.empty:
        try:
            # Ensure that the column names exist in the DataFrame
            interval_from, interval_to, limitation_percentage = upcoming.iloc[0][['interval_from', 'interval_to', 'limitation_percentage']]
            st.warning(f"Indisponibility found for tomorrow: Interval from {interval_from} to {interval_to}, Limitation percentage: {limitation_percentage}%")
        except KeyError as e:
            st.error(f"Column names error: {e}. Please check the column names in the database.")
    else:
        st.write("No indisponibility scheduled for tomorrow.")

    return interval_from, interval_to, limitation_percentage



# Render and manage the indisponibility database for the given client
def render_indisponibility_db(table_name, title):
    # Add new Grid Limitation
    st.subheader(f"{title} - Add Grid Limitation")
    grid_start_date = st.date_input(f"Grid Limitation Start Date ({title})", value=date.today())
    grid_end_date = st.date_input(f"Grid Limitation End Date ({title})", value=date.today())
    grid_limitation_percentage = st.number_input(f"Grid Limitation Percentage ({title})", min_value=0.0, max_value=100.0, value=50.0)
    grid_interval_from = st.number_input(f"Interval From (Grid) ({title})", min_value=0, max_value=24, value=1)
    grid_interval_to = st.number_input(f"Interval To (Grid)", min_value=0, max_value=24, value=24)

    if st.button(f"Add Grid Limitation ({title})"):
        add_indisponibility_to_postgres(table_name, "Grid Limitation", grid_start_date, grid_end_date, grid_interval_from, grid_interval_to, grid_limitation_percentage)

    # Add new Asset Limitation
    st.subheader(f"{title} - Add Asset Limitation")
    asset_start_date = st.date_input(f"Asset Limitation Start Date ({title})", value=date.today())
    asset_end_date = st.date_input(f"Asset Limitation End Date ({title})", value=date.today())
    asset_limitation_percentage = st.number_input(f"Asset Limitation Percentage ({title})", min_value=0.0, max_value=100.0, value=50.0)
    asset_interval_from = st.number_input(f"Interval From (Asset)", min_value=0, max_value=24, value=1)
    asset_interval_to = st.number_input(f"Interval To (Asset)", min_value=0, max_value=24, value=24)

    if st.button(f"Add Asset Limitation ({title})"):
        add_indisponibility_to_postgres(table_name, "Asset Limitation", asset_start_date, asset_end_date, asset_interval_from, asset_interval_to, asset_limitation_percentage)

    # Loading the indisponibilities for the selected Client
    df = load_data(table_name)
    st.write(f"Loaded Data for {title}")
    st.dataframe(df)

    st.subheader(f"Remove an Entry ({title})")
    entry_id_to_delete = st.selectbox(f"Select Entry ID to Delete ({title})", df['id'].tolist())
    st.write(f"Selected ID to delete: {entry_id_to_delete}")

    # Delete the selected entry
    if st.button(f"Delete Selected Entry ({title})"):
        st.write("DataFrame before deletion:")
        st.write(df)
        
        df = df[df['id'] != entry_id_to_delete]
        st.write("DataFrame after deletion:")
        st.write(df)

        save_data(table_name, df)

        df_reloaded = load_data(table_name)
        st.write("DataFrame after reloading from Postgres:")
        st.write(df_reloaded)

        if entry_id_to_delete not in df_reloaded['id'].values:
            st.success(f"Entry ID {entry_id_to_delete} was successfully removed.")
        else:
            st.error(f"Entry ID {entry_id_to_delete} was NOT removed.")
        
        st.rerun()

    # Check for tomorrow's indisponibilities
    interval_from, interval_to, limitation_percentage = check_tomorrow_indisponibilities(table_name)
    return interval_from, interval_to, limitation_percentage

# Specific functions for each client
def render_indisponibility_db_Solina():
    return render_indisponibility_db("indisponibility_solina", "Solina")

def render_indisponibility_db_Astro():
    return render_indisponibility_db("indisponibility_astro", "Astro")

def render_indisponibility_db_Imperial():
    return render_indisponibility_db("indisponibility_imperial", "Imperial")
