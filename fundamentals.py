import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import wapi
from openpyxl import load_workbook
from datetime import datetime
from entsoe import EntsoePandasClient
import xml.etree.ElementTree as ET

# ================================================================================VOLUE data==================================================================================

# Set the date dinamically as today
# Get the current date with time set to 00:00
issue_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Format the date as a string in the desired format
issue_date_str = issue_date.isoformat()
issue_date_str = issue_date.strftime('%Y-%m-%dT%H:%M')

# Fetching the token and store it's expiring timestamp
load_dotenv()
client_id = os.getenv("volue_client_id")
client_secret = os.getenv("volue_client_secret")

# Replace 'client_id' and 'client_secret' with your actual credentials
session = wapi.Session(client_id = client_id, client_secret = client_secret)

def fetch_token(client_id, client_secret):
	"""
	Fetches a new access token using client credentials.

	Args:
		client_id (str): The client ID provided by Volue API.
		client_secret (str): The client secret provided by Volue API.

	Returns:
		dict: A dictionary containing the access token, token type, and expiration timestamp.
	"""
	url = "https://auth.volueinsight.com/oauth2/token"
	auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
	headers = {"Content-Type": "application/x-www-form-urlencoded"}
	data = {"grant_type": "client_credentials"}

	response = requests.post(url, headers=headers, data=data, auth=auth)
	
	if response.status_code == 200:
		token_info = response.json()
		# Calculate expiration timestamp
		expires_in = token_info.get("expires_in", 3600)  # Default to 3600 seconds
		expiration_timestamp = datetime.now() + timedelta(seconds=expires_in)
		
		return {
			"access_token": token_info["access_token"],
			"token_type": token_info["token_type"],
			"expires_at": expiration_timestamp
		}
	else:
		raise Exception("Failed to fetch token: " + response.text)

# Example usage:
# token_info = fetch_token(client_id, client_secret)
# print(token_info)

def is_token_valid(token_info):
	"""
	Checks if the current access token is valid or needs to be refreshed.

	Args:
		token_info (dict): The dictionary containing the token information.

	Returns:
		bool: True if the token is valid, False otherwise.
	"""
	if token_info is None:
		return False
	
	# Consider token as expired if it's close to expiration time (e.g., 5 minutes buffer)
	print(token_info["expires_at"], datetime.now() + timedelta(minutes=5))
	return datetime.now() + timedelta(minutes=5) < token_info["expires_at"]

# Usage example
# if not is_token_valid(token_info):
# 	token_info = fetch_token(client_id, client_secret)
# 	# Update your storage with the new token_info


# Fetching the curves==================================
# Wind curve horizon = days

def fetch_curve(token, curve_name):
	"""
	Fetches curve data by name using the provided access token.

	Args:
		token (str): The access token for authorization.
		curve_name (str): The name of the curve to fetch.

	Returns:
		dict: A dictionary containing the curve data, or an error message.
	"""
	url = "https://api.volueinsight.com/api/instances/"
	headers = {
		"Authorization": f"Bearer {token}",
		"Content-Type": "application/json"
	}
	params = {
		"name": curve_name  # Filter by curve name
	}
	
	response = requests.get(url, headers=headers, params=params)
	
	if response.status_code == 200:
		return response.json()  # Returns the curve data
	else:
		return {"error": "Failed to fetch curve data", "status_code": response.status_code, "message": response.text}

# Usage example (Assuming `token_info` is a dictionary containing your valid access token)
# curve_name = "pro ro wnd ec00 mwh/h cet min15 f"
# curve_data = fetch_curve(token_info['access_token'], curve_name)
# print(curve_data)


def fetch_time_series_data(token, curve_id, start_date, end_date, time_zone=None, output_time_zone=None, filter=None, function=None, frequency=None):
	"""
	Fetches time series data for a specified curve.

	Args:
		token (str): The access token for authorization.
		curve_id (int): The ID of the curve to fetch data for.
		start_date (str): The start date for the data range in YYYY-MM-DD format.
		end_date (str): The end date for the data range in YYYY-MM-DD format.
		time_zone (str): Optional. The curve time zone before filtering and frequency change.
		output_time_zone (str): Optional. The curve time zone after filtering and frequency change.
		filter (str): Optional. Filter out parts of the time series.
		function (str): Optional. The aggregation/split function to use when changing frequency.
		frequency (str): Optional. The required frequency of the output.

	Returns:
		dict: A dictionary containing the time series data for the curve, or an error message.
	"""
	url = f"https://api.volueinsight.com/api/series/{curve_id}"
	headers = {
		"Authorization": f"Bearer {token}",
		"Content-Type": "application/json"
	}
	params = {
		"from": start_date,
		"to": end_date,
	}
	
	# Optional parameters
	if time_zone:
		params['time_zone'] = time_zone
	if output_time_zone:
		params['output_time_zone'] = output_time_zone
	if filter:
		params['filter'] = filter
	if function:
		params['function'] = function
	if frequency:
		params['frequency'] = frequency

	response = requests.get(url, headers=headers, params=params)

	if response.status_code == 200:
		return response.json()  # Returns the time series data for the curve
	else:
		return {"error": "Failed to fetch time series data", "status_code": response.status_code, "message": response.text}

#=================================Fetching the Wind Energy data============================================
def fetch_volue_wind_data():
	# INSTANCES curve 15 min
	curve = session.get_curve(name='pro ro wnd ec00 mwh/h cet min15 f')
	# INSTANCES curves contain a timeseries for each defined issue dates
	# Get a list of available curves with issue dates within a timerange with:
	# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
	ts_15min = curve.get_instance(issue_date=issue_date_str)
	df_wind_15min = ts_15min.to_pandas() # convert TS object to pandas.Series object
	df_wind_15min = df_wind_15min.to_frame() # convert pandas.Series to pandas.DataFrame
	st.dataframe(df_wind_15min)
	df_wind_15min.to_csv("./Market Fundamentals/Wind_data_15min.csv")
	## INSTANCES curve hour
	curve = session.get_curve(name='pro ro wnd fwd mw cet h f')
	# INSTANCES curves contain a timeseries for each defined issue dates
	# Get a list of available curves with issue dates within a timerange with:
	# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
	ts_h = curve.get_instance(issue_date=issue_date_str)
	pd_s_h = ts_h.to_pandas() # convert TS object to pandas.Series object
	pd_df_h = pd_s_h.to_frame() # convert pandas.Series to pandas.DataFrame
	st.dataframe(pd_df_h)
	pd_df_h.to_csv("./Market Fundamentals/Wind_data_hourly.csv")

	# Writing the hourly values to the Trading Tool file
	# Load the wind data from CSV without altering the date format
	wind_data_path = './Market Fundamentals/Wind_data_hourly.csv'  # Update with the actual path
	wind_data = pd.read_csv(wind_data_path)

	# Determine tomorrow's date as a string to match your CSV format
	tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

	# Filter rows based on the string representation of tomorrow's date
	# Assuming the date in your CSV is in the format 'YYYY-MM-DD' and is in the first column
	tomorrow_data = wind_data[wind_data.iloc[:, 0].str.startswith(tomorrow)]
	st.dataframe(tomorrow_data)
	# Write to Excel
	excel_file_path = './Market Fundamentals/Volue_data.xlsx'  # Update with the actual path
	workbook = load_workbook(excel_file_path)
	sheet = workbook["Volue_Data_eng"] 

	# Confirm we have data to write
	if len(tomorrow_data) > 0:
		excel_row = 4
		for index, row in tomorrow_data.iterrows():
			if excel_row == 12 or excel_row == 25:
				excel_row += 1
			cell = f'E{excel_row}'
			sheet[cell] = row[1]  # Assuming data to write is in the second column
			print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
			excel_row += 1
		workbook.save(filename=excel_file_path)
		print("Excel file has been updated.")
	else:
		print("No data available for tomorrow to write into the Excel file.")

	# Writing the quarterly wind data to the Volue data Excel file
	wind_data_path = './Market Fundamentals/Wind_data_15min.csv'  # Update with the actual path
	wind_data = pd.read_csv(wind_data_path)
	# Write to Excel
	excel_file_path = './Market Fundamentals/Volue_data.xlsx'  # Update with the actual path
	workbook = load_workbook(excel_file_path)
	sheet = workbook["Volue_Data_eng"] 
	excel_row = 4
	for index, row in wind_data.iterrows():
		cell = f'AQ{excel_row}'
		sheet[cell] = row[0]  # Assuming data to write is in the second column
		cell = f'AR{excel_row}'
		sheet[cell] = row[1]  # Assuming data to write is in the second column
		print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
		excel_row += 1
	workbook.save(filename=excel_file_path)
	print("Excel file has been updated.")

	return df_wind_15min
#=====================================================================================Input Data=======================================================================================

# Updating the date on the Pret_PZU sheet
# Step 2: Create a new workbook (or you can open an existing one)
def updating_PZU_date():
	wb = load_workbook('./Market Fundamentals/Volue_data.xlsx')

	# Step 3: Select the active worksheet
	ws = wb["Pret_PZU"]

	# Step 4: Calculate the next day's date
	next_day = datetime.now() + timedelta(days=1)

	# Step 5: Write dates in the format "dd.mm.yyyy" from A2 to A25
	for row in range(2, 26):  # Note: range(2, 26) will loop from 2 to 25
		# Format the date as "dd.mm.yyyy"
		formatted_date = next_day.strftime("%d.%m.%Y")
		ws[f'A{row}'] = formatted_date

	# Step 6: Save the workbook
	wb.save("./Market Fundamentals/Volue_data.xlsx")

# Fetching the Consumption and Production from Transelectrica===================================================
# 1. Consumption
def process_file_consumption_transelectrica(file_path):
	# Read the file, skipping initial rows to get to the actual data
	data_cleaned = pd.read_excel(file_path, skiprows=4)
	
	# Drop the unnecessary first two columns (index and "Update day")
	data_cleaned.drop(columns=data_cleaned.columns[:2], inplace=True)
	
	# Rename the first column to 'Date' for clarity
	data_cleaned.rename(columns={data_cleaned.columns[0]: 'Date'}, inplace=True)
	
	# Determine the number of intervals (subtracting the Date column)
	num_intervals = len(data_cleaned.columns) - 1
	
	# Generate interval identifiers
	interval_identifiers = list(range(1, num_intervals + 1))
	
	# Melt the dataframe with generated interval identifiers
	data_long = pd.melt(data_cleaned, id_vars=["Date"], value_vars=data_cleaned.columns[1:], var_name="Interval", value_name="Value")
	
	# Replace the interval column with the generated interval identifiers
	data_long['Interval'] = data_long.groupby('Date').cumcount() + 1
	
	# Sort values to ensure they are ordered by Date and then by Interval
	data_long_sorted = data_long.sort_values(by=["Date", "Interval"]).reset_index(drop=True)
	
	return data_long_sorted

# 2. Production
def process_file_production_transelectrica(file_path):
	# Read the CSV, skipping initial rows to get to the actual data
	data_cleaned = pd.read_excel(file_path, skiprows=4)
	
	# Drop the unnecessary first two columns (index and "Update day")
	data_cleaned.drop(columns=data_cleaned.columns[:2], inplace=True)
	
	# Rename the first column to 'Date' for clarity
	data_cleaned.rename(columns={data_cleaned.columns[0]: 'Date'}, inplace=True)
	
	# Melt the dataframe to transform it from wide to long format
	data_long = data_cleaned.melt(id_vars=["Date"], var_name="Interval", value_name="Value")
	
	# Extract interval numbers from the Interval column (e.g., "int1" -> 1)
	data_long["Interval"] = data_long["Interval"].str.extract('(\d+)').astype(int)
	
	# Sort values to ensure they are ordered by Date and then by Interval
	data_long_sorted = data_long.sort_values(by=["Date", "Interval"]).reset_index(drop=True)
	
	return data_long_sorted

#====================================================================================ENTSOE data=======================================================================================
api_key_entsoe = os.getenv("api_key_entsoe")
client = EntsoePandasClient(api_key=api_key_entsoe)

# 1 Imbalance Prices
def imbalance_prices(start, end):
	# Define the start and end timestamps for the query
	# start = pd.Timestamp('20240401', tz='Europe/Bucharest')  # Adjust the start date as needed
	# end = pd.Timestamp('20240411', tz='Europe/Bucharest')    # Adjust the end date as needed

	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania

	# Fetch imbalance prices
	imbalance_prices = client.query_imbalance_prices(country_code, start=start, end=end, psr_type=None)

	# Display or analyze the fetched data
	return imbalance_prices

# 2. Imbalabce Volumes
def imbalance_volumes(start, end):
	# Define the start and end timestamps for the query
	# start = pd.Timestamp('20240401', tz='Europe/Bucharest')  # Adjust the start date as needed
	# end = pd.Timestamp('20240411', tz='Europe/Bucharest')    # Adjust the end date as needed

	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania

	# Fetch imbalance prices
	imbalance_volumes = client.query_imbalance_volumes(country_code, start=start, end=end, psr_type=None)

	# Display or analyze the fetched data
	return imbalance_volumes

#3. Contracted Aggragated mFRR Volumes
def activated_mFRR_energy(start, end):
	# Update parameters with Czech control area domain
	params = {
		'documentType': 'A83',
		"controlArea_Domain": "10YRO-TEL------P",
		"businessType": "A97"
	}

	# Make the API request
	response = client._base_request(params=params, start=start, end=end)

	# Process the response
	if response.status_code == 200:
		# Check if the response is empty
		if response.text:
			# Check the content type
			content_type = response.headers.get('Content-Type', '')
			if 'application/json' in content_type:
				try:
					data = response.json()
					# st.write(data)
				except ValueError as e:
					st.error(f"Invalid JSON data received: {e}")
			else:
				st.error(f"Unexpected content type: {content_type}")
				# st.text(f"Response content: {response.text}")
		else:
			st.warning("Empty response received.")
	else:
		st.error(f"Failed to retrieve data: HTTP Status {response.status_code}")

	return response.text

# Defining the function to process the server response
def creating_mFRR_dfs(data):
	# Creating two dataframes, one for Up and another for Down
	# The XML content you provided
	xml_data = data

	# Define the namespace map to use with ElementTree
	namespaces = {
		'ns': 'urn:iec62325.351:tc57wg16:451-6:balancingdocument:3:0'  # 'ns' is a placeholder for the namespace
	}

	# Parse the XML
	root = ET.fromstring(xml_data)

	# Dictionary to hold DataFrames, one for each TimeSeries
	dfs = {}

	# Counter to identify TimeSeries
	time_series_id = 1

	# Navigate through the XML structure and extract data
	for ts in root.findall('.//ns:TimeSeries', namespaces):
		timestamps = []
		positions = []
		quantities = []

		for point in ts.findall('.//ns:Point', namespaces):
			position = int(point.find('ns:position', namespaces).text)
			quantity = point.find('ns:quantity', namespaces).text
			# Assuming the timestamp is the same for all points in a TimeSeries for simplicity
			time_interval = ts.find('.//ns:Period/ns:timeInterval', namespaces)
			start = time_interval.find('ns:start', namespaces).text
			end = time_interval.find('ns:end', namespaces).text
			start_date = pd.to_datetime(start).strftime('%d.%m.%Y')  # Format as "dd.mm.yyyy"
			end_date = pd.to_datetime(end).strftime('%d.%m.%Y')  # Format as "dd.mm.yyyy"
			timestamps.append(end_date)
			positions.append(position)
			quantities.append(quantity)

		# Create a DataFrame for the current TimeSeries
		df = pd.DataFrame({
			'Date': timestamps,
			'Interval': positions,
			'Quantity': quantities
		})
		
		# Rename columns based on TimeSeries number
		if time_series_id == 1:
			df.rename(columns={'Quantity': 'Activated Energy Down'}, inplace=True)
		else:
			df.rename(columns={'Quantity': 'Activated Energy Up'}, inplace=True)
		
		# Store the DataFrame in the dictionary with a unique key
		dfs[f"TimeSeries_{time_series_id}"] = df
		time_series_id += 1

	# Now dfs['TimeSeries_1'] will hold the DataFrame for the first TimeSeries
	# and dfs['TimeSeries_2'] for the second, etc.

	# Example to print DataFrame for TimeSeries 1 and 2
	st.write("DataFrame for TimeSeries 1:")
	st.dataframe(dfs['TimeSeries_1'])
	st.write("\nDataFrame for TimeSeries 2:")
	st.dataframe(dfs['TimeSeries_2'])

	# Merge the dataframes on 'Date' and 'Interval'
	activated_energy_df = pd.merge(dfs['TimeSeries_1'], dfs['TimeSeries_2'], on=['Date', 'Interval'], how='outer')
	return activated_energy_df

# Defining the functions fetch the data for a range of days
def make_api_request(params, start, end):
    # Replace with your actual API request logic
    response = client._base_request(params=params, start=start, end=end)
    return response

def query_daily_mFRR(start_date, end_date):
    current_date = start_date
    final_dfs = []  # List to store each day's DataFrame

    while current_date < end_date:
        # Generate start and end timestamps for the current day
        start = pd.Timestamp(f"{current_date.strftime('%Y%m%d')}0000", tz='Europe/Bucharest')
        end = pd.Timestamp(f"{(current_date + timedelta(days=1)).strftime('%Y%m%d')}0000", tz='Europe/Bucharest')
        
        # Update parameters with the control area domain
        params = {
            'documentType': 'A83',
            "controlArea_Domain": "10YRO-TEL------P",
            "businessType": "A97"
        }
        
        # Make the API request for the current day
        response = make_api_request(params, start, end)

        # Process the API response into a DataFrame
        if response.status_code == 200 and response.text:
            day_df = creating_mFRR_dfs(response.text)  # Assume this function returns a DataFrame
            final_dfs.append(day_df)
        else:
            st.error(f"Failed to retrieve data for {current_date.strftime('%Y-%m-%d')}: HTTP Status {response.status_code}")

        # Move to the next day
        current_date += timedelta(days=1)

    # Concatenate all daily DataFrames into a single DataFrame
    if final_dfs:
        combined_df = pd.concat(final_dfs, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no data was collected

#4. Fethcing the Actual Load 
def actual_load(start, end):
	# Define the start and end timestamps for the query
	# start = pd.Timestamp('20240401', tz='Europe/Bucharest')  # Adjust the start date as needed
	# end = pd.Timestamp('20240411', tz='Europe/Bucharest')    # Adjust the end date as needed

	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania

	# Fetch imbalance prices
	actual_load = client.query_load(country_code, start=start, end=end)

	# Display or analyze the fetched data
	return actual_load

#5. Fetching the Generation Forecast
def generation_forecast(start, end):
	# Define the start and end timestamps for the query
	# start = pd.Timestamp('20240401', tz='Europe/Bucharest')  # Adjust the start date as needed
	# end = pd.Timestamp('20240411', tz='Europe/Bucharest')    # Adjust the end date as needed

	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania

	# Fetch generation forecast
	generation_forecast = client.query_generation_forecast(country_code, start=start, end=end)

	# Display or analyze the fetched data
	return generation_forecast

#6. Fetching the Actual Geneeration per Source
def actual_generation_source(start, end):
	# Define the start and end timestamps for the query
	# start = pd.Timestamp('20240401', tz='Europe/Bucharest')  # Adjust the start date as needed
	# end = pd.Timestamp('20240411', tz='Europe/Bucharest')    # Adjust the end date as needed

	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania

	# Fetch imbalance prices
	actual_generation_source = client.query_generation(country_code, start=start, end=end, psr_type=None, include_eic=False)

	# Display or analyze the fetched data
	return actual_generation_source
#====================================================================================Rendering into App================================================================================

if "df_wind_15min" and "df_solar_15min" not in st.session_state:
	st.session_state["df_wind_15min"] = []
	st.session_state["df_solar_15min"] = []

def render_fundamentals_page():
	
	# Page tittle
	st.header("Market Fundamentals", divider = "rainbow")

	# Get Wind Forecast
	st.subheader("Wind Data", divider = "green")
	
	# if st.button("Get Wind Data"):
	# 	df_wind_15min = fetch_volue_wind_data()

	# Get Solar Forecast
	st.subheader("PV Data", divider = "orange")
	if st.button("Get Solar Data"):
		## INSTANCE curve 15 min
		curve = session.get_curve(name='pro ro spv ec00 mwh/h cet min15 f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_15min = curve.get_instance(issue_date=issue_date_str)
		pd_s_15min = ts_15min.to_pandas() # convert TS object to pandas.Series object
		df_solar_15min = pd_s_15min.to_frame() # convert pandas.Series to pandas.DataFrame
		st.dataframe(df_solar_15min)
		df_solar_15min.to_csv("./Market Fundamentals/PV_data_15min.csv")
		## INSTANCE curve hour
		curve = session.get_curve(name='pro ro spv fwd mw cet h f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_h = curve.get_instance(issue_date=issue_date_str)
		pd_s_h = ts_h.to_pandas() # convert TS object to pandas.Series object
		pd_df_h = pd_s_h.to_frame() # convert pandas.Series to pandas.DataFrame
		st.dataframe(pd_df_h)
		# Writing the hourly values to the Trading Tool file
		pd_df_h.to_csv("./Market Fundamentals/PV_data_hourly.csv")
		# Load the wind data from CSV without altering the date format
		pv_data_path = './Market Fundamentals/PV_data_hourly.csv'  # Update with the actual path
		pv_data = pd.read_csv(pv_data_path)

		# Determine tomorrow's date as a string to match your CSV format
		tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

		# Filter rows based on the string representation of tomorrow's date
		# Assuming the date in your CSV is in the format 'YYYY-MM-DD' and is in the first column
		tomorrow_data = pv_data[pv_data.iloc[:, 0].str.startswith(tomorrow)]
		st.dataframe(tomorrow_data)
		# Write to Excel
		excel_file_path = './Market Fundamentals/Volue_data.xlsx'  # Update with the actual path
		workbook = load_workbook(excel_file_path)
		sheet = workbook["Volue_Data_eng"] 

		# Confirm we have data to write
		if len(tomorrow_data) > 0:
			excel_row = 4
			for index, row in tomorrow_data.iterrows():
				if excel_row == 12 or excel_row == 25:
					excel_row += 1
				cell = f'P{excel_row}'
				sheet[cell] = row[1]  # Assuming data to write is in the second column
				print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
				excel_row += 1
			workbook.save(filename=excel_file_path)
			print("Excel file has been updated.")
		else:
			print("No data available for tomorrow to write into the Excel file.")

		# Writing the quarterly pv data to the Volue data Excel file
		pv_data_path = './Market Fundamentals/PV_data_15min.csv'  # Update with the actual path
		pv_data = pd.read_csv(pv_data_path)
		# Write to Excel
		excel_file_path = './Market Fundamentals/Volue_data.xlsx'  # Update with the actual path
		workbook = load_workbook(excel_file_path)
		sheet = workbook["Volue_Data_eng"] 
		excel_row = 4
		for index, row in pv_data.iterrows():
			cell = f'AY{excel_row}'
			sheet[cell] = row[0]  # Assuming data to write is in the second column
			cell = f'AZ{excel_row}'
			sheet[cell] = row[1]  # Assuming data to write is in the second column
			print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
			excel_row += 1
		workbook.save(filename=excel_file_path)
		print("Excel file has been updated.")

		# Creating the Volue dataframe
		df_wind_15min = fetch_volue_wind_data()
		# 1. Creating the first layer of the big dataframe containing the Wind and Solar Energy
		df_wind_15min.reset_index(inplace=True)
		df_wind_15min.columns = ['Timestamp', "Wind Energy"]

		# Convert 'Timestamp' to datetime format
		df_wind_15min['Timestamp'] = pd.to_datetime(df_wind_15min['Timestamp'])

		# Create 'Date' and 'Interval' columns from 'Timestamp'
		df_wind_15min['Date'] = df_wind_15min['Timestamp'].dt.strftime('%d.%m.%Y')
		df_wind_15min['Interval'] = ((df_wind_15min['Timestamp'].dt.hour * 60 + df_wind_15min['Timestamp'].dt.minute) // 15 + 1)
		df_wind_15min.drop(columns=["Timestamp"], inplace=True)
		st.dataframe(df_wind_15min)

		df_solar_15min.reset_index(inplace=True)
		df_solar_15min.columns = ['Timestamp', "Solar Energy"]

		# Convert 'Timestamp' to datetime format
		df_solar_15min['Timestamp'] = pd.to_datetime(df_solar_15min['Timestamp'])

		# Create 'Date' and 'Interval' columns from 'Timestamp'
		df_solar_15min['Date'] = df_solar_15min['Timestamp'].dt.strftime('%d.%m.%Y')
		df_solar_15min['Interval'] = ((df_solar_15min['Timestamp'].dt.hour * 60 + df_solar_15min['Timestamp'].dt.minute) // 15 + 1)
		df_solar_15min.drop(columns=["Timestamp"], inplace=True)
		st.dataframe(df_solar_15min)
		# Now proceed with the merge as previously described
		df_final = pd.merge(df_wind_15min, df_solar_15min, on=['Date', 'Interval'], how='left')

		st.dataframe(df_final)

	# Get Hydro Forecast
	st.subheader("Hydro Data", divider = "blue")
	if st.button("Get Hydro Data"):
		## INSTANCE curve hour
		curve = session.get_curve(name='pro ro hydro tot mwh/h cet h f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_h = curve.get_instance(issue_date=issue_date_str)
		pd_s_h = ts_h.to_pandas() # convert TS object to pandas.Series object
		pd_df_h = pd_s_h.to_frame() # convert pandas.Series to pandas.DataFrame
		st.dataframe(pd_df_h)
		# Writing the hourly values to the Trading Tool file
		pd_df_h.to_csv("./Market Fundamentals/Hydro_data_hourly.csv")
		# Load the wind data from CSV without altering the date format
		hydro_data_path = './Market Fundamentals/Hydro_data_hourly.csv'  # Update with the actual path
		hydro_data = pd.read_csv(hydro_data_path)

		# Writing the quarterly hydro data to the Volue data Excel file
		hydro_data_path = './Market Fundamentals/Hydro_data_hourly.csv'  # Update with the actual path
		hydro_data = pd.read_csv(hydro_data_path)
		# Write to Excel
		excel_file_path = './Market Fundamentals/Volue_data.xlsx'  # Update with the actual path
		workbook = load_workbook(excel_file_path)
		sheet = workbook["Volue_Data_eng"] 
		excel_row = 4
		for index, row in hydro_data.iterrows():
			cell = f'AI{excel_row}'
			sheet[cell] = row[0]  # Assuming data to write is in the second column
			cell = f'AJ{excel_row}'
			sheet[cell] = row[1]  # Assuming data to write is in the second column
			print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
			excel_row += 1
		workbook.save(filename=excel_file_path)
		print("Excel file has been updated.")

	# Get Temperature Forecast
	st.subheader("Temperature Data", divider = "red")
	if st.button("Get Temperature Data"):
		## INSTANCE curve 15 min
		curve = session.get_curve(name='tt ro con ec00 °c cet min15 f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_15min = curve.get_instance(issue_date=issue_date_str)
		pd_s_15min = ts_15min.to_pandas() # convert TS object to pandas.Series object
		pd_df_15min = pd_s_15min.to_frame() # convert pandas.Series to pandas.DataFrame
		st.dataframe(pd_df_15min)
		pd_df_15min.to_csv("./Market Fundamentals/Temperature_data_15min.csv")

		# Writing the quarterly pv data to the Volue data Excel file
		temp_data_path = './Market Fundamentals/Temperature_data_15min.csv'  # Update with the actual path
		temp_data = pd.read_csv(temp_data_path)
		# Write to Excel
		excel_file_path = './Market Fundamentals/Volue_data.xlsx'  # Update with the actual path
		workbook = load_workbook(excel_file_path)
		sheet = workbook["Volue_Data_eng"] 
		excel_row = 4
		for index, row in temp_data.iterrows():
			cell = f'BN{excel_row}'
			sheet[cell] = row[0]  # Assuming data to write is in the second column
			cell = f'BO{excel_row}'
			sheet[cell] = row[1]  # Assuming data to write is in the second column
			print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
			excel_row += 1
		workbook.save(filename=excel_file_path)
		print("Excel file has been updated.")

	# Get Price Forecast
	st.subheader("Price Data", divider = "grey")
	if st.button("Get Price Data"):
		## INSTANCE curve hour
		curve = session.get_curve(name='pri ro spot ec12ens ron/mwh cet h f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_h = curve.get_instance(issue_date=issue_date_str)
		pd_s_h = ts_h.to_pandas() # convert TS object to pandas.Series object
		pd_df_h = pd_s_h.to_frame() # convert pandas.Series to pandas.DataFrame
		st.dataframe(pd_df_h)
		# Writing the hourly values to the Trading Tool file
		pd_df_h.to_csv("./Market Fundamentals/Price_data_hourly.csv")
		# Load the wind data from CSV without altering the date format
		price_data_path = './Market Fundamentals/Price_data_hourly.csv'  # Update with the actual path
		price_data = pd.read_csv(price_data_path)

		# Determine tomorrow's date as a string to match your CSV format
		tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
		two_days_ahead = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
		three_days_ahead = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')

		# Filter rows based on the string representation of tomorrow's date
		# Assuming the date in your CSV is in the format 'YYYY-MM-DD' and is in the first column
		tomorrow_data = price_data[price_data.iloc[:, 0].str.startswith(tomorrow)]
		two_days_ahead_data = price_data[price_data.iloc[:, 0].str.startswith(two_days_ahead)]
		three_days_ahead_data = price_data[price_data.iloc[:, 0].str.startswith(three_days_ahead)]
		st.dataframe(tomorrow_data)
		st.dataframe(two_days_ahead_data)
		st.dataframe(three_days_ahead_data)
		# Write to Excel
		excel_file_path = './Market Fundamentals/Volue_data.xlsx'  # Update with the actual path
		workbook = load_workbook(excel_file_path)
		sheet = workbook["Pret_PZU"] 

		# Confirm we have data to write
		if len(tomorrow_data) > 0:
			excel_row = 3
			for index, row in tomorrow_data.iterrows():
				if excel_row == 11 or excel_row == 24:
					excel_row += 1
				cell = f'AE{excel_row}'
				sheet[cell] = row[1]  # Assuming data to write is in the second column
				print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
				excel_row += 1
		if len(two_days_ahead_data) > 0:
			excel_row = 3
			for index, row in two_days_ahead_data.iterrows():
				if excel_row == 11 or excel_row == 24:
					excel_row += 1
				cell = f'AF{excel_row}'
				sheet[cell] = row[1]  # Assuming data to write is in the second column
				print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
				excel_row += 1
		if len(three_days_ahead_data) > 0:
			excel_row = 3
			for index, row in three_days_ahead_data.iterrows():
				if excel_row == 11 or excel_row == 24:
					excel_row += 1
				cell = f'AG{excel_row}'
				sheet[cell] = row[1]  # Assuming data to write is in the second column
				print(f"Writing {row[1]} to {cell}")  # Diagnostic print to confirm writing
				excel_row += 1
			workbook.save(filename=excel_file_path)
			print("Excel file has been updated.")
		else:
			print("No data available for tomorrow to write into the Excel file.")

	# Updating PZU sheet date
	st.subheader("Updating Dates", divider = True)
	if st.button("Update Date"):
		updating_PZU_date()

	

	# Fething the Transelectrica data
	st.subheader("Transelectrica Data", divider="violet")
	if st.button("Fetch Transelectrica"):
		# 1. Consumption
		# Now you can call this function with the path to your consumption data file
		processed_data = process_file_consumption_transelectrica('./Market Fundamentals/Transelectrica_data/weekly consumtion 2023.xlsx')

		# First, ensure we're working with string types to avoid errors on non-string types
		processed_data['Date'] = processed_data['Date'].astype(str)

		# Then, filter out any rows where 'Date' does not contain a valid date string (e.g., the string "Data")
		processed_data = processed_data[processed_data['Date'].str.contains(r'\d{4}-\d{2}-\d{2}')]

		# Now, safely convert 'Date' column to datetime format
		processed_data['Date'] = pd.to_datetime(processed_data['Date'])

		# Filter for current montha and year
		# Get the current date
		current_date = datetime.now()

		# Extract the current year and month
		current_year = current_date.year
		current_month = current_date.month

		# Filter the data for the current year and month
		filtered_data = processed_data[(processed_data['Date'].dt.year == current_year) & (processed_data['Date'].dt.month == current_month)]

		filtered_data.dropna(inplace=True)
		filtered_data.to_excel('./Market Fundamentals/Transelectrica_data/Weekly_Consumption_2024.xlsx', index=False)

		# Example usage
		file_path = './Market Fundamentals/Transelectrica_data/weekly_production_2023.xlsx'  # Change this to your actual file path
		processed_data = process_file_production_transelectrica(file_path)

		# First, ensure we're working with string types to avoid errors on non-string types
		processed_data['Date'] = processed_data['Date'].astype(str)

		# Then, filter out any rows where 'Date' does not contain a valid date string (e.g., the string "Data")
		processed_data = processed_data[processed_data['Date'].str.contains(r'\d{4}-\d{2}-\d{2}')]

		# Now, safely convert 'Date' column to datetime format
		processed_data['Date'] = pd.to_datetime(processed_data['Date'])

		# Filter for April 2024
		filtered_data = filtered_data = processed_data[(processed_data['Date'].dt.year == current_year) & (processed_data['Date'].dt.month == current_month)]
		filtered_data.dropna(inplace=True)

		filtered_data.to_excel('./Market Fundamentals/Transelectrica_data/Weekly_Production_2024.xlsx', index=False)

	# Fething the Entsoe data
	st.subheader("Entsoe Data", divider="violet")
	start_date = st.date_input("Select Start Date", value=pd.to_datetime('2024-04-11'))
	end_date = st.date_input("Select End Date", value=pd.to_datetime('2024-04-12'))
	# start_date = pd.to_datetime('2024-04-14')
	# end_date = pd.to_datetime('2024-04-15')
	# Convert the input dates to Timestamps with time set to '0000' hours
	start = pd.Timestamp(f"{start_date.strftime('%Y%m%d')}0000", tz='Europe/Bucharest')
	end = pd.Timestamp(f"{end_date.strftime('%Y%m%d')}0000", tz='Europe/Bucharest')
	
	# start = pd.Timestamp('202404110000', tz='Europe/Bucharest')  # Adjust the start date as needed
	# end = pd.Timestamp('202404120000', tz='Europe/Bucharest')    # Adjust the end date as needed
	if st.button("Entsoe"):
		# Fetch the DataFrames
		df_imbalance_prices = imbalance_prices(start, end)
		df_imbalance_volumes = imbalance_volumes(start, end)
		# Merge the DataFrames on their indices
		df_imbalance = pd.merge(df_imbalance_prices, df_imbalance_volumes, left_index=True, right_index=True, how='inner')
		# Assuming df_imbalance is your merged DataFrame
		df_imbalance = df_imbalance.rename(columns={'Long': 'Excedent Price',
													'Short': 'Deficit Price'})
		st.dataframe(df_imbalance)
		# Fetching the Activated mFRR capacities
		if (end_date-start_date).days > 1:
			st.text("Fetching data for more than one day")
			df_activated_energy = query_daily_mFRR(start_date, end_date)
		else:
			data = activated_mFRR_energy(start, end)
			df_activated_energy = creating_mFRR_dfs(data)
		st.dataframe(df_activated_energy)

		# Fethcing the Actual Load
		df_actual_load = actual_load(start, end)
		# st.dataframe(df_actual_load)

		# Fetching the Generation Forecast
		df_generation_forecast = generation_forecast(start, end)
		# st.dataframe(df_generation_forecast)

		# Fetching the Generation per Source
		df_actual_generation_source = actual_generation_source(start, end)
		st.dataframe(df_actual_generation_source)
		st.write(df_actual_generation_source.columns)
		
		# Creating the dataframe with all the Entsoe data
		# 1. Concatenating the df_activated_energy and df_imbalance
		df_imbalance.reset_index(inplace=True)
		df_imbalance.columns = ['Timestamp', 'Excedent Price', 'Deficit Price', 'Imbalance Volume']

		# Convert 'Timestamp' to datetime format
		df_imbalance['Timestamp'] = pd.to_datetime(df_imbalance['Timestamp'])

		# Create 'Date' and 'Interval' columns from 'Timestamp'
		df_imbalance['Date'] = df_imbalance['Timestamp'].dt.strftime('%d.%m.%Y')
		df_imbalance['Interval'] = ((df_imbalance['Timestamp'].dt.hour * 60 + df_imbalance['Timestamp'].dt.minute) // 15 + 1)

		# Now proceed with the merge as previously described
		df_final = pd.merge(df_activated_energy, df_imbalance, on=['Date', 'Interval'], how='left')

		# Optionally remove the 'Timestamp' column if it's no longer needed
		df_final.drop(columns=['Timestamp'], inplace=True)

		# 2. Adding the Actual Load
		df_actual_load.reset_index(inplace=True)
		df_actual_load.rename(columns={'index': 'Timestamp'}, inplace=True)
		# Convert 'Timestamp' to datetime format
		df_actual_load['Timestamp'] = pd.to_datetime(df_actual_load['Timestamp'])

		# Create 'Date' and 'Interval' columns from 'Timestamp'
		df_actual_load['Date'] = df_actual_load['Timestamp'].dt.strftime('%d.%m.%Y')
		df_actual_load['Interval'] = ((df_actual_load['Timestamp'].dt.hour * 60 + df_actual_load['Timestamp'].dt.minute) // 15 + 1)

		# Now proceed with the merge as previously described
		df_final_2 = pd.merge(df_final, df_actual_load, on=['Date', 'Interval'], how='left')

		# Optionally remove the 'Timestamp' column if it's no longer needed
		df_final_2.drop(columns=['Timestamp'], inplace=True)

		# 3. Adding the Generation Forecast
		# Convert the Series to DataFrame
		df_generation_forecast = df_generation_forecast.to_frame('Generation Forecast')
		# If your Series had the timestamp as the index (which is common in time series data), you can reset the index to make it a column:
		df_generation_forecast.reset_index(inplace=True)
		df_generation_forecast.rename(columns={'index': 'Timestamp'}, inplace=True)

		# Create 'Date' and 'Interval' columns from 'Timestamp'
		df_generation_forecast['Date'] = df_generation_forecast['Timestamp'].dt.strftime('%d.%m.%Y')
		df_generation_forecast['Interval'] = ((df_generation_forecast['Timestamp'].dt.hour * 60 + df_generation_forecast['Timestamp'].dt.minute) // 15 + 1)

		# Now proceed with the merge as previously described
		df_final_3 = pd.merge(df_final_2, df_generation_forecast, on=['Date', 'Interval'], how='left')

		# Optionally remove the 'Timestamp' column if it's no longer needed
		df_final_3.drop(columns=['Timestamp'], inplace=True)

		# 4. Adding the Generation Forecast per Source
		df_actual_generation_source.reset_index(inplace=True)
		df_actual_generation_source.columns = ['Timestamp', "Biomass", "Fossil Brown coal/Lignite", "Fossil Gas", "Fossil Hard coal", 
		"Hydro Run-of-river and poundage", "Hydro Water Reservoir", "Nuclear", "Solar", "Wind Onshore"]

		# Convert 'Timestamp' to datetime format
		df_actual_generation_source['Timestamp'] = pd.to_datetime(df_actual_generation_source['Timestamp'])

		# Create 'Date' and 'Interval' columns from 'Timestamp'
		df_actual_generation_source['Date'] = df_actual_generation_source['Timestamp'].dt.strftime('%d.%m.%Y')
		df_actual_generation_source['Interval'] = ((df_actual_generation_source['Timestamp'].dt.hour * 60 + df_actual_generation_source['Timestamp'].dt.minute) // 15 + 1)

		# Now proceed with the merge as previously described
		df_final_4 = pd.merge(df_final_3, df_actual_generation_source, on=['Date', 'Interval'], how='left')

		# Optionally remove the 'Timestamp' column if it's no longer needed
		df_final_4.drop(columns=['Timestamp'], inplace=True)

		# Display the merged DataFrame
		st.dataframe(df_final_4)

		# Exporting the final Entsoe dataframe to Excel
		df_final_4.to_excel("./Market Fundamentals/Entsoe_data/Entsoe_data.xlsx")

		# Formatting the Date column
		# Assuming df_final_4 is your DataFrame
		# Create an Excel writer object
		with pd.ExcelWriter("./Market Fundamentals/Entsoe_data/Entsoe_data.xlsx", 
							engine='xlsxwriter', 
							datetime_format='dd.mm.yyyy') as writer:
			df_final_4.to_excel(writer, index=False)

			# Access the xlsxwriter workbook and worksheet objects from the dataframe
			workbook  = writer.book
			worksheet = writer.sheets['Sheet1']

			# Get the number of rows in the DataFrame
			num_rows = len(df_final_4.index)

			# Define a format object for Excel to use
			date_format = workbook.add_format({'num_format': 'dd.mm.yyyy'})

			# Apply the date format to the column with dates (assuming it's the first column)
			worksheet.set_column(0, 0, None, date_format)  # Column 'A:A' if your dates are in the first column

		

		






