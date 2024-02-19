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

def concatenate_ghi_data(CEF):
    folder_path = './{}/Production/Input/'.format(CEF)  # Replace with your folder path
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
    concatenated_hourly_df.to_excel('./{}/Production/Input/Concatenated_Hourly_GHI.xlsx'.format(CEF), index=False)

    print("All files concatenated into Concatenated_Daily_GHI.xlsx and Concatenated_Hourly_GHI.xlsx")


#=======================================================================Preprocessing GHI data======================================================================================

# Setup for GHI
lat = 47.2229
lon = 24.7244

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


def prepare_lookup_column(file_path, date_col_name='Data', interval_col_name='Interval'):
    # Load the Excel file into a DataFrame
    df = pd.read_excel(file_path)
    
    # Ensure the 'Data' column is in datetime format
    df[date_col_name] = pd.to_datetime(df[date_col_name])
    
    # Create the 'Lookup' column by concatenating the 'Data' and 'Interval' columns
    # Format the 'Data' column as a string in 'dd.mm.yyyy' format for concatenation
    df['Lookup'] = df[date_col_name].dt.strftime('%d.%m.%Y') + df[interval_col_name].astype(str)
    df.to_excel(file_path, index=False)
    return df


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
def creating_weather_date_hour_columns(CEF):
    # Load the data
    weather_df = pd.read_excel('./{}/Production/Input/weather.xlsx'.format(CEF))

    # Ensure the column 'E' is in datetime format
    weather_df['dt_txt'] = pd.to_datetime(weather_df['dt_txt'])

    # Insert new columns for Date and Hour
    weather_df.insert(loc=weather_df.columns.get_loc('dt_txt') + 1, column='Data', value=weather_df['dt_txt'].dt.date)
    weather_df.insert(loc=weather_df.columns.get_loc('Data') + 1, column='Interval', value=weather_df['dt_txt'].dt.hour)

    # Save the modified DataFrame back to Excel
    weather_df.to_excel('./{}/Production/Input/weather.xlsx'.format(CEF), index=False)

def change_date_format_weather_wb(CEF):
    # Check if the named style already exists
    weather_wb = openpyxl.open('./{}/Production/Input/weather.xlsx'.format(CEF))
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
    weather_wb.save('./{}/Production/Input/weather.xlsx'.format(CEF))

# Defining the lookup column in the weather file
def add_lookup_column_weather(CEF):
    # Load the workbook and sheet
    workbook = load_workbook('./{}/Production/Input/weather.xlsx'.format(CEF))
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
    workbook.save('./{}/Production/Input/weather.xlsx'.format(CEF))
    weather_df = pd.read_excel('./{}/Production/Input/weather.xlsx'.format(CEF))
    weather_df["Lookup_python"] = weather_df["Data"].astype(str) + weather_df["Interval"].astype(str)
    weather_df.to_excel('./{}/Production/Input/weather.xlsx'.format(CEF))

def prepare_lookup_column(file_path, date_col_name='Data', interval_col_name='Interval'):
    # Load the Excel file into a DataFrame
    df = pd.read_excel(file_path)

    # Ensure the 'Data' column is in datetime format
    df[date_col_name] = pd.to_datetime(df[date_col_name])
    
    # Create the 'Lookup' column by concatenating the 'Data' and 'Interval' columns
    # Format the 'Data' column as a string in 'dd.mm.yyyy' format for concatenation
    df['Lookup'] = df[date_col_name].dt.strftime('%d.%m.%Y') + df[interval_col_name].astype(str)
    df.to_excel(file_path, index=False)
    return df
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

def building_input_file(CEF):
    # Define file paths
    # base_path = Path("./RAAL/Production").parent  # Adjust this path as necessary
    ghi_file_path = "./{}/Production/Input/Concatenated_Hourly_GHI.xlsx".format(CEF)
    weather_file_path = "./{}/Production/Input/weather.xlsx".format(CEF)
    
    # Load workbooks and sheets
    ghi_wb = openpyxl.load_workbook(ghi_file_path, data_only=True)
    weather_wb = openpyxl.load_workbook(weather_file_path, data_only=True)
    from pathlib import Path
    # Example for loading an existing workbook
    workbook_path = Path("./{}/Production/Input.xlsx".format(CEF))  # Ensure this path is correct
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
    main_wb.save("./{}/Production/Input.xlsx".format(CEF))  # Adjust the path as necessary
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
    # last_col = 5
    
    # Create a new column header 'Lookup' in the next column
    # lookup_col_letter = get_column_letter(last_col + 1)
    sheet["E1"] = 'Lookup'
    
    # Determine the last row with data in column F
    last_row = max((c.row for c in sheet['A'] if c.value is not None))

    # Starting from the second row, insert the formula
    for row in range(2, last_row + 1):
        sheet[f"E{row}"] = f"=A{row}&B{row}"

    # Save the workbook
    workbook.save('./RAAL/Production/Input.xlsx')

def add_lookup_column_input_xlsxwriter():
    # Reading the weather file with openpyxl
    weather_df = pd.read_excel("./RAAL/Production/Input/weather.xlsx")
    st.write(weather_df)
    wb = xlsxwriter.Workbook("./RAAL/Production/Input_xlsxwriter.xlsx")
    ws = wb.add_worksheet("forecast_dataset")
    # Adding the columns
    ws.write(0,0,"Data")
    ws.write(0,1,"Interval")
    ws.write(0,2,"Radiatie")
    ws.write(0,3,"Temperatura")
    ws.write(0,4,"Nori")
    ws.write(0,5,"Lookup")
    date_format = wb.add_format({'num_format':'dd.mm.yyyy'})
    # Writing the dates
    for row, data in enumerate(weather_df["Data"], start=1):
        # Convert the string to datetime object
        # This assumes your date format in the DataFrame is consistent and recognized by strptime
        date_obj = datetime.strptime(str(data), "%Y-%m-%d %H:%M:%S")
        ws.write_datetime(row, 0, date_obj, date_format)
    # Writing the dates intervals
    for row, interval in enumerate(weather_df["Interval"], start=1):
        ws.write(row,1,interval)
    # row=1
    # col=0
    # # Creating the Lookup column
    # for data in weather_df["Data"].values:
    #     ws.write_formula(row, col+5, "=A"+ str(row+1) + "&" + "B"+ str(row+1))
    #     row +=1
    row = 1  # Starting row (after headers)
    for index, data in weather_df.iterrows():
        # Write the original data in columns A and B
        ws.write(row, 0, data['Data'], date_format)
        ws.write(row, 1, data['Interval'])

        # Creating the Lookup formula in column F (index 5)
        formula = f'=A{row+1}&B{row+1}'
        ws.write_formula(row, 5, formula)
        
        # Also, write the expected result of the formula as a string in another column (for example, column G)
        # This replicates the formula's action in Python and writes it as a string
        concatenated_result = str(data['Data']) + str(data['Interval'])
        ws.write(row, 6, concatenated_result)
        
        row += 1
    wb.close()

# Lookuping the GHI values
# def lookup_ghi_values():
#     main_df = pd.read_excel("./RAAL/Production/Input.xlsx")
#     st.write(main_df)
#     main_df["Lookup"] = main_df["Lookup"].astype(str)
#     lookup_df = pd.read_excel("./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx")
#     lookup_df["Lookup"] = lookup_df["Lookup"].astype(str)
#     st.write(lookup_df)
#     # Create a dictionary from lookup_df for efficient lookup
#     lookup_dict = lookup_df.set_index("Lookup")["cloudy_sky_ghi"].to_dict()
#     # Perform the lookup by mapping the 'Lookup' column in main_df to the values in lookup_dict
#     main_df['Radiatie'] = main_df['Lookup'].map(lookup_dict)
#     # Check the result
#     print(main_df[['Lookup', 'Radiatie']])
#     # Save the updated DataFrame to an Excel file
#     main_df.to_excel('./RAAL/Production/Input.xlsx', index=False)

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

def lookup_ghi_values(CEF, input_df, ghi_df):
    # Create a dictionary from the GHI DataFrame for efficient lookup
    ghi_dict = ghi_df.set_index('Lookup')['cloudy_sky_ghi'].to_dict()
    
    # Map the 'Lookup' values from the input DataFrame to get the 'cloudy_sky_ghi' values
    input_df['Radiatie'] = input_df['Lookup'].map(ghi_dict)
    input_df.to_excel("./{}/Production/Input.xlsx".format(CEF), index=False)
    return input_df

def lookup_weather_values(CEF, input_df, weather_df):
    # Create a dictionary from the main.temp DataFrame for efficient lookup
    weather_dict = weather_df.set_index('Lookup')['main.temp'].to_dict()
    
    # Map the 'Lookup' values from the input DataFrame to get the 'temperatures' values
    input_df['Temperatura'] = input_df['Lookup'].map(weather_dict)
    # Create a dictionary from the main.temp DataFrame for efficient lookup
    weather_dict = weather_df.set_index('Lookup')['clouds.all'].to_dict()
    
    # Map the 'Lookup' values from the input DataFrame to get the 'temperatures' values
    input_df['Nori'] = input_df['Lookup'].map(weather_dict)
    input_df.to_excel("./{}/Production/Input.xlsx".format(CEF), index=False)
    return input_df
#===============================================================================Forcasting RAAL Production=================================================================

def predicting_exporting_RAAL(dataset):
    xgb_loaded = joblib.load("./RAAL/Production/rs_xgb_RAAL_prod.pkl")
    dataset.dropna(inplace=True)
    dataset_forecast = dataset.copy()
    dataset_forecast = dataset_forecast[["Data", "Interval", "Radiatie", "Temperatura"]]
    dataset_forecast["Month"] = dataset_forecast.Data.dt.month
    dataset_forecast.dropna(inplace=True)
    dataset_forecast = dataset_forecast.drop("Data", axis=1)
    st.write(dataset_forecast)
    preds = xgb_loaded.predict(dataset_forecast.values)
    #Exporting Results to Excel
    workbook = xlsxwriter.Workbook("./RAAL/Production/Results_Production_xgb_RAAL_wm.xlsx")
    worksheet = workbook.add_worksheet("Production_Predictions")
    date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
    # Define a format for cells with three decimal places
    decimal_format = workbook.add_format({'num_format': '0.000'})
    row = 1
    col = 0
    worksheet.write(0,0,"Data")
    worksheet.write(0,1,"Interval")
    worksheet.write(0,2,"Prediction")
    # Rounded values
    rounded_preds = [round(val, 3) for val in preds]
    for value in rounded_preds:
            # Convert the rounded value to a string
            worksheet.write(row, col + 2, value, decimal_format)
            row +=1
    row = 1
    for Data, Interval in zip(dataset.Data, dataset.Interval):
            worksheet.write(row, col + 0, Data, date_format)
            worksheet.write(row, col + 1, Interval)
            row +=1

    workbook.close()

#===============================================================================Forcasting Solina Production=================================================================

def predicting_exporting_Solina(dataset):
    xgb_loaded = joblib.load("./Solina/Production/rs_xgb_Solina_prod_WM.pkl")
    dataset_forecast = dataset.copy()
    dataset.dropna(inplace=True)
    dataset_forecast = dataset_forecast[["Data", "Interval", "Radiatie", "Temperatura"]]
    dataset_forecast["Month"] = dataset_forecast.Data.dt.month

    dataset_forecast = dataset_forecast.drop("Data", axis=1)

    preds = xgb_loaded.predict(dataset_forecast.values)
    #Exporting Results to Excel
    workbook = xlsxwriter.Workbook('./Solina/Production/Results_Production_xgb_Solina_wm.xlsx')
    worksheet = workbook.add_worksheet("Production_Predictions")
    date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
    # Define a format for cells with three decimal places
    # decimal_format = workbook.add_format({'num_format': '0.000'})
    row = 1
    col = 0
    worksheet.write(0,0,"Data")
    worksheet.write(0,1,"Interval")
    worksheet.write(0,2,"Prediction")
    # Rounded values
    rounded_preds = [round(val, 3) for val in preds]
    for value in rounded_preds:
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
    # **Forecast Production**

    ''')

    # Streamlit interface
    location = st.radio(
    "Select location",
    ["Alba Iulia", "Prundu Bargaului"],
    captions = ["***Solina***", "***RAAL***"])

    if location == "Prundu Bargaului":
        lat = 47.2229
        lon = 24.7244
    else:
        lat = 46.073272
        lon = 23.580489
    # User inputs for start and end dates
    start_date = st.date_input("Start Date", datetime.today().date())
    end_date = st.date_input("End Date", datetime.today().date())
        
    if st.button("Run Forecast"):
        current_date = start_date
        # FORECASTING RAAL PRODUCTION
        # Check if the file exists
        if location == "Prundu Bargaului":
            CEF = "RAAL"
            # 1. Building the Input file
            # Iterate from start_date to end_date, day by day
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
            concatenate_ghi_data(CEF)
            # Formatting the date column
            ghi_file_path = "./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx"
            process_and_save_excel(ghi_file_path)
            # Adding the lookup column
            # add_lookup_column_GHI()
            file_path = "./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx"
            date_col_name = "date"
            interval_col_name = "hour"
            ghi_df = prepare_lookup_column(file_path, date_col_name, interval_col_name)

            # Fetching the weather data
            nr_days = ((end_date - start_date).days + 2)*24
            print(nr_days)
            temps_clouds_data = fetch_temps_clouds_data_from_api(lat,lon,api_key,nr_days)
            print(temps_clouds_data)
            # Saving the json file
            json_data = temps_clouds_data  # Replace with your JSON data
            folder_path = "./RAAL/Production/Input/"  # Replace with your folder path
            file_name = "weather.json"  # Replace with your desired file name
            save_json_to_file(json_data, folder_path, file_name)
            # Processing the weather data
            json_file_path = './RAAL/Production/Input/weather.json'  # Replace with your JSON file path
            output_file_path = './RAAL/Production/Input/weather.xlsx'  # Replace with your desired output file path
            flatten_json_to_excel(json_file_path, output_file_path)
            creating_weather_date_hour_columns(CEF)
            # change_date_format_weather_wb()
            # add_lookup_column_weather()
            file_path = "./RAAL/Production/Input/weather.xlsx"
            date_col_name = "Data"
            interval_col_name = "Interval"
            weather_df = prepare_lookup_column(file_path, date_col_name, interval_col_name)

            # Vuilding the Input file
            building_input_file(CEF)
            # add_lookup_column_Input()
            # add_lookup_column_input_xlsxwriter()
            file_path = "./RAAL/Production/Input.xlsx"
            date_col_name = "Data"
            interval_col_name = "Interval"
            input_df = prepare_lookup_column(file_path, date_col_name, interval_col_name)
            # lookup_ghi_values()
            # lookup_weather_values()
            # Lookuping the GHI values
            input_df = pd.read_excel("./RAAL/Production/Input.xlsx")
            ghi_df = pd.read_excel("./RAAL/Production/Input/Concatenated_Hourly_GHI.xlsx")
            lookup_ghi_values(CEF, input_df, ghi_df)
            # Lookupinh the temperatures and clouds values
            weather_df = pd.read_excel("./RAAL/Production/Input/weather.xlsx")
            lookup_weather_values(CEF, input_df, weather_df)
            # Predicting the Production
            if os.path.exists("./RAAL/Production/Input.xlsx"):
                # If the file exists, show the button
                df = pd.read_excel("./RAAL/Production/Input.xlsx")
                predicting_exporting_RAAL(df)
                file_path_results = './RAAL/Production/Results_Production_xgb_RAAL_wm.xlsx'
                with open(file_path_results, "rb") as f:
                    excel_data = f.read()

                # Create a download link
                b64 = base64.b64encode(excel_data).decode()
                button_html = f"""
                     <a download="Production_Forecast_RAAL_WM_{current_date}.xlsx" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download>
                     <button kind="secondary" data-testid="baseButton-secondary" class="st-emotion-cache-12tniow ef3psqc12">Download Forecast Results</button>
                     </a> 
                     """
                st.markdown(button_html, unsafe_allow_html=True)
            else:
                # If the file does not exist, display a message
                st.error("Input file does not exist. Please ensure the file is in the correct location before proceeding.")
        # Forecasting Solina Production
        elif location == "Alba Iulia":
            CEF = "Solina"
            # Iterate from start_date to end_date, day by day
            current_date = start_date
            while current_date <= end_date:
                print(current_date.strftime('%Y-%m-%d'))
                # Fetching data for the date
                ghi_data = fetch_ghi_data_from_api(lat, lon, current_date.strftime('%Y-%m-%d'), api_key)
                # Processing GHI data
                output_file_path = './Solina/Production/Input/GHI_{}.xlsx'.format(current_date.strftime('%Y-%m-%d'))  # Replace with your desired output file path
                ghi_json_to_excel(ghi_data, output_file_path)
                # Increment the date by one day
                current_date += timedelta(days=1)
            # Concatenating the GHI data into one file
            concatenate_ghi_data(CEF)
            # Formatting the date column
            ghi_file_path = "./Solina/Production/Input/Concatenated_Hourly_GHI.xlsx"
            process_and_save_excel(ghi_file_path)
            # Adding the lookup column
            # add_lookup_column_GHI()
            file_path = "./Solina/Production/Input/Concatenated_Hourly_GHI.xlsx"
            date_col_name = "date"
            interval_col_name = "hour"
            ghi_df = prepare_lookup_column(file_path, date_col_name, interval_col_name)

            # Fetching the weather data
            nr_days = ((end_date - start_date).days + 2)*24
            print(nr_days)
            temps_clouds_data = fetch_temps_clouds_data_from_api(lat,lon,api_key,nr_days)
            print(temps_clouds_data)
            # Saving the json file
            json_data = temps_clouds_data  # Replace with your JSON data
            folder_path = "./Solina/Production/Input/"  # Replace with your folder path
            file_name = "weather.json"  # Replace with your desired file name
            save_json_to_file(json_data, folder_path, file_name)
            # Processing the weather data
            json_file_path = './Solina/Production/Input/weather.json'  # Replace with your JSON file path
            output_file_path = './Solina/Production/Input/weather.xlsx'  # Replace with your desired output file path
            flatten_json_to_excel(json_file_path, output_file_path)
            creating_weather_date_hour_columns(CEF)
            # change_date_format_weather_wb()
            # add_lookup_column_weather()
            file_path = "./Solina/Production/Input/weather.xlsx"
            date_col_name = "Data"
            interval_col_name = "Interval"
            weather_df = prepare_lookup_column(file_path, date_col_name, interval_col_name)

            # Building the Input file
            building_input_file(CEF)
            # add_lookup_column_Input()
            # add_lookup_column_input_xlsxwriter()
            file_path = "./Solina/Production/Input.xlsx"
            date_col_name = "Data"
            interval_col_name = "Interval"
            input_df = prepare_lookup_column(file_path, date_col_name, interval_col_name)
            # lookup_ghi_values()
            # lookup_weather_values()
            # Lookuping the GHI values
            input_df = pd.read_excel("./Solina/Production/Input.xlsx")
            ghi_df = pd.read_excel("./Solina/Production/Input/Concatenated_Hourly_GHI.xlsx")
            lookup_ghi_values(CEF, input_df, ghi_df)
            # Lookupinh the temperatures and clouds values
            weather_df = pd.read_excel("./Solina/Production/Input/weather.xlsx")
            lookup_weather_values(CEF, input_df, weather_df)
            if os.path.exists("./Solina/Production/Input.xlsx"):
            # Check if the file exists
                df = pd.read_excel("./Solina/Production/Input.xlsx")
                predicting_exporting_Solina(df)
                file_path_results = './Solina/Production/Results_Production_xgb_Solina_wm.xlsx'
                with open(file_path_results, "rb") as f:
                    excel_data = f.read()

                # Create a download link
                b64 = base64.b64encode(excel_data).decode()
                button_html = f"""
                     <a download="Production_Forecast_Solina_WM_{end_date}.xlsx" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download>
                     <button kind="secondary" data-testid="baseButton-secondary" class="st-emotion-cache-12tniow ef3psqc12">Download Forecast Results</button>
                     </a> 
                     """
                st.markdown(button_html, unsafe_allow_html=True)
            else:
                # If the file does not exist, display a message
                st.error("Input file does not exist. Please ensure the file is in the correct location before proceeding.")
        