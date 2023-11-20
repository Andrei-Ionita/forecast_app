import streamlit as st
import streamlit.components.v1 as stc
import pandas as pd
import numpy as np
import base64
import xgboost as xgb
import joblib
import xlsxwriter
import os
import time
from datetime import datetime

session_start_time = time.time()

# Creating the holidays dataframe
# Creating the dictionary of holidays
New_year_and_day_after = pd.DataFrame({"holiday": "Anul Nou & A doua zi",
														"ds": pd.to_datetime(["2017-01-01", "2017-01-02", "2016-01-01", "2016-01-02", "2015-01-01", "2015-01-02", "2014-01-01", "2014-01-02", "2019-01-01",
																									"2019-01-02", "2018-01-01", "2018-01-02", "2020-01-01", "2020-01-02", "2021-01-01", "2021-01-02",
																									"2022-01-01", "2022-01-02", "2023-01-01", "2023-01-02"]),
														"lower_window": -1,
														"upper_window": 1})

National_holiday = pd.DataFrame({"holiday": "Ziua Nationala",
																 "ds": pd.to_datetime(["2016-12-01", "2015-12-01", "2014-12-01", "2018-12-01", "2019-12-01", "2020-12-01", "2021-12-01", "2022-12-01", "2023-12-01"]),
																 "lower_window": 0,
																 "upper_window": 1})
Ziua_Principatelor = pd.DataFrame({"holiday": "Ziua Principatelor",
																 "ds": pd.to_datetime(["2017-01-24", "2016-01-24", "2018-01-24", "2019-01-24", "2020-01-24", "2021-01-24", "2022-01-24", "2023-01-24"]),
																 "lower_window": 0,
																 "upper_window": 1})
Christmas = pd.DataFrame({"holiday": "Craciunul",
													"ds": pd.to_datetime(["2017-12-25", "2017-12-26", "2016-12-25", "2016-12-26", "2015-12-25", "2015-12-26", "2014-12-25", "2014-12-26", "2018-12-25", "2018-12-26", "2019-12-25", "2019-12-26", "2020-12-25", "2020-12-26", "2021-12-25", "2021-12-26",
																								"2022-12-25", "2022-12-26", "2023-12-25", "2023-12-26"]),
													"lower_window": -1,
													"upper_window": 1})
St_Andrew = pd.DataFrame({"holiday": "Sfantul Andrei",
													"ds": pd.to_datetime(["2017-11-30", "2016-11-30", "2015-11-30", "2014-11-30", "2018-11-30", "2019-11-30", "2020-11-30", "2021-11-30", "2022-11-30",
																								"2023-11-30"]),
													"lower_window": -1,
													"upper_window": 0})
Adormirea_Maicii_Domnului = pd.DataFrame({"holiday": "Adormirea Maicii Domnului",
																					"ds": pd.to_datetime(["2017-08-15", "2016-08-15", "2015-08-15", "2014-08-15", "2018-08-15", "2019-08-15", "2020-08-15", "2021-08-15","2022-08-15", "2023-08-15"])})
Rusalii = pd.DataFrame({"holiday": "Rusalii",
												"ds": pd.to_datetime(["2017-06-04", "2017-06-05", "2016-06-19", "2016-06-20", "2015-05-31", "2015-06-01", "2014-06-08", "2014-06-09", "2018-05-27", "2018-05-28", "2019-06-16", "2019-06-17", "2020-06-07", "2020-06-08", "2021-06-20", "2021-06-21",
																							"2022-06-12", "2022-06-13", "2023-06-04", "2023-06-05"])})
Ziua_Copilului = pd.DataFrame({"holiday": "Ziua Copilului",
															"ds": pd.to_datetime(["2017-06-01", "2018-06-01", "2019-06-01", "2020-06-01", "2021-06-01", "2022-06-01", "2023-06-01"])})
Ziua_Muncii = pd.DataFrame({"holiday": "Ziua Muncii",
														"ds": pd.to_datetime(["2017-05-01", "2016-05-01", "2015-05-01", "2014-05-01", "2018-05-01", "2019-05-01", "2020-05-01", "2021-05-01", "2022-05-01", "2023-05-01"])})
Pastele = pd.DataFrame({"holiday": "Pastele",
												"ds": pd.to_datetime(["2017-04-16", "2017-04-17", "2016-05-01", "2016-05-02", "2015-04-12", "2015-04-13", "2014-04-20", "2014-04-21", "2018-04-08", "2018-04-09", "2019-04-28", "2019-04-29", "2020-04-19", "2020-04-20", "2021-05-02", "2021-05-03",
																							"2022-04-24", "2022-04-25", "2023-04-16", "2023-04-17"]),
												"lower_window": -1,
												"upper_window": 1})
Vinerea_Mare = pd.DataFrame({"holiday": "Vinerea Mare",
														 "ds": pd.to_datetime(["2020-04-17", "2019-04-26", "2018-04-06", "2021-04-30", "2022-04-30", "2023-04-30"])})
Ziua_Unirii = pd.DataFrame({"holiday": "Ziua Unirii",
														"ds": pd.to_datetime(["2015-01-24", "2020-01-24", "2019-01-24", "2021-01-24", "2022-01-24", "2023-01-24"])})
Public_Holiday = pd.DataFrame({"holiday": "Public Holiday",
															"ds": pd.to_datetime(["2019-04-30"])})
holidays = pd.concat((New_year_and_day_after, National_holiday, Christmas, St_Andrew, Ziua_Principatelor, Adormirea_Maicii_Domnului, Rusalii, Ziua_Copilului, Ziua_Muncii,
											Pastele, Vinerea_Mare, Ziua_Unirii, Public_Holiday))

file_path = "./Solina/Production/Results_Production_xgb.xlsx"
def get_file_creation_date(file_path):
    """Returns the creation date of the file."""
    if os.path.exists(file_path):
        creation_time = os.path.getctime(file_path)
        return datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d')
    else:
        return "File not found"

def predicting_exporting(dataset):
	xgb_loaded = joblib.load("./Solina/Production/rs_xgb_Solina_prod.pkl")
	dataset_forecast = dataset.copy()
	dataset_forecast["Month"] = dataset_forecast.Data.dt.month

	dataset_forecast = dataset_forecast.drop("Data", axis=1)

	preds = xgb_loaded.predict(dataset_forecast.values)
	#Exporting Results to Excel
	workbook = xlsxwriter.Workbook("./Solina/Production/Results_Production_xgb.xlsx")
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

def predicting_exporting_Consumption_Solina(forecast_dataset):
	# Predict on forecast data
	forecast_dataset["Month"] = forecast_dataset.Data.dt.month
	forecast_dataset["WeekDay"] = forecast_dataset.Data.dt.weekday
	forecast_dataset["Holiday"] = 0
	for holiday in forecast_dataset["Data"].unique():
			if holiday in holidays.ds.values:
					forecast_dataset["Holiday"][forecast_dataset["Data"] == holiday] = 1

	# Restructuring the dataset
	forecast_dataset = forecast_dataset[["WeekDay", "Month", "Holiday", "Interval", "Temperatura"]]
	# Loading the model
	xgb_loaded = joblib.load("./Solina/Consumption/XGB_Consumption_Temperature.pkl")
	preds = xgb_loaded.predict(forecast_dataset.values)
	#Exporting Results to Excel
	workbook = xlsxwriter.Workbook("./Solina/Consumption/Results_Consumption.xlsx")
	worksheet = workbook.add_worksheet("Prediction_Consumption")

	row = 1
	col = 0
	worksheet.write(0,0,"Prediction")
	# worksheet.write(0,1,"Real")

	for value in preds:
			worksheet.write(row, col, value)
			row +=1
	# row = 1
	# for value in y_test:
	#     worksheet.write(row, col + 1, value)
	#     row +=1

	workbook.close()

def render_consumption_forecast():
	st.write("Consumption Forecast Section")
	# ... (other content and functionality for consumption forecasting)
	uploaded_files_consumption = st.file_uploader("Choose a file", type=["text/csv", "xlsx"], accept_multiple_files=True)

	if uploaded_files_consumption is not None:
		for uploaded_file in uploaded_files_consumption:
			if uploaded_file.type == "text/csv":
				df = pd.read_csv(uploaded_file)
			elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
				try:
					df = pd.read_excel(uploaded_file, sheet_name="Forecast_dataset")
				except ValueError:
					st.error("Expected sheet name 'Forecast_dataset' not found in Excel file.")
					continue
			else:
				st.error("Unsupported file format. Please upload a CSV or XLSX file.")
				continue
			st.dataframe(df)

			# Submit button
			if st.button('Submit'):
				# Replace this line with the code to generate and display the forecast
				st.success('Forecast Ready', icon="✅")
				predicting_exporting_Consumption_Solina(df)
				# Assume the forecast data is already written to forecast_results.xlsx
				file_path = './Solina/Consumption/Results_Consumption.xlsx'

				with open(file_path, "rb") as f:
					excel_data = f.read()

				# Create a download link
				b64 = base64.b64encode(excel_data).decode()
				button_html = f"""
					 <a download="Consumption_Forecast.xlsx" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download>
					 <button kind="secondary" data-testid="baseButton-secondary" class="st-emotion-cache-12tniow ef3psqc12">Download Forecast Results</button>
					 </a> 
					 """
				st.markdown(button_html, unsafe_allow_html=True)

def render_production_forecast():
	st.write("Production Forecast Section")
	# ... (other content and functionality for production forecasting)
	uploaded_files = st.file_uploader("Choose a file", type=["text/csv", "xlsx"], accept_multiple_files=True)

	if uploaded_files is not None:
		for uploaded_file in uploaded_files:
			if uploaded_file.type == "text/csv":
				df = pd.read_csv(uploaded_file)
			elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
				try:
					df = pd.read_excel(uploaded_file, sheet_name="Forecast_Dataset")
				except ValueError:
					st.error("Expected sheet name 'Forecast_Dataset' not found in Excel file.")
					continue
			else:
				st.error("Unsupported file format. Please upload a CSV or XLSX file.")
				continue
			st.dataframe(df)

			# Submit button
			if st.button('Submit'):
				st.success('Forecast Ready', icon="✅")
				# Your code to generate the forecast
				predicting_exporting(df)
				file_path = './Solina/Production/Results_Production_xgb.xlsx'

				with open(file_path, "rb") as f:
					excel_data = f.read()

				# Create a download link
				b64 = base64.b64encode(excel_data).decode()
				button_html = f"""
					 <a download="Production_Forecast.xlsx" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download>
					 <button kind="secondary" data-testid="baseButton-secondary" class="st-emotion-cache-12tniow ef3psqc12">Download Forecast Results</button>
					 </a> 
					 """
				st.markdown(button_html, unsafe_allow_html=True)

def render_forecast_page():
	
	# Web App Title
	st.markdown('''
	# **The Forecast Section**

	''')

	# Allow the user to choose between Consumption and Production
	forecast_type = st.radio("Choose Forecast Type:", options=["Consumption", "Production"])

	if forecast_type == "Consumption":
			render_consumption_forecast()
	elif forecast_type == "Production":
			render_production_forecast()