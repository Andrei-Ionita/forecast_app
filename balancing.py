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
from entsoe import EntsoePandasClient
import xml.etree.ElementTree as ET

#=====================================================================Data Engineering============================================================================================================
api_key_entsoe = os.getenv("api_key_entsoe")
client = EntsoePandasClient(api_key=api_key_entsoe)

def get_issue_date():
    issue_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    print(issue_date)
    # Format the date as a string in the desired format
    issue_date_str = issue_date.isoformat()
    issue_date_str = issue_date.strftime('%Y-%m-%dT%H:%M')
    print(issue_date_str)
    return issue_date_str, issue_date

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

# 2. Imbalance Volumes
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

#7. Fetching the Forecast Load
def load_forecast(start, end):
	# Define the start and end timestamps for the query
	# start = pd.Timestamp('20240401', tz='Europe/Bucharest')  # Adjust the start date as needed
	# end = pd.Timestamp('20240411', tz='Europe/Bucharest')    # Adjust the end date as needed

	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania

	# Fetch Load Forecast
	load_forecast = client.query_load_forecast(country_code, start=start, end=end)

	# Display or analyze the fetched data
	return load_forecast

#8. Fetching the Forecast Load in CET for the Trading_Tool Update
def load_forecast_CET(start_cet, end_cet):
	# Define the start and end timestamps for the query
	# start = pd.Timestamp('20240401', tz='Europe/Bucharest')  # Adjust the start date as needed
	# end = pd.Timestamp('20240411', tz='Europe/Bucharest')    # Adjust the end date as needed

	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania

	# Fetch Load Forecast
	load_forecast_cet = client.query_load_forecast(country_code, start=start_cet, end=end_cet)
	load_forecast_cet.reset_index(inplace=True)
	load_forecast_cet.columns = ["Timestamp", "Load"]

	# Convert 'Timestamp' to datetime format
	load_forecast_cet['Timestamp'] = pd.to_datetime(load_forecast_cet['Timestamp'])
	# Convert datetime to CET timezone
	load_forecast_cet['Timestamp'] = load_forecast_cet['Timestamp'].dt.tz_convert('CET')

	# Remove timezone information but keep the time in CET
	load_forecast_cet['Timestamp'] = load_forecast_cet['Timestamp'].dt.tz_localize(None)
	load_forecast_cet.to_excel("./Market Fundamentals/Entsoe_data/load_forecast.xlsx", index=False)
	# Display or analyze the fetched data
	return load_forecast_cet

#9. Fetching the Load and Forecast Load
def load_and_forecast_load(start_cet, end_cet):
	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania

	# Fetch Load Forecast
	load = client.query_load_and_forecast(country_code, start=start_cet, end=end_cet)
	load.reset_index(inplace=True)
	load.rename(columns = {"index": "Timestamp"}, inplace=True)
	return load

#10. Fetch Wind and Solar Generation
def wind_solar_generation(start_cet, end_cet):
	# Set the country code for Romania
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania
	
	# Fetch Wind and Solar Generation
	wind_solar_generation = client.query_intraday_wind_and_solar_forecast(country_code, start=start_cet, end=end_cet, psr_type=None)
	wind_solar_generation.reset_index(inplace=True)
	wind_solar_generation.rename(columns = {"index": "Timestamp"}, inplace=True)
	return wind_solar_generation

#11. Fetch Scheduled Exchanges BG
def scheduled_exchanges_BG_RO(start_cet, end_cet):
	country_code_from = "BG"
	country_code_to = "RO"
	scheduled_exchanges_BG_RO_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_BG_RO = scheduled_exchanges_BG_RO_series.to_frame(name='Power_BG_RO [MW]')
	scheduled_exchanges_BG_RO.reset_index(inplace=True)
	scheduled_exchanges_BG_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_BG_RO

def scheduled_exchanges_RO_BG(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "BG"
	scheduled_exchanges_RO_BG_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_RO_BG = scheduled_exchanges_RO_BG_series.to_frame(name='Power_RO_BG [MW]')
	scheduled_exchanges_RO_BG.reset_index(inplace=True)
	scheduled_exchanges_RO_BG.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_RO_BG

#12. Fetch Scheduled Exchanges HU
def scheduled_exchanges_HU_RO(start_cet, end_cet):
	country_code_from = "HU"
	country_code_to = "RO"
	scheduled_exchanges_HU_RO_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_HU_RO = scheduled_exchanges_HU_RO_series.to_frame(name='Power_HU_RO [MW]')
	scheduled_exchanges_HU_RO.reset_index(inplace=True)
	scheduled_exchanges_HU_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_HU_RO

def scheduled_exchanges_RO_HU(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "HU"
	scheduled_exchanges_RO_HU_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_RO_HU = scheduled_exchanges_RO_HU_series.to_frame(name='Power_RO_HU [MW]')
	scheduled_exchanges_RO_HU.reset_index(inplace=True)
	scheduled_exchanges_RO_HU.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_RO_HU

#12. Fetch Scheduled Exchanges RS
def scheduled_exchanges_RS_RO(start_cet, end_cet):
	country_code_from = "RS"
	country_code_to = "RO"
	scheduled_exchanges_RS_RO_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_RS_RO = scheduled_exchanges_RS_RO_series.to_frame(name='Power_RS_RO [MW]')
	scheduled_exchanges_RS_RO.reset_index(inplace=True)
	scheduled_exchanges_RS_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_RS_RO

def scheduled_exchanges_RO_RS(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "RS"
	scheduled_exchanges_RO_RS_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_RO_RS = scheduled_exchanges_RO_RS_series.to_frame(name='Power_RO_RS [MW]')
	scheduled_exchanges_RO_RS.reset_index(inplace=True)
	scheduled_exchanges_RO_RS.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_RO_RS

#13. Fetch Scheduled Exchanges MD
def scheduled_exchanges_MD_RO(start_cet, end_cet):
	country_code_from = "MD"
	country_code_to = "RO"
	scheduled_exchanges_MD_RO_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_MD_RO = scheduled_exchanges_MD_RO_series.to_frame(name='Power_MD_RO [MW]')
	scheduled_exchanges_MD_RO.reset_index(inplace=True)
	scheduled_exchanges_MD_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_MD_RO

def scheduled_exchanges_RO_MD(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "MD"
	scheduled_exchanges_RO_MD_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_RO_MD = scheduled_exchanges_RO_MD_series.to_frame(name='Power_RO_MD [MW]')
	scheduled_exchanges_RO_MD.reset_index(inplace=True)
	scheduled_exchanges_RO_MD.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_RO_MD

#14. Fetch Scheduled Exchanges UA
def scheduled_exchanges_UA_RO(start_cet, end_cet):
	country_code_from = "UA"
	country_code_to = "RO"
	scheduled_exchanges_UA_RO_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_UA_RO = scheduled_exchanges_UA_RO_series.to_frame(name='Power_UA_RO [MW]')
	scheduled_exchanges_UA_RO.reset_index(inplace=True)
	scheduled_exchanges_UA_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_UA_RO

def scheduled_exchanges_RO_UA(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "UA"
	scheduled_exchanges_RO_UA_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	scheduled_exchanges_RO_UA = scheduled_exchanges_RO_UA_series.to_frame(name='Power_RO_UA [MW]')
	scheduled_exchanges_RO_UA.reset_index(inplace=True)
	scheduled_exchanges_RO_UA.rename(columns = {"index": "Timestamp"}, inplace=True)
	return scheduled_exchanges_RO_UA

# 15. Fetch Physical Flow RO_BG
def flow_BG_RO(start_cet, end_cet):
	country_code_from = "BG"
	country_code_to = "RO"
	flow_BG_RO_series = client.query_crossborder_flows(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	flow_BG_RO = flow_BG_RO_series.to_frame(name='Actual_Power_BG_RO [MW]')
	flow_BG_RO.reset_index(inplace=True)
	flow_BG_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return flow_BG_RO

def flow_RO_BG(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "BG"
	flow_RO_BG_series = client.query_crossborder_flows(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	flow_RO_BG = flow_RO_BG_series.to_frame(name='Actual_Power_BG_RO [MW]')
	flow_RO_BG.reset_index(inplace=True)
	flow_RO_BG.rename(columns = {"index": "Timestamp"}, inplace=True)
	return flow_RO_BG

#16. Fetch Physical FLow RO_HU
def flow_HU_RO(start_cet, end_cet):
	country_code_from = "HU"
	country_code_to = "RO"
	flow_HU_RO_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	flow_HU_RO = flow_HU_RO_series.to_frame(name='Actual_Power_HU_RO [MW]')
	flow_HU_RO.reset_index(inplace=True)
	flow_HU_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return flow_HU_RO

def flow_RO_HU(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "HU"
	flow_RO_HU_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	flow_RO_HU = flow_RO_HU_series.to_frame(name='Actual_Power_RO_HU [MW]')
	flow_RO_HU.reset_index(inplace=True)
	flow_RO_HU.rename(columns = {"index": "Timestamp"}, inplace=True)
	return flow_RO_HU

#17. Fetch Physical FLow RO_RS
def flow_RS_RO(start_cet, end_cet):
	country_code_from = "RS"
	country_code_to = "RO"
	flow_RS_RO_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	flow_RS_RO = flow_RS_RO_series.to_frame(name='Actual_Power_RS_RO [MW]')
	flow_RS_RO.reset_index(inplace=True)
	flow_RS_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return flow_RS_RO

def flow_RO_RS(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "RS"
	flow_RO_RS_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	flow_RO_RS = flow_RO_RS_series.to_frame(name='Actual_Power_RO_RS [MW]')
	flow_RO_RS.reset_index(inplace=True)
	flow_RO_RS.rename(columns = {"index": "Timestamp"}, inplace=True)
	return flow_RO_RS

#18. Fetch Physical FLow RO_MD
def flow_MD_RO(start_cet, end_cet):
	country_code_from = "MD"
	country_code_to = "RO"
	flow_MD_RO_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	flow_MD_RO = flow_MD_RO_series.to_frame(name='Actual_Power_MD_RO [MW]')
	flow_MD_RO.reset_index(inplace=True)
	flow_MD_RO.rename(columns = {"index": "Timestamp"}, inplace=True)
	return flow_MD_RO

def flow_RO_MD(start_cet, end_cet):
	country_code_from = "RO"
	country_code_to = "MD"
	flow_RO_MD_series = client.query_scheduled_exchanges(country_code_from, country_code_to, start=start_cet, end=end_cet)
	# Convert the TimeSeries to a DataFrame
	flow_RO_MD = flow_RO_MD_series.to_frame(name='Actual_Power_RO_MD [MW]')
	flow_RO_MD.reset_index(inplace=True)
	flow_RO_MD.rename(columns = {"index": "Timestamp"}, inplace=True)
	return flow_RO_MD


# Physical Crossborder All Borders
def flows_crossborders(start_cet, end_cet):
	country_code = 'RO'  # ISO-3166 alpha-2 code for Romania
	all_borders_physical_flows = client.query_physical_crossborder_allborders(country_code, start_cet, end_cet, export=True)
	return all_borders_physical_flows

#=====================================================================BALANGING MARKET INTRADAY===================================================================================================

def render_balancing_market_intraday_page():
	
	# Web App Title
	st.header("Balancing Market :blue[Intraday Dashboard]")

	# Fetching the data and crating the dataframe/dataframes
	issue_date = get_issue_date()[1]
	start_date = st.date_input("Select Start Date", value=pd.to_datetime(issue_date + timedelta(days=1)))
	end_date = st.date_input("Select End Date", value=pd.to_datetime(issue_date + timedelta(days=2)))
	# start_date = pd.to_datetime('2024-04-14')
	# end_date = pd.to_datetime('2024-04-15')
	# Convert the input dates to Timestamps with time set to '0000' hours
	start = pd.Timestamp(f"{start_date.strftime('%Y%m%d')}0000", tz='Europe/Bucharest')
	end = pd.Timestamp(f"{end_date.strftime('%Y%m%d')}0000", tz='Europe/Bucharest')
	# Switching to CET time for the Load Forecast
	start_cet = pd.Timestamp(f"{start_date.strftime('%Y%m%d')}0000", tz='Europe/Budapest')
	end_cet = pd.Timestamp(f"{end_date.strftime('%Y%m%d')}0000", tz='Europe/Budapest')

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
		# st.dataframe(df_activated_energy)

		# Fethcing the Actual Load
		df_actual_load = actual_load(start, end)
		# st.dataframe(df_actual_load)

		# Fethcing the Forecast Load
		df_load_forecast = load_forecast(start, end)
		df_load_forecast_CET = load_forecast_CET(start_cet, end_cet)
		st.dataframe(df_load_forecast_CET)

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
	
	if st.button("Intraday Market Fundamentals"):
		# Fetch load and forecast
		load_and_forecast_df = load_and_forecast_load(start_cet, end_cet)
		st.dataframe(load_and_forecast_df)
		# Fetch the Wind and Solar Generation
		wind_solar_generation_df = wind_solar_generation(start_cet, end_cet)
		st.dataframe(wind_solar_generation_df)
		# Creating the Intraday Dataframe
		df_fundamentals = pd.merge(load_and_forecast_df, wind_solar_generation_df, on=['Timestamp'], how='left')
		# Subtract one hour from the timestamps
		df_fundamentals['Timestamp'] = df_fundamentals['Timestamp'] - pd.Timedelta(hours=1)
		df_fundamentals['Timestamp'] = df_fundamentals['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S%z')
		st.dataframe(df_fundamentals)
		df_fundamentals['Timestamp'] = pd.to_datetime(df_fundamentals['Timestamp'])
		st.dataframe(df_fundamentals)
		# scheduled_exchanges_RO_BG_df = scheduled_exchanges_RO_BG(start_cet, end_cet)
		# scheduled_exchanges_BG_RO_df = scheduled_exchanges_BG_RO(start_cet, end_cet)
		# # Creating the Intraday Dataframe
		# df_final = pd.merge(scheduled_exchanges_RO_BG_df , scheduled_exchanges_BG_RO_df, on=['Timestamp'], how='left')

		# # Adding the RO_HU crossborder scheduled exchanges to the overall scheduled exchanges dafatrame
		# scheduled_exchanges_RO_HU_df = scheduled_exchanges_RO_HU(start_cet, end_cet)
		# scheduled_exchanges_HU_RO_df = scheduled_exchanges_HU_RO(start_cet, end_cet)
		# # Creating the Intermediate RO_HU dataframe
		# df_RO_HU = pd.merge(scheduled_exchanges_RO_HU_df , scheduled_exchanges_HU_RO_df, on=['Timestamp'], how='left')
		# # Adding the df_RO_HU to the final dataframe of scheduled exchanges
		# df_final = pd.merge(df_RO_HU, df_final, on=['Timestamp'], how='left')
		# # Filling the empty quarters of the RO_BG exchanges
		# df_final['Timestamp'] = pd.to_datetime(df_final['Timestamp'])

		# # Set the Timestamp column as the index
		# df_final.set_index('Timestamp', inplace=True)

		# # Fill missing values for Power_RO_BG [MW] and Power_BG_RO [MW]
		# df_final['Power_RO_BG [MW]'] = df_final['Power_RO_BG [MW]'].fillna(method='ffill').fillna(method='bfill')
		# df_final['Power_BG_RO [MW]'] = df_final['Power_BG_RO [MW]'].fillna(method='ffill').fillna(method='bfill')

		# # Reset the index
		# df_final.reset_index(inplace=True)
		# # Adjusting the timestamps to the correct ones
		# # Convert the 'Timestamp' column to datetime, including timezone
		# df_final['Timestamp'] = pd.to_datetime(df_final['Timestamp'], utc=True).dt.tz_convert('Europe/Bucharest')

		# # Subtract one hour from the timestamps
		# df_final['Timestamp'] = df_final['Timestamp'] - pd.Timedelta(hours=1)

		# # Convert back to the same string format
		# df_final['Timestamp'] = df_final['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S%z')

		# # Adding the RO_RS_df to the final dataframe of scheduled exchanges
		# scheduled_exchanges_RO_RS_df = scheduled_exchanges_RO_RS(start_cet, end_cet)
		# scheduled_exchanges_RS_RO_df = scheduled_exchanges_RS_RO(start_cet, end_cet)
		# # Creating the Intraday Dataframe
		# df_RO_RS = pd.merge(scheduled_exchanges_RO_RS_df , scheduled_exchanges_RS_RO_df, on=['Timestamp'], how='left')
		# # Subtract one hour from the timestamps
		# df_RO_RS['Timestamp'] = df_RO_RS['Timestamp'] - pd.Timedelta(hours=1)
		# df_RO_RS['Timestamp'] = df_RO_RS['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S%z')

		# # Adding the RO_RS_df to the df_final
		# df_final = pd.merge(df_final, df_RO_RS, on=['Timestamp'], how='left')
		# # Filling the empty quarters of the RO_RS exchanges
		# df_final['Timestamp'] = pd.to_datetime(df_final['Timestamp'])

		# # Set the Timestamp column as the index
		# df_final.set_index('Timestamp', inplace=True)

		# # Fill missing values for Power_RO_BG [MW] and Power_BG_RO [MW]
		# df_final['Power_RO_RS [MW]'] = df_final['Power_RO_RS [MW]'].fillna(method='ffill').fillna(method='bfill')
		# df_final['Power_RS_RO [MW]'] = df_final['Power_RS_RO [MW]'].fillna(method='ffill').fillna(method='bfill')

		# # Reset the index
		# df_final.reset_index(inplace=True)

		# # Adding the RO_MD_df to the final dataframe of scheduled exchanges
		# scheduled_exchanges_RO_MD_df = scheduled_exchanges_RO_MD(start_cet, end_cet)
		# scheduled_exchanges_MD_RO_df = scheduled_exchanges_MD_RO(start_cet, end_cet)
		# # Creating the Intraday Dataframe
		# df_RO_MD = pd.merge(scheduled_exchanges_RO_MD_df , scheduled_exchanges_MD_RO_df, on=['Timestamp'], how='left')
		# # Subtract one hour from the timestamps
		# df_RO_MD['Timestamp'] = df_RO_MD['Timestamp'] - pd.Timedelta(hours=1)
		# df_RO_MD['Timestamp'] = df_RO_MD['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S%z')
	
		# df_RO_MD['Timestamp'] = pd.to_datetime(df_RO_MD['Timestamp'])
		# # Adding the RO_MD_df to the df_final
		# df_final = pd.merge(df_final, df_RO_MD, on=['Timestamp'], how='left')
		# # Filling the empty quarters of the RO_MD exchanges
		# df_final['Timestamp'] = pd.to_datetime(df_final['Timestamp'])

		# # Set the Timestamp column as the index
		# df_final.set_index('Timestamp', inplace=True)

		# # Fill missing values for Power_RO_BG [MW] and Power_BG_RO [MW]
		# df_final['Power_RO_MD [MW]'] = df_final['Power_RO_MD [MW]'].fillna(method='ffill').fillna(method='bfill')
		# df_final['Power_MD_RO [MW]'] = df_final['Power_MD_RO [MW]'].fillna(method='ffill').fillna(method='bfill')

		# # Reset the index
		# df_final.reset_index(inplace=True)

		# # Adding the RO_UA_df to the final dataframe of scheduled exchanges
		# scheduled_exchanges_RO_UA_df = scheduled_exchanges_RO_UA(start_cet, end_cet)
		# scheduled_exchanges_UA_RO_df = scheduled_exchanges_UA_RO(start_cet, end_cet)
		# # Creating the Intraday Dataframe
		# df_RO_UA = pd.merge(scheduled_exchanges_RO_UA_df , scheduled_exchanges_UA_RO_df, on=['Timestamp'], how='left')
		# # Subtract one hour from the timestamps
		# df_RO_UA['Timestamp'] = df_RO_UA['Timestamp'] - pd.Timedelta(hours=1)
		# df_RO_UA['Timestamp'] = df_RO_UA['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S%z')
		# st.dataframe(df_RO_UA)
		# df_RO_UA['Timestamp'] = pd.to_datetime(df_RO_UA['Timestamp'])
		# # Adding the RO_MD_df to the df_final
		# df_final = pd.merge(df_final, df_RO_UA, on=['Timestamp'], how='left')
		# # Filling the empty quarters of the RO_MD exchanges
		# df_final['Timestamp'] = pd.to_datetime(df_final['Timestamp'])

		# # Set the Timestamp column as the index
		# df_final.set_index('Timestamp', inplace=True)

		# # Fill missing values for Power_RO_BG [MW] and Power_BG_RO [MW]
		# df_final['Power_RO_UA [MW]'] = df_final['Power_RO_UA [MW]'].fillna(method='ffill').fillna(method='bfill')
		# df_final['Power_UA_RO [MW]'] = df_final['Power_UA_RO [MW]'].fillna(method='ffill').fillna(method='bfill')

		# # Reset the index
		# df_final.reset_index(inplace=True)

		# st.dataframe(df_final)

		st.dataframe(flows_crossborders(start_cet, end_cet))