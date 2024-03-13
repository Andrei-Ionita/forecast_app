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
import zipfile
from datetime import datetime
import gdown
import requests

session_start_time = time.time()

# Creating the holidays dataframe
# Creating the dictionary of holidays
New_year_and_day_after = pd.DataFrame({"holiday": "Anul Nou & A doua zi",
														"ds": pd.to_datetime(["2017-01-01", "2017-01-02", "2016-01-01", "2016-01-02", "2015-01-01", "2015-01-02", "2014-01-01", "2014-01-02", "2019-01-01",
																									"2019-01-02", "2018-01-01", "2018-01-02", "2020-01-01", "2020-01-02", "2021-01-01", "2021-01-02",
																									"2022-01-01", "2022-01-02", "2023-01-01", "2023-01-02","2024-01-01", "2024-01-02"]),
														"lower_window": -1,
														"upper_window": 1})	

National_holiday = pd.DataFrame({"holiday": "Ziua Nationala",
																 "ds": pd.to_datetime(["2016-12-01", "2015-12-01", "2014-12-01", "2018-12-01", "2019-12-01", "2020-12-01", "2021-12-01", "2022-12-01", "2023-12-01", "2024-12-01"]),
																 "lower_window": 0,
																 "upper_window": 1})
Ziua_Principatelor = pd.DataFrame({"holiday": "Ziua Principatelor",
																 "ds": pd.to_datetime(["2017-01-24", "2016-01-24", "2018-01-24", "2019-01-24", "2020-01-24", "2021-01-24", "2022-01-24", "2023-01-24", "2024-01-24"]),
																 "lower_window": 0,
																 "upper_window": 1})
Christmas = pd.DataFrame({"holiday": "Craciunul",
													"ds": pd.to_datetime(["2017-12-25", "2017-12-26", "2016-12-25", "2016-12-26", "2015-12-25", "2015-12-26", "2014-12-25", "2014-12-26", "2018-12-25", "2018-12-26", "2019-12-25", "2019-12-26", "2020-12-25", "2020-12-26", "2021-12-25", "2021-12-26",
																								"2022-12-25", "2022-12-26", "2023-12-25", "2023-12-26", "2024-12-25", "2024-12-26"]),
													"lower_window": -1,
													"upper_window": 1})
St_Andrew = pd.DataFrame({"holiday": "Sfantul Andrei",
													"ds": pd.to_datetime(["2017-11-30", "2016-11-30", "2015-11-30", "2014-11-30", "2018-11-30", "2019-11-30", "2020-11-30", "2021-11-30", "2022-11-30",
																								"2023-11-30", "2024-11-30"]),
													"lower_window": -1,
													"upper_window": 0})
Adormirea_Maicii_Domnului = pd.DataFrame({"holiday": "Adormirea Maicii Domnului",
																					"ds": pd.to_datetime(["2017-08-15", "2016-08-15", "2015-08-15", "2014-08-15", "2018-08-15", "2019-08-15", "2020-08-15", "2021-08-15","2022-08-15", "2024-08-15"])})
Rusalii = pd.DataFrame({"holiday": "Rusalii",
												"ds": pd.to_datetime(["2017-06-04", "2017-06-05", "2016-06-19", "2016-06-20", "2015-05-31", "2015-06-01", "2014-06-08", "2014-06-09", "2018-05-27", "2018-05-28", "2019-06-16", "2019-06-17", "2020-06-07", "2020-06-08", "2021-06-20", "2021-06-21",
																							"2022-06-12", "2022-06-13", "2023-06-04", "2023-06-05", "2024-06-24"])})
Ziua_Copilului = pd.DataFrame({"holiday": "Ziua Copilului",
															"ds": pd.to_datetime(["2017-06-01", "2018-06-01", "2019-06-01", "2020-06-01", "2021-06-01", "2022-06-01", "2023-06-01", "2024-06-01"])})
Ziua_Muncii = pd.DataFrame({"holiday": "Ziua Muncii",
														"ds": pd.to_datetime(["2017-05-01", "2016-05-01", "2015-05-01", "2014-05-01", "2018-05-01", "2019-05-01", "2020-05-01", "2021-05-01", "2022-05-01", "2023-05-01",
															"2024-05-01"])})
Pastele = pd.DataFrame({"holiday": "Pastele",
												"ds": pd.to_datetime(["2017-04-16", "2017-04-17", "2016-05-01", "2016-05-02", "2015-04-12", "2015-04-13", "2014-04-20", "2014-04-21", "2018-04-08", "2018-04-09", "2019-04-28", "2019-04-29", "2020-04-19", "2020-04-20", "2021-05-02", "2021-05-03",
																							"2022-04-24", "2022-04-25", "2023-04-16", "2023-04-17", "2024-05-06"]),
												"lower_window": -1,
												"upper_window": 1})
Vinerea_Mare = pd.DataFrame({"holiday": "Vinerea Mare",
														 "ds": pd.to_datetime(["2020-04-17", "2019-04-26", "2018-04-06", "2021-04-30", "2022-04-30", "2023-04-30", "2024-05-03"])})
Ziua_Unirii = pd.DataFrame({"holiday": "Ziua Unirii",
														"ds": pd.to_datetime(["2015-01-24", "2020-01-24", "2019-01-24", "2021-01-24", "2022-01-24", "2023-01-24", "2024-01-24"])})
Public_Holiday = pd.DataFrame({"holiday": "Public Holiday",
															"ds": pd.to_datetime(["2019-04-30"])})
holidays = pd.concat((New_year_and_day_after, National_holiday, Christmas, St_Andrew, Ziua_Principatelor, Adormirea_Maicii_Domnului, Rusalii, Ziua_Copilului, Ziua_Muncii,
											Pastele, Vinerea_Mare, Ziua_Unirii, Public_Holiday))

#=============================================================================Feetching the data for Transavia locations========================================================================
solcast_api_key = os.getenv("solcast_api_key")
# output_path = "./Transavia/data/Bocsa.csv"

# Defining the fetching data function
def fetch_data(lat, lon, api_key, output_path):
	# Fetch data from the API
	api_url = "https://api.solcast.com.au/data/forecast/radiation_and_weather?latitude={}&longitude={}&hours=336&output_parameters=ghi,air_temp,cloud_opacity&period=PT60M&format=csv&api_key={}".format(lat, lon, solcast_api_key)
	response = requests.get(api_url)
	print("Fetching data...")
	if response.status_code == 200:
		# Write the content to a CSV file
		with open(output_path, 'wb') as file:
			file.write(response.content)
	else:
		raise Exception(f"Failed to fetch data: Status code {response.status_code}")

# ============================Crating the Input_production file==========
def creating_input_production_file(path):
	santimbru_data = pd.read_csv(f"{path}/Santimbru.csv")
	input_production = pd.read_excel("./Transavia/Production/Input_production.xlsx")
	input_production = input_production.copy()

	# Convert 'period_end' in santimbru to datetime
	santimbru_data['period_end'] = pd.to_datetime(santimbru_data['period_end'], errors='coerce')
	# Extract just the date part in the desired format (as strings)
	santimbru_dates = santimbru_data['period_end'].dt.strftime('%Y-%m-%d')

	# Write the dates from santimbru_dates to input_production.Data
	input_production['Data'] = santimbru_dates.values
	# Fill NaNs in the 'Data' column with next valid observation
	input_production['Data'].fillna(method='bfill', inplace=True)

	# Completing the Interval column
	santimbru_intervals = santimbru_data["period_end"].dt.hour
	input_production["Interval"] = santimbru_intervals
	# Replace NaNs in the 'Interval' column with 0
	input_production['Interval'].fillna(0, inplace=True)

	# Completing the Radiatie column
	santimbru_radiatie = santimbru_data["ghi"]
	input_production["Radiatie"] = santimbru_radiatie

	# Completing the Temperatura column
	santimbru_temperatura = santimbru_data["air_temp"]
	input_production["Temperatura"] = santimbru_temperatura

	# Completing the Nori column
	santimbru_nori = santimbru_data["cloud_opacity"]
	input_production["Nori"] = santimbru_nori

	# Completing the Centrala column
	input_production["Centrala"] = "Abator_Oiejdea"

	# Copying the data for FNC PVPP
	copy_df = input_production.copy()
	copy_df['Centrala'] = "FNC"

	# Append the copied dataframe to the original dataframe
	input_production = pd.concat([input_production, copy_df])

	# Copying the data for F4 PVPP
	copy_df = input_production[input_production["Centrala"] == "Abator_Oiejdea"].copy()
	copy_df['Centrala'] = "F4"

	# Append the copied dataframe to the original dataframe
	input_production = pd.concat([input_production, copy_df])

	# Copying the data for Ciugud PVPP
	copy_df = input_production[input_production["Centrala"] == "Abator_Oiejdea"].copy()
	copy_df['Centrala'] = "Ciugud"

	# Append the copied dataframe to the original dataframe
	input_production = pd.concat([input_production, copy_df])

	# Copying the data for Abator Bocsa PVPP
	copy_df = input_production[input_production["Centrala"] == "Abator_Oiejdea"].copy()
	copy_df['Centrala'] = "Abator_Bocsa"
	# Append the copied dataframe to the original dataframe
	input_production = pd.concat([input_production, copy_df])

	bocsa_data = pd.read_csv(f"{path}/Bocsa.csv")

	# Completing the Radiatie column for Abator Bocsa
	bocsa_radiatie = bocsa_data["ghi"]
	input_production["Radiatie"][input_production["Centrala"] == "Abator_Bocsa"] = bocsa_radiatie

	# Completing the Temperatura column for Abator Bocsa
	bocsa_temperatura = bocsa_data["air_temp"]
	input_production["Temperatura"][input_production["Centrala"] == "Abator_Bocsa"] = bocsa_temperatura

	# Completing the Nori column for Abator Bocsa
	bocsa_nori = bocsa_data["cloud_opacity"]
	input_production["Nori"][input_production["Centrala"] == "Abator_Bocsa"] = bocsa_nori

	# Copying the data for Lunca PVPP
	copy_df = input_production[input_production["Centrala"] == "Abator_Oiejdea"].copy()
	copy_df['Centrala'] = "F24"
	# Append the copied dataframe to the original dataframe
	input_production = pd.concat([input_production, copy_df])

	lunca_data = pd.read_csv(f"{path}/Lunca.csv")

	# Completing the Radiatie column for F24
	lunca_radiatie = lunca_data["ghi"]
	input_production["Radiatie"][input_production["Centrala"] == "F24"] = lunca_radiatie

	# Completing the Temperatura column for F24
	lunca_temperatura = lunca_data["air_temp"]
	input_production["Temperatura"][input_production["Centrala"] == "F24"] = lunca_temperatura

	# Completing the Nori column for F24
	lunca_nori = lunca_data["cloud_opacity"]
	input_production["Nori"][input_production["Centrala"] == "F24"] = lunca_nori

	# Copying the data for Brasov PVPP
	copy_df = input_production[input_production["Centrala"] == "Abator_Oiejdea"].copy()
	copy_df['Centrala'] = "Brasov"
	# Append the copied dataframe to the original dataframe
	input_production = pd.concat([input_production, copy_df])

	brasov_data = pd.read_csv(f"{path}/Brasov.csv")

	# Completing the Radiatie column for Brasov
	brasov_radiatie = brasov_data["ghi"]
	input_production["Radiatie"][input_production["Centrala"] == "Brasov"] = brasov_radiatie

	# Completing the Temperatura column for Brasov
	brasov_temperatura = brasov_data["air_temp"]
	input_production["Temperatura"][input_production["Centrala"] == "Brasov"] = brasov_temperatura

	# Completing the Nori column for Brasov
	brasov_nori = brasov_data["cloud_opacity"]
	input_production["Nori"][input_production["Centrala"] == "Brasov"] = brasov_nori

	# Saving input_production to Excel
	input_production.to_excel("./Transavia/Production/Input_production_filled.xlsx", index=False)

# ===================================================================================TRANSAVIA FORECAST==================================================================================================================
def predicting_exporting_Transavia(dataset):
	datasets_forecast = dataset.copy()
	CEFs = datasets_forecast.Centrala.unique()
	dataset_forecast = {elem : pd.DataFrame for elem in CEFs}
	for CEF in CEFs:
		print("Predicting for {}".format(CEF))
		xgb_loaded = joblib.load("./Transavia/Production/Models/rs_xgb_{}.pkl".format(CEF))
		dataset_forecast = datasets_forecast[:][datasets_forecast.Centrala == CEF]
		dataset_forecast["Data"] = pd.to_datetime(dataset_forecast["Data"])
		dataset_forecast["Month"] = dataset_forecast.Data.dt.month
		if CEF in ["F24"]:
			df_forecast = dataset_forecast.drop(["Data", "Nori", "Centrala"], axis=1)
		else:
			df_forecast = dataset_forecast.drop(["Data", "Centrala"], axis=1)
		preds = xgb_loaded.predict(df_forecast.values)
		# Exporting Results to Excel
		workbook = xlsxwriter.Workbook("./Transavia/Production/Results/Results_daily_{}.xlsx".format(CEF))
		worksheet = workbook.add_worksheet("Prediction_Production")

		worksheet.write(0,0,"Data")
		worksheet.write(0,1,"Interval")
		worksheet.write(0,2,"Production")
		date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
		row = 1
		col = 0
		for value in preds:
		  worksheet.write(row, col+2, value)
		  row +=1
		row = row - len(preds)
		for data in dataset_forecast["Data"]:
		  worksheet.write(row, col, data, date_format)
		  row +=1
		row = row - len(dataset_forecast["Data"])
		for value in dataset_forecast["Interval"]:
		  worksheet.write(row, col+1, value)
		  row +=1
		workbook.close()

def predicting_exporting_consumption_Santimbru(dataset):
	# Importing the dataset
	dataset_forecast = dataset
	IBDs = dataset_forecast.IBD.unique()
	IBDs_PVPP = ["Abator", "Abator_Bocsa", "Ciugud", "F5", "Ferma_Bocsa", "FNC", "F4"]
	datasets_forecast = {elem : pd.DataFrame for elem in IBDs}
	for IBD in IBDs:
		datasets_forecast[IBD] = dataset_forecast[:][dataset_forecast.IBD == IBD]
		datasets_forecast[IBD]["WeekDay"] = datasets_forecast[IBD].Data.dt.weekday
		datasets_forecast[IBD]["Month"] = datasets_forecast[IBD].Data.dt.month
		datasets_forecast[IBD]["Holiday"] = 0
		for holiday in datasets_forecast[IBD]["Data"].unique():
			if holiday in holidays.ds.values:
				datasets_forecast[IBD]["Holiday"][datasets_forecast[IBD]["Data"] == holiday] = 1
		if len(datasets_forecast[IBD]["Flow_Chicks"].value_counts()) > 0 and len(datasets_forecast[IBD]["Radiatie"].value_counts()) > 0:
			## Restructuring the dataset
			datasets_forecast[IBD] = datasets_forecast[IBD][["Month", "WeekDay","Holiday", "Interval", "Temperatura", "Flow_Chicks", "Radiatie"]]
		elif len(datasets_forecast[IBD]["Flow_Chicks"].value_counts()) > 0:
			datasets_forecast[IBD] = datasets_forecast[IBD][["Month", "WeekDay","Holiday", "Interval", "Temperatura", "Flow_Chicks"]]
		elif len(datasets_forecast[IBD]["Radiatie"].value_counts()) > 0:
			datasets_forecast[IBD] = datasets_forecast[IBD][["Month", "WeekDay","Holiday", "Interval", "Temperatura", "Radiatie"]]
		else:
		  datasets_forecast[IBD] = datasets_forecast[IBD][["Month", "WeekDay","Holiday", "Interval", "Temperatura"]]
	# datasets_forecast[IBD].replace([np.inf, -np.inf], np.nan)
	# datasets_forecast[IBD].dropna(inplace = True)
		# Check if the cons place has PVPP and add the column, if it does
		if IBD in IBDs_PVPP:
			datasets_forecast[IBD]["PVPP"] = 1
	# Predicting
	predictions = {}
	for IBD in datasets_forecast.keys():
		if IBD in IBDs_PVPP:
		  xgb_loaded = joblib.load("./Transavia/Consumption/Models_PVPP/rs_xgb_{}.pkl".format(IBD))
		  print("Predicting for {}".format(IBD))
		  # print(datasets_forecast[IBD])
		  xgb_preds = xgb_loaded.predict(datasets_forecast[IBD].drop("PVPP", axis=1).values)
		  predictions[IBD] = xgb_preds
		  predictions["Data"] = dataset_forecast["Data"]
		  predictions["Interval"] = dataset_forecast["Interval"]
		else:
			xgb_loaded = joblib.load("./Transavia/Consumption/Models_PVPP/rs_xgb_{}.pkl".format(IBD))
			print("Predicting for {}".format(IBD))
			# print(datasets_forecast[IBD])
			xgb_preds = xgb_loaded.predict(datasets_forecast[IBD].values)
			predictions[IBD] = xgb_preds
			predictions["Data"] = dataset_forecast["Data"]
			predictions["Interval"] = dataset_forecast["Interval"]
	# Predicting with PVPP models
	predictions_PVPP = {}
	for IBD in datasets_forecast.keys():
		if IBD in IBDs_PVPP:
			if os.path.isfile("./Transavia/Consumption/Models_PVPP/rs_xgb_{}_PVPP.pkl".format(IBD)):
				xgb_loaded = joblib.load("./Transavia/Consumption/Models_PVPP/rs_xgb_{}_PVPP.pkl".format(IBD))
				print("Predicting for {}".format(IBD))
				# print(datasets_forecast[IBD])
				xgb_preds = xgb_loaded.predict(datasets_forecast[IBD].drop("Radiatie", axis=1).values)
				predictions_PVPP[IBD] = xgb_preds
				predictions_PVPP["Data"] = dataset_forecast["Data"]
				predictions_PVPP["Interval"] = dataset_forecast["Interval"]
	# Exporting Results to Excel
	workbook = xlsxwriter.Workbook("./Transavia/Consumption/Results/XGB/Results_IBDs_daily.xlsx")
	worksheet = workbook.add_worksheet("Prediction_Consumption")

	worksheet.write(0,0,"Data")
	worksheet.write(0,1,"Interval")
	worksheet.write(0,2,"Prediction")
	worksheet.write(0,3,"IBD")
	worksheet.write(0,4,"Lookup")
	worksheet.write(0,5,"PVPP_Model_Prediction")
	date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
	row = 1
	col = 0
	for IBD in datasets_forecast.keys():
		if IBD in predictions_PVPP.keys():
			for value in predictions[IBD]:
				worksheet.write(row, col+2, value)
				worksheet.write(row, col+3, IBD)
				row +=1
			row = row-len(predictions[IBD])
			for value in predictions_PVPP[IBD]:
				worksheet.write(row, col+5, value)
				row +=1
		else:
			for value in predictions[IBD]:
				worksheet.write(row, col+2, value)
				worksheet.write(row, col+3, IBD)
				row +=1
	row = row - len(predictions[IBD])*len(datasets_forecast.keys())
	for data in predictions["Data"]:
		worksheet.write(row, col, datetime.date(data),date_format)
		worksheet.write_formula(row, col+4, "=A"+ str(row+1)+ "&" + "B"+ str(row+1)+ "&" + "D" + str(row+1))
		row +=1
	row = row - len(predictions["Data"])
	for interval in predictions["Interval"]:
		worksheet.write(row, col+1, interval)
		row +=1
	# row = 1
	# for value in y_test:
	#     worksheet.write(row, col + 1, value)
	#     row +=1
	workbook.close()

def predicting_exporting_consumption_Brasov(dataset):
	# Importing the dataset
	dataset_forecast = dataset
	PODs = dataset_forecast.POD.unique()
	datasets_forecast = {elem : pd.DataFrame for elem in PODs}
	for POD in PODs:
		datasets_forecast[POD] = dataset_forecast[:][dataset_forecast.POD == POD]
		datasets_forecast[POD]["WeekDay"] = datasets_forecast[POD].Data.dt.weekday
		datasets_forecast[POD]["Month"] = datasets_forecast[POD].Data.dt.month
		datasets_forecast[POD]["Holiday"] = 0
		for holiday in datasets_forecast[POD]["Data"].unique():
		  if holiday in holidays.ds.values:
			  datasets_forecast[POD]["Holiday"][datasets_forecast[POD]["Data"] == holiday] = 1
		if len(datasets_forecast[POD]["Flow_Chicks"].value_counts()) > 0 and len(datasets_forecast[POD]["PVPP"].value_counts()) > 0:
			datasets_forecast[POD] = datasets_forecast[POD][["Month", "WeekDay","Holiday", "Interval", "Temperatura", "Flow_Chicks", "PVPP"]]
		elif len(datasets_forecast[POD]["Flow_Chicks"].value_counts()) > 0:
			datasets_forecast[POD] = datasets_forecast[POD][["Month", "WeekDay","Holiday", "Interval", "Temperatura", "Flow_Chicks"]]
		elif len(datasets_forecast[POD]["PVPP"].value_counts()) > 0:
			datasets_forecast[POD] = datasets_forecast[POD][["Month", "WeekDay","Holiday", "Interval", "Temperatura", "PVPP"]]
		else:
			datasets_forecast[POD] = datasets_forecast[POD][["Month", "WeekDay","Holiday", "Interval", "Temperatura"]]
		# datasets_forecast[POD].replace([np.inf, -np.inf], np.nan)
		# datasets_forecast[POD].dropna(inplace = True)
	# Predicting noPVPP
	predictions = {}
	for POD in datasets_forecast.keys():
		if "PVPP" in datasets_forecast[POD].columns:
		  xgb_loaded = joblib.load("./Transavia/Consumption/Models_PVPP/Brasov_Models/rs_xgb_{}.pkl".format(POD))
		  print("Predicting for {}".format(POD))
		  # print(datasets_forecast[POD])
		  xgb_preds = xgb_loaded.predict(datasets_forecast[POD].values)
		  predictions[POD] = xgb_preds
		  predictions["Data"] = dataset_forecast["Data"]
		  predictions["Interval"] = dataset_forecast["Interval"]
		else:
		  xgb_loaded = joblib.load("./Transavia/Consumption/Models_PVPP/Brasov_Models/rs_xgb_{}.pkl".format(POD))
		  print("Predicting for {}".format(POD))
		  # print(datasets_forecast[POD])
		  xgb_preds = xgb_loaded.predict(datasets_forecast[POD].values)
		  predictions[POD] = xgb_preds
		  predictions["Data"] = dataset_forecast["Data"]
		  predictions["Interval"] = dataset_forecast["Interval"]
	# Predicting with PVPP
	predictions_PVPP = {}
	for POD in datasets_forecast.keys():
		if os.path.isfile(".Transavia/Consumption/Brasov_Models/rs_xgb_{}_PVPP.pkl".format(POD)):
		  xgb_loaded = joblib.load("./Transavia/Consumption/Brasov_Models/rs_xgb_{}_PVPP.pkl".format(POD))
		  print("Predicting for {}".format(POD))
		  # print(datasets_forecast[POD])
		  xgb_preds = xgb_loaded.predict(datasets_forecast[POD].values)
		  predictions_PVPP[POD] = xgb_preds
		  predictions_PVPP["Data"] = dataset_forecast["Data"]
		  predictions_PVPP["Interval"] = dataset_forecast["Interval"]
	# Exporting Results to Excel
	workbook = xlsxwriter.Workbook("./Transavia/Consumption/Results/XGB/Results_IBDs_daily_Brasov.xlsx")
	worksheet = workbook.add_worksheet("Prediction_Consumption")

	worksheet.write(0,0,"Data")
	worksheet.write(0,1,"Interval")
	worksheet.write(0,2,"Prediction")
	worksheet.write(0,3,"POD")
	worksheet.write(0,4,"Lookup")
	worksheet.write(0,5,"Prediction_PVPP")
	date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
	row = 1
	col = 0
	for POD in datasets_forecast.keys():
		if POD in predictions_PVPP.keys():
			for value in predictions[POD]:
				worksheet.write(row, col+2, abs(value))
				worksheet.write(row, col+3, str(POD))
				row +=1
			row = row - len(predictions[POD])
			for value in predictions_PVPP[POD]:
				worksheet.write(row, col+5, abs(value))
				row +=1
		else:
			for value in predictions[POD]:
				worksheet.write(row, col+2, abs(value))
				worksheet.write(row, col+3, str(POD))
				row +=1
	row = row - (len(predictions[POD]) * len(datasets_forecast.keys()))
	for data in predictions["Data"]:
		worksheet.write(row, col, datetime.date(data),date_format)
		worksheet.write_formula(row, col+4, "=A"+ str(row+1) + "&" + "B"+ str(row+1) + "&" +  "D" + str(row+1))
		row +=1
	row = row - len(predictions["Data"])
	for interval in predictions["Interval"]:
		worksheet.write(row, col+1, interval)
		row +=1
	# row = 1
	# for value in y_test:
	#     worksheet.write(row, col + 1, value)
	#     row +=1
	workbook.close()

def zip_files(folder_path, zip_name):
	zip_path = os.path.join(folder_path, zip_name)
	with zipfile.ZipFile(zip_path, 'w') as zipf:
		for root, _, files in os.walk(folder_path):
			for file in files:
				if file != zip_name:  # Avoid zipping the zip file itself
					file_path = os.path.join(root, file)
					arcname = os.path.relpath(file_path, folder_path)  # Relative path within the zip file
					zipf.write(file_path, arcname)

# Creating the dictionary for the Production PVPPs locations
locations_PVPPs = {"Lunca": {"lat": 46.427350, "lon": 23.905963}, "Brasov": {"lat": 45.642680, "lon": 25.588725},
                    "Santimbru": {"lat":46.135244 , "lon":23.644428 }, "Bocsa": {"lat":45.377012 , "lon":21.718752}}
def render_production_forecast_Transavia(locations_PVPPs):
	st.write("Production Forecast")
	# ... (other content and functionality for production forecasting)
	# Iterating through the dictionary of PVPP locations
	for location in locations_PVPPs.keys():
		print("Getting data for {}".format(location))
		output_path = f"./Transavia/data/{location}.csv"
		lat = locations_PVPPs[location]["lat"]
		lon = locations_PVPPs[location]["lon"]
		fetch_data(lat, lon, solcast_api_key, output_path)
	# Creating the input_production file
	path = "./Transavia/data"
	creating_input_production_file(path)
	df = pd.read_excel("./Transavia/Production/Input_production_filled.xlsx")
	# uploaded_files = st.file_uploader("Choose a file", type=["text/csv", "xlsx"], accept_multiple_files=True)

	# if uploaded_files is not None:
	# 	for uploaded_file in uploaded_files:
	# 		if uploaded_file.type == "text/csv":
	# 			df = pd.read_csv(uploaded_file)
	# 		elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
	# 			try:
	# 				df = pd.read_excel(uploaded_file)
	# 			except ValueError:
	# 				st.error("Expected sheet name 'Forecast_Dataset' not found in Excel file.")
	# 				continue
	# 		else:
	# 			st.error("Unsupported file format. Please upload a CSV or XLSX file.")
	# 			continue
	st.dataframe(df)
	# Submit button
	if st.button('Submit'):
		st.success('Forecast Ready', icon="✅")
		# Your code to generate the forecast
		predicting_exporting_Transavia(df)
		print("Forecast is on going...")
		# Creating the ZIP file with the Productions:
		folder_path = './Transavia/Production/Results'
		zip_name = 'Transavia_Production_Results.zip'
		zip_files(folder_path, zip_name)
		file_path = './Transavia/Production/Results/Transavia_Production_Results.zip'

		with open(file_path, "rb") as f:
			zip_data = f.read()

		# Create a download link
		b64 = base64.b64encode(zip_data).decode()
		button_html = f"""
			 <a download="Transavia_Production_Results.zip" href="data:application/zip;base64,{b64}" download>
			 <button kind="secondary" data-testid="baseButton-secondary" class="st-emotion-cache-12tniow ef3psqc12">Download Forecast Results</button>
			 </a> 
			 """
		st.markdown(button_html, unsafe_allow_html=True)

def render_consumption_forecast_Transavia():
	st.write("Consumption Forecast")
	# ... (other content and functionality for production forecasting)
	uploaded_files = st.file_uploader("Choose a file", type=["text/csv", "xlsx"], accept_multiple_files=True)

	if uploaded_files is not None:
		for uploaded_file in uploaded_files:
			if uploaded_file.type == "text/csv":
				df = pd.read_csv(uploaded_file)
			elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
				try:
					df = pd.read_excel(uploaded_file)
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
				if uploaded_file.name == "Input.xlsx":
					predicting_exporting_consumption_Santimbru(df)
				else:
					predicting_exporting_consumption_Brasov(df)
				# Creating the ZIP file with the Productions:
				folder_path = './Transavia/Consumption/Results/XGB'
				zip_name = 'Transavia_Consumption_Results.zip'
				zip_files(folder_path, zip_name)
				file_path = './Transavia/Consumption/Results/XGB/Transavia_Consumption_Results.zip'

				with open(file_path, "rb") as f:
					zip_data = f.read()

				# Create a download link
				b64 = base64.b64encode(zip_data).decode()
				button_html = f"""
					 <a download="Transavia_Consumption_Results.zip" href="data:application/zip;base64,{b64}" download>
					 <button kind="secondary" data-testid="baseButton-secondary" class="st-emotion-cache-12tniow ef3psqc12">Download Forecast Results</button>
					 </a> 
					 """
				st.markdown(button_html, unsafe_allow_html=True)

def render_Transavia_page():
	
	# Web App Title
	st.markdown('''
	## **The Transavia Forecast Section**

	''')

	# Allow the user to choose between Consumption and Production
	forecast_type = st.radio("Choose Forecast Type:", options=["Consumption", "Production"])

	if forecast_type == "Consumption":
		render_consumption_forecast_Transavia()
	elif forecast_type == "Production":
		render_production_forecast_Transavia(locations_PVPPs)

#================================================================================GENERAL FUNCTIONALITY==========================================================================================

def predicting_exporting_Solina(dataset):
	xgb_loaded = joblib.load("./Solina/Production/rs_xgb_Solina_prod.pkl")
	dataset_forecast = dataset.copy()
	dataset_forecast["Month"] = dataset_forecast.Data.dt.month

	dataset_forecast = dataset_forecast.drop("Data", axis=1)

	preds = xgb_loaded.predict(dataset_forecast.values)
	#Exporting Results to Excel
	workbook = xlsxwriter.Workbook("./Solina/Production/Results_Production_xgb.xlsx")
	worksheet = workbook.add_worksheet("Production_Predictions")
	date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
	# Define a format for cells with three decimal places
	decimal_format = workbook.add_format({'num_format': '0.000'})
	row = 1
	col = 0
	worksheet.write(0,0,"Data")
	worksheet.write(0,1,"Interval")
	worksheet.write(0,2,"Prediction")

	for value in preds:
			worksheet.write(row, col + 2, value, decimal_format)
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
	# Define a format for cells with three decimal places
	decimal_format = workbook.add_format({'num_format': '0.000'})

	row = 1
	col = 0
	worksheet.write(0,0,"Prediction")
	# worksheet.write(0,1,"Real")

	for value in preds:
			worksheet.write(row, col, value, decimal_format)
			row +=1
	# row = 1
	# for value in y_test:
	#     worksheet.write(row, col + 1, value)
	#     row +=1

	workbook.close()

def predicting_exporting_RAAL(dataset):
	xgb_loaded = joblib.load("./RAAL/Production/rs_xgb_RAAL_prod.pkl")
	dataset_forecast = dataset.copy()
	dataset_forecast["Month"] = dataset_forecast.Data.dt.month
	dataset_forecast.drop("Nori", axis=1, inplace=True)
	dataset_forecast = dataset_forecast.drop("Data", axis=1)

	preds = xgb_loaded.predict(dataset_forecast.values)
	#Exporting Results to Excel
	workbook = xlsxwriter.Workbook("./RAAL/Production/Results_Production_xgb_RAAL.xlsx")
	worksheet = workbook.add_worksheet("Production_Predictions")
	date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
	# Define a format for cells with three decimal places
	decimal_format = workbook.add_format({'num_format': '0.000'})
	row = 1
	col = 0
	worksheet.write(0,0,"Data")
	worksheet.write(0,1,"Interval")
	worksheet.write(0,2,"Prediction")

	for value in preds:
			worksheet.write(row, col + 2, value, decimal_format)
			row +=1
	row = 1
	for Data, Interval in zip(dataset.Data, dataset.Interval):
			worksheet.write(row, col + 0, Data, date_format)
			worksheet.write(row, col + 1, Interval)
			row +=1

	workbook.close()

def predicting_exporting_Consumption_RAAL(dataset):
	# Predict on forecast data
	forecast_dataset = dataset.copy()
	st.write(forecast_dataset)
	forecast_dataset["Month"] = forecast_dataset.Data.dt.month
	forecast_dataset["WeekDay"] = forecast_dataset.Data.dt.weekday
	forecast_dataset["Holiday"] = 0
	for holiday in forecast_dataset["Data"].unique():
		if holiday in holidays.ds.values:
			forecast_dataset["Holiday"][forecast_dataset["Data"] == holiday] = 1

	# Restructuring the dataset
	forecast_dataset = forecast_dataset[["WeekDay", "Month", "Holiday", "Interval", "Temperatura"]]
	# Loading the model
	xgb_loaded = joblib.load("./RAAL/Consumption/XGB_Consumption_RAAL.pkl")
	preds = xgb_loaded.predict(forecast_dataset.values)
	#Exporting Results to Excel
	workbook = xlsxwriter.Workbook("./RAAL/Consumption/Results_Consumption_RAAL.xlsx")
	worksheet = workbook.add_worksheet("Consumption_Predictions")
	date_format = workbook.add_format({'num_format':'dd.mm.yyyy'})
	# Define a format for cells with three decimal places
	decimal_format = workbook.add_format({'num_format': '0.000'})
	row = 1
	col = 0
	worksheet.write(0,0,"Data")
	worksheet.write(0,1,"Interval")
	worksheet.write(0,2,"Prediction")
	for value in preds:
		worksheet.write(row, col + 2, value, decimal_format)
		row +=1
	row = 1
	for Data, Interval in zip(dataset.Data, dataset.Interval):
		worksheet.write(row, col + 0, Data, date_format)
		worksheet.write(row, col + 1, Interval)
		row +=1

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
				if uploaded_file.name == "Input_consump_Solina.xlsx":
					predicting_exporting_Consumption_Solina(df)
					# Assume the forecast data is already written to forecast_results.xlsx
					file_path = './Solina/Consumption/Results_Consumption.xlsx'
				else:
					predicting_exporting_Consumption_RAAL(df)
					# Assume the forecast data is already written to forecast_results.xlsx
					file_path = './RAAL/Consumption/Results_Consumption_RAAL.xlsx'
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
				if uploaded_file.name == "Input.xlsx":
					predicting_exporting_Solina(df)
					file_path = './Solina/Production/Results_Production_xgb.xlsx'
				else:
					predicting_exporting_RAAL(df)
					file_path = './RAAL/Production/Results_Production_xgb_RAAL.xlsx'
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
	forecast_type = st.radio("Choose Forecast Type:", options=["Consumption", "Production", "Transavia"])

	if forecast_type == "Consumption":
		render_consumption_forecast()
	elif forecast_type == "Production":
		render_production_forecast()
	elif forecast_type == "Transavia":
		render_Transavia_page()

#======================================================BALANGING MARKET===================================================================================================

def render_balancing_market_page():
	
	# Web App Title
	st.markdown('''
	# **The Balancing Market Section**

	''')