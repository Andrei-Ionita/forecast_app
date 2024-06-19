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




#=====================================================================BALANGING MARKET INTRADAY===================================================================================================

def render_balancing_market_intraday_page():
	
	# Web App Title
	st.header("Balancing Market :blue[Intraday Dashboard]")
