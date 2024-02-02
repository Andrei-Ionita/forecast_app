import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
import xlsxwriter
from datetime import datetime, timedelta
import os
import openpyxl
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import NamedStyle, numbers
# import win32com.client as win32
# import pythoncom
# from pywintypes import com_error
import os, os.path
# import win32com.client
import joblib
import base64
from pathlib import Path

# Defining the functions
def fetch_ghi_data_from_api(lat, lon, date, api_key):
    # Fetch data from the API
    api_url = "https://api.openweathermap.org/energy/1.0/solar/data?lat={}&lon={}&date={}&appid={}".format(lat, lon, date, api_key)
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: Status code {response.status_code}")

def fetch_temps_clouds_data_from_api(lat, lon, api_key, nr_days):
    # Fetch data from the API
    api_url = api_url = "https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={}&lon={}&appid={}&cnt={}&units=metric".format(lat, lon, api_key, nr_days)
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: Status code {response.status_code}")

def ghi_json_to_excel(ghi_data, output_file_path):
    # Load JSON data
    json_data = ghi_data

    # Flattening 'irradiance' data for 'daily' and 'hourly'
    daily_irradiance = pd.DataFrame(json_data['irradiance']['daily'])
    hourly_irradiance = pd.DataFrame(json_data['irradiance']['hourly'])

    # Further flatten nested data in 'irradiance'
    daily_clear_sky = pd.json_normalize(daily_irradiance['clear_sky']).add_prefix('clear_sky_')
    daily_cloudy_sky = pd.json_normalize(daily_irradiance['cloudy_sky']).add_prefix('cloudy_sky_')
    flattened_daily_irradiance = pd.concat([daily_clear_sky, daily_cloudy_sky], axis=1)

    hourly_irradiance['clear_sky'] = hourly_irradiance['clear_sky'].apply(lambda x: {} if pd.isna(x) else x)
    hourly_irradiance['cloudy_sky'] = hourly_irradiance['cloudy_sky'].apply(lambda x: {} if pd.isna(x) else x)
    hourly_clear_sky = pd.json_normalize(hourly_irradiance['clear_sky']).add_prefix('clear_sky_')
    hourly_cloudy_sky = pd.json_normalize(hourly_irradiance['cloudy_sky']).add_prefix('cloudy_sky_')
    flattened_hourly_irradiance = pd.concat([hourly_irradiance['hour'], hourly_clear_sky, hourly_cloudy_sky], axis=1)

    # Extracting top-level data, excluding the 'irradiance' key
    top_level_data = {k: json_data[k] for k in json_data if k != 'irradiance'}
    top_level_df = pd.DataFrame([top_level_data])

    # Merging the top-level data with the flattened irradiance data
    merged_daily = pd.concat([top_level_df] * len(flattened_daily_irradiance), ignore_index=True)
    merged_daily = pd.concat([merged_daily, flattened_daily_irradiance], axis=1)
    merged_hourly = pd.concat([top_level_df] * len(flattened_hourly_irradiance), ignore_index=True)
    merged_hourly = pd.concat([merged_hourly, flattened_hourly_irradiance], axis=1)

    # Saving to Excel
    with pd.ExcelWriter(output_file_path) as writer:
        merged_daily.to_excel(writer, sheet_name='Daily', index=False)
        merged_hourly.to_excel(writer, sheet_name='Hourly', index=False)

def save_json_to_file(json_data, folder_path, file_name):
    # Create folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Full path for the json file
    file_path = os.path.join(folder_path, file_name)

    # Write the JSON data to the file
    with open(file_path, 'w') as file:
        json.dump(json_data, file)

    print(f"File saved successfully at {file_path}")

def flatten_json_to_excel(json_file_path, output_file_path):
    # Load JSON data
    with open(json_file_path, 'r') as file:
        raw_json_data = json.load(file)

    # Extract the data under the 'list' key
    list_data = raw_json_data['list']

    # Flattening the 'list' data
    flattened_records = []
    for record in list_data:
        # Flattening top-level fields
        flattened_record = pd.json_normalize(record)
        # Appending the flattened record to the list
        flattened_records.append(flattened_record)

    # Concatenate all flattened records into a DataFrame
    flattened_list_data = pd.concat(flattened_records, ignore_index=True)

    # Saving to Excel
    flattened_list_data.to_excel(output_file_path, index=False)

def concatenate_ghi_data():
    folder_path = './RAAL/Production/Input/'  # Replace with your folder path
    specific_string = 'GHI_'  # Replace with the string you want to check for
    all_files = [f for f in os.listdir(folder_path) if specific_string in f]


    # Lists to hold DataFrames from each sheet
    all_daily_dataframes = []
    all_hourly_dataframes = []

    for filename in all_files:
        file_path = os.path.join(folder_path, filename)
        daily_df = pd.read_excel(file_path, sheet_name='Daily')
        hourly_df = pd.read_excel(file_path, sheet_name='Hourly')

        all_daily_dataframes.append(daily_df)
        all_hourly_dataframes.append(hourly_df)

    # Concatenate DataFrames from each sheet
    concatenated_daily_df = pd.concat(all_daily_dataframes, ignore_index=True)
    concatenated_hourly_df = pd.concat(all_hourly_dataframes, ignore_index=True)

    # Optionally, save the concatenated DataFrames to new Excel files
    # concatenated_daily_df.to_excel('Concatenated_Daily_GHI.xlsx', index=False)
    concatenated_hourly_df.to_excel('./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx', index=False)

    print("All files concatenated into Concatenated_Daily_GHI.xlsx and Concatenated_Hourly_GHI.xlsx")


#=======================================================================Preprocessing GHI data======================================================================================

# Setup for GHI
lat = 46.073272
lon = 24.724419

api_key = "f62968d774964bad9bee981406d43d8e"
date = datetime.now().strftime('%Y-%m-%d')

# Fetching the data
ghi_data = fetch_ghi_data_from_api(lat, lon, date, api_key)

# Preprocessing the data
output_file_path = './RAAL/Weather_data/GHI_{}.xlsx'.format(date)  # Replace with your desired output file path
ghi_json_to_excel(ghi_data, output_file_path)

# Formatting the date column (Column "C")
def process_and_save_excel(file_path):
    # Load dataframe
    df = pd.read_excel(file_path, engine='openpyxl')
    # Convert 'date' column to datetime type
    df['date'] = pd.to_datetime(df['date'])
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter') 
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='Sheet1', index=False)    
    # Get workbook
    workbook  = writer.book
    # Add a format for the date using xlsxwriter
    date_format = workbook.add_format({'num_format': 'dd.mm.yyyy'})
    # Get the worksheet
    worksheet = writer.sheets['Sheet1']
    # Set date format
    worksheet.set_column('C:C', None, date_format)
    # Close the Pandas Excel writer and output the Excel file
    workbook.close()

# Defining the lookup column in the GHI file
def add_lookup_column_GHI():
    # Load the workbook and sheet
    workbook = load_workbook("./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx")
    sheet = workbook.active

    # Determine the last column with data
    last_col = sheet.max_column
    
    # Create a new column header 'Lookup' in the next column
    lookup_col_letter = get_column_letter(last_col + 1)
    sheet[f"{lookup_col_letter}1"] = 'Lookup'
    
    # Determine the last row with data in column C
    last_row = max((c.row for c in sheet['C'] if c.value is not None))

    # Starting from the second row, insert the formula
    for row in range(2, last_row + 1):
        sheet[f"{lookup_col_letter}{row}"] = f"=C{row}&G{row}"

    # Save the workbook
    workbook.save("./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx")

#=======================================================================Preprocessing temps_clouds data======================================================================================

# Setup for temps_clouds
api_key = "f62968d774964bad9bee981406d43d8e"
date = datetime.now().strftime('%Y-%m-%d')

# Fetching the data
# temps_clouds_data = fetch_temps_clouds_data_from_api(lat,lon,api_key,nr_days)

# Preprocessing the data
# json_file_path = temps_clouds_data  # Replace with your JSON file path
# output_file_path = './RAAL/Weather_data/temps_clouds_{}.xlsx'.format(date)  # Replace with your desired output file path

# First, we need to do some preprocessing of the weather and GHI file
def creating_weather_date_hour_columns():
    # Load the data
    weather_df = pd.read_excel('./RAAL/Production/Input/weather.xlsx')

    # Ensure the column 'E' is in datetime format
    weather_df['dt_txt'] = pd.to_datetime(weather_df['dt_txt'])

    # Insert new columns for Date and Hour
    weather_df.insert(loc=weather_df.columns.get_loc('dt_txt') + 1, column='Data', value=weather_df['dt_txt'].dt.date)
    weather_df.insert(loc=weather_df.columns.get_loc('Data') + 1, column='Interval', value=weather_df['dt_txt'].dt.hour)

    # Save the modified DataFrame back to Excel
    weather_df.to_excel('./RAAL/Production/Input/weather.xlsx', index=False)

def change_date_format_weather_wb():
    # Check if the named style already exists
    weather_wb = openpyxl.open('./RAAL/Production/Input/weather.xlsx')
    style_name = 'date_style'
    if style_name not in weather_wb.named_styles:
        # Create a new NamedStyle and add it to the workbook
        date_style = NamedStyle(name=style_name, number_format='DD.MM.YYYY')
        weather_wb.add_named_style(date_style)
    else:
        # If the style already exists, there's no need to add it again
        print(f"Style '{style_name}' already exists in the workbook.")
    # Now you can safely assign the style to cells without causing an error
    for row in range(1, weather_wb.active.max_row + 1):
        weather_wb.active.cell(row=row, column=6).style = date_style
    weather_wb.save('./RAAL/Production/Input/weather.xlsx')

# Defining the lookup column in the weather file
def add_lookup_column_weather():
    # Load the workbook and sheet
    workbook = load_workbook('./RAAL/Production/Input/weather.xlsx')
    sheet = workbook.active

    # Determine the last column with data
    last_col = sheet.max_column
    
    # Create a new column header 'Lookup' in the next column
    lookup_col_letter = get_column_letter(last_col + 1)
    sheet[f"{lookup_col_letter}1"] = 'Lookup'
    
    # Determine the last row with data in column F
    last_row = max((c.row for c in sheet['F'] if c.value is not None))

    # Starting from the second row, insert the formula
    for row in range(2, last_row + 1):
        sheet[f"{lookup_col_letter}{row}"] = f"=F{row}&G{row}"

    # Save the workbook
    workbook.save('./RAAL/Production/Input/weather.xlsx')

#=======================================================================Creating Input file======================================================================================

# Creating the Input file
# workbook = xlsxwriter.Workbook("./RAAL/Production/Input.xlsx")
# worksheet = workbook.add_worksheet("forecast_dataset")
# date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
# row = 1
# col = 0
# worksheet.write(0,0,"Data")
# worksheet.write(0,1,"Interval")
# worksheet.write(0,2,"Radiatie")
# worksheet.write(0,3,"Temperatura")
# worksheet.write(0,4,"Nori")

# # for value in preds:
# #     worksheet.write(row, col + 2, value)
# #     row +=1
# # row = 1
# # for Data, Interval in zip(dataset.Data, dataset.Interval):
# #     worksheet.write(row, col + 0, Data, date_format)
# #     worksheet.write(row, col + 1, Interval)
# #     row +=1

# workbook.close()

# def run_vba_macro():
#     if os.path.exists(file_path):
#             pythoncom.CoInitialize()
#             xl=win32com.client.Dispatch("Excel.Application")
#             xl.Workbooks.Open(os.path.abspath(file_path), ReadOnly=1)
#             print("Workbook Opened")
#             try:
#                 xl.Application.Run("Data_Eng.Building_Input_file")
#             except com_error as e:
#                 print(f"COM error encountered: {e}")
#                 # Handle or log the error as needed. Consider continuing if it's a known non-critical error.
#             print("Macro finished!")
#             # xl.Application.Save() # if you want to save then uncomment this line and change delete the ", ReadOnly=1" part from the open function.
#             # xl.Application.Quit() # Comment this out if your excel script closes
#             del xl
#             pythoncom.CoUninitialize()

# Example usage
file_path = "./RAAL/Production/Input.xlsm"  # Update this path to your actual file path

def building_input_file():
    # Define file paths
    # base_path = Path("./RAAL/Production").parent  # Adjust this path as necessary
    ghi_file_path = "./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx"
    weather_file_path = "./RAAL/Production/Input/weather.xlsx"
    
    # Load workbooks and sheets
    ghi_wb = openpyxl.load_workbook(ghi_file_path, data_only=True)
    weather_wb = openpyxl.load_workbook(weather_file_path, data_only=True)
    from pathlib import Path
    # Example for loading an existing workbook
    workbook_path = Path("./RAAL/Production/Input.xlsx")  # Ensure this path is correct
    if workbook_path.exists():
        main_wb = openpyxl.load_workbook(workbook_path)
        ws = main_wb.active  # or specify the sheet name directly if needed

        # Check if the named style already exists
        style_name = 'date_style'
        if style_name not in main_wb.named_styles:
            # Create a new NamedStyle and add it to the workbook
            date_style = NamedStyle(name=style_name, number_format='DD.MM.YYYY')
            main_wb.add_named_style(date_style)
        else:
            # If the style already exists, there's no need to add it again
            print(f"Style '{style_name}' already exists in the workbook.")
    else:
        print(f"Workbook not found at {workbook_path}")
    # Copying weather data
    weather_ws = weather_wb.active  # Adjust the sheet if necessary
    weather_data = pd.read_excel(weather_file_path, sheet_name=weather_ws.title)
    dates_intervals = weather_data[['Data', 'Interval']]  # Adjust column names as necessary
    for index, row in dates_intervals.iterrows():
        # Make sure ws is defined
        if ws is not None:
            # Assuming 'Data' is the correct column name; adjust as needed
            for index, row in dates_intervals.iterrows():
                if 'Data' in row:  # Check if 'Data' column exists in row
                    ws.cell(row=index + 2, column=1, value=row['Data'])
                    ws.cell(row=index + 2, column=2, value=row['Interval'])
                else:
                    print(f"Column 'Data' not found in row {index + 2}")
        else:
            print("Worksheet not initialized.")
    # Assuming you have specific logic to match and insert formulas, here's a simplified example
    # For GHI data
    # last_row = ws.max_row
    # for row in range(2, last_row + 1):
    #     # Constructing the INDEX MATCH formula as a string
    #     # Adjust the formula according to your specific Excel file names, sheet names, and column references
    #     index_match_formula = (
    #         f'=INDEX([Concatenated_Hourly_GHI.xlsx]Sheet1!$K:$K, '
    #         f'MATCH(A{row}&B{row}, [Concatenated_Hourly_GHI.xlsx]Sheet1!$N:$N, 0))'
    #     )

    #     # Setting the formula for a specific cell, e.g., in the 'Radiatie' column (assuming column C)
    #     ws.cell(row=row, column=3).value = index_match_formula
    # Load your main data and the data to be matched against
    # main_df = pd.read_excel(workbook_path)
    # st.write(main_df)
    # lookup_df = pd.read_excel(ghi_file_path)
    # # st.write(lookup_df)
    # # # Create a new column in both dataframes that concatenates the values of columns A and B

    # # Create the 'MatchKey' column by concatenating the formatted 'Data' and 'Interval'
    # Adjust 'ColumnA' and 'ColumnB' to match your actual column names
    # main_df['MatchKey'] = main_df["Lookup"]
    # lookup_df['MatchKey'] = lookup_df["Lookup"].astype(str)
    # st.write(lookup_df)
    # # Now, perform the match based on this new 'MatchKey' column and retrieve the desired value from the lookup dataframe
    # # Adjust 'ValueColumn' to the actual name of the column you want to retrieve after matching
    # main_df['Radiatie'] = main_df['MatchKey'].map(lookup_df.set_index('MatchKey')['cloudy_sky_ghi'])

    # # Similar steps for temperature and clouds from weather data, adjust the formula and columns as necessary
    
    # # Save and close workbooks
    main_wb.save("./RAAL/Production/Input.xlsx")  # Adjust the path as necessary
    # No need to explicitly close in Python, as workbooks are closed when the program ends or when they're no longer referenced

# Adding the Lookup column to the Input file
def add_lookup_column_Input():

    # # Let's create the Lookup column in the main workbook
    # last_row = ws.max_row
    # ws.cell(1,6).value = "Lookup"
    # for row in range(2, last_row + 1):
    #     # Concatenate the values of columns A and B for each row
    #     ws.cell(row=row, column=6).value = f'=A{row}&B{row}'
    # Load the workbook and sheet
    workbook = load_workbook('./RAAL/Production/Input.xlsx')
    sheet = workbook.active

    # Determine the last column with data
    last_col = 5
    
    # Create a new column header 'Lookup' in the next column
    lookup_col_letter = get_column_letter(last_col + 1)
    sheet[f"{lookup_col_letter}1"] = 'Lookup'
    
    # Determine the last row with data in column F
    last_row = max((c.row for c in sheet['A'] if c.value is not None))

    # Starting from the second row, insert the formula
    for row in range(2, last_row + 1):
        sheet[f"{lookup_col_letter}{row}"] = f"=A{row}&B{row}"

    # Save the workbook
    workbook.save('./RAAL/Production/Input.xlsx')

# Lookuping the GHI values
def lookup_ghi_values():
    main_df = pd.read_excel("./RAAL/Production/Input.xlsx")
    main_df["Lookup"] = main_df["Lookup"].astype(str)
    lookup_df = pd.read_excel("./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx")
    lookup_df["Lookup"] = lookup_df["Lookup"].astype(str)
    # Create a dictionary from lookup_df for efficient lookup
    lookup_dict = lookup_df.set_index("Lookup")["cloudy_sky_ghi"].to_dict()
    # Perform the lookup by mapping the 'Lookup' column in main_df to the values in lookup_dict
    main_df['Radiatie'] = main_df['Lookup'].map(lookup_dict)
    # Check the result
    # print(main_df[['Lookup', 'Radiatie']])
    # Save the updated DataFrame to an Excel file
    main_df.to_excel('./RAAL/Production/Input.xlsx', index=False)

# Lookuping the temperatures and clouds
def lookup_weather_values():
    main_df = pd.read_excel("./RAAL/Production/Input.xlsx")
    main_df["Lookup"] = main_df["Lookup"].astype(str)
    lookup_df = pd.read_excel("./RAAL/Production/Input/weather.xlsx")
    lookup_df["Lookup"] = lookup_df["Lookup"].astype(str)
    # Temperatures values
    # Create a dictionary from lookup_df for efficient lookup
    lookup_dict = lookup_df.set_index("Lookup")["main.temp"].to_dict()
    # Perform the lookup by mapping the 'Lookup' column in main_df to the values in lookup_dict
    main_df['Temperatura'] = main_df['Lookup'].map(lookup_dict)
    # Check the result
    # print(main_df[['Lookup', 'Radiatie']])
    # Save the updated DataFrame to an Excel file
    # Clouds values
    # Create a dictionary from lookup_df for efficient lookup
    lookup_dict = lookup_df.set_index("Lookup")["clouds.all"].to_dict()
    # Perform the lookup by mapping the 'Lookup' column in main_df to the values in lookup_dict
    main_df['Nori'] = main_df['Lookup'].map(lookup_dict)
    main_df.to_excel('./RAAL/Production/Input.xlsx', index=False)
#===============================================================================Forcasting RAAL Production=================================================================

def predicting_exporting_RAAL(dataset):
    xgb_loaded = joblib.load("./RAAL/Production/rs_xgb_RAAL_prod.pkl")
    dataset_forecast = dataset.copy()
    dataset_forecast = dataset_forecast[["Data", "Interval", "Radiatie", "Temperatura", "Nori"]]
    dataset_forecast["Month"] = dataset_forecast.Data.dt.month

    dataset_forecast = dataset_forecast.drop("Data", axis=1)
    st.write(dataset_forecast)
    preds = xgb_loaded.predict(dataset_forecast.values)
    #Exporting Results to Excel
    workbook = xlsxwriter.Workbook("./RAAL/Production/Results_Production_xgb_RAAL_wm.xlsx")
    worksheet = workbook.add_worksheet("Production_Predictions")
    date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
    row = 1
    col = 0
    worksheet.write(0,0,"Data")
    worksheet.write(0,1,"Interval")
    worksheet.write(0,2,"Prediction")

    for value in preds:
            worksheet.write(row, col + 2, value)
            row +=1
    row = 1
    for Data, Interval in zip(dataset.Data, dataset.Interval):
            worksheet.write(row, col + 0, Data, date_format)
            worksheet.write(row, col + 1, Interval)
            row +=1

    workbook.close()

#===============================================================================Rendering the Data Engineering page=================================================================

def render_data_eng_page():
    
    # Web App Title
    st.markdown('''
    # **Forecast RAAL Production**

    ''')

    # Streamlit interface

    # User inputs for start and end dates
    start_date = st.date_input("Start Date", datetime.today().date())
    end_date = st.date_input("End Date", datetime.today().date())

    if st.button("Fetch and Process GHI Data"):
        # Iterate from start_date to end_date, day by day
        current_date = start_date
        while current_date <= end_date:
            print(current_date.strftime('%Y-%m-%d'))
            # Fetching data for the date
            ghi_data = fetch_ghi_data_from_api(lat, lon, current_date.strftime('%Y-%m-%d'), api_key)
            # Processing GHI data
            output_file_path = './RAAL/Production/Input/GHI_{}.xlsx'.format(current_date.strftime('%Y-%m-%d'))  # Replace with your desired output file path
            ghi_json_to_excel(ghi_data, output_file_path)
            # Increment the date by one day
            current_date += timedelta(days=1)
        # Concatenating the GHI data into one file
        concatenate_ghi_data()
        # Formatting the date column
        ghi_file_path = "./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx"
        process_and_save_excel(ghi_file_path)
        # Adding the lookup column
        add_lookup_column_GHI()
    # Fetching and processing the Weather data
    if st.button("Fetch and Process Weather Data"):
        # Fetching the data
        nr_days = ((end_date - start_date).days + 2)*24
        print(nr_days)
        temps_clouds_data = fetch_temps_clouds_data_from_api(lat,lon,api_key,nr_days)
        print(temps_clouds_data)
        # Saving the json file
        json_data = temps_clouds_data  # Replace with your JSON data
        folder_path = "./RAAL/Production/Input/"  # Replace with your folder path
        file_name = "weather.json"  # Replace with your desired file name
        save_json_to_file(json_data, folder_path, file_name)
        # Processing the data
        json_file_path = './RAAL/Production/Input/weather.json'  # Replace with your JSON file path
        output_file_path = './RAAL/Production/Input/weather.xlsx'  # Replace with your desired output file path
        flatten_json_to_excel(json_file_path, output_file_path)
        creating_weather_date_hour_columns()
        change_date_format_weather_wb()
        add_lookup_column_weather()
    # Now wee need to create the Input file
    if st.button("Build Input file"):
        # Running the macro
        # run_vba_macro()
        building_input_file()
        add_lookup_column_Input()
        lookup_ghi_values()
        lookup_weather_values()
    # Forecasting RAAL Production
    # Check if the file exists
    if os.path.exists(file_path):
        # If the file exists, show the button
        if st.button("Run Forecast"):
            df = pd.read_excel("./RAAL/Production/Input.xlsx")
            predicting_exporting_RAAL(df)
            file_path_results = './RAAL/Production/Results_Production_xgb_RAAL_wm.xlsx'
            with open(file_path_results, "rb") as f:
                excel_data = f.read()

            # Create a download link
            b64 = base64.b64encode(excel_data).decode()
            button_html = f"""
                 <a download="Production_Forecast.xlsx" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download>
                 <button kind="secondary" data-testid="baseButton-secondary" class="st-emotion-cache-12tniow ef3psqc12">Download Forecast Results</button>
                 </a> 
                 """
            st.markdown(button_html, unsafe_allow_html=True)
    else:
        # If the file does not exist, display a message
        st.error("Input file does not exist. Please ensure the file is in the correct location before proceeding.")
        