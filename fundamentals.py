import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import wapi
from openpyxl import load_workbook

# ================================================================================VOLUE data==================================================================================

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


#====================================================================================Rendering into App================================================================================

def render_fundamentals_page():
	
	# Page tittle
	st.header("Market Fundamentals", divider = "rainbow")

	# Get Wind Forecast
	st.subheader("Wind Data", divider = "green")
	
	if st.button("Get Wind Data"):
		## INSTANCES curve 15 min
		curve = session.get_curve(name='pro ro wnd ec00 mwh/h cet min15 f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_15min = curve.get_instance(issue_date='2024-04-01T00:00')
		pd_s_15min = ts_15min.to_pandas() # convert TS object to pandas.Series object
		pd_df_15min = pd_s_15min.to_frame() # convert pandas.Series to pandas.DataFrame
		st.dataframe(pd_df_15min)
		## INSTANCES curve hour
		curve = session.get_curve(name='pro ro wnd fwd mw cet h f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_h = curve.get_instance(issue_date='2024-04-01T00:00')
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


	# Get Solar Forecast
	st.subheader("PV Data", divider = "orange")
	if st.button("Get Solar Data"):
		## INSTANCE curve 15 min
		curve = session.get_curve(name='pro ro spv ec00 mwh/h cet min15 f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_15min = curve.get_instance(issue_date='2024-04-01T00:00')
		pd_s_15min = ts_15min.to_pandas() # convert TS object to pandas.Series object
		pd_df_15min = pd_s_15min.to_frame() # convert pandas.Series to pandas.DataFrame
		st.dataframe(pd_df_15min)
		## INSTANCE curve hour
		curve = session.get_curve(name='pro ro spv fwd mw cet h f')
		# INSTANCES curves contain a timeseries for each defined issue dates
		# Get a list of available curves with issue dates within a timerange with:
		# curve.search_instances(issue_date_from='2018-01-01', issue_date_to='2018-01-01')
		ts_h = curve.get_instance(issue_date='2024-04-01T00:00')
		pd_s_h = ts_h.to_pandas() # convert TS object to pandas.Series object
		pd_df_h = pd_s_h.to_frame() # convert pandas.Series to pandas.DataFrame
		st.dataframe(pd_df_h)