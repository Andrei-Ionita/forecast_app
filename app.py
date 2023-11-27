import streamlit as st
import streamlit.components.v1 as stc
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import xlsxwriter


# Importing apps
from eda import render_eda_page
from ml import render_forecast_page, render_balancing_market_page

# Define rendering functions before the main function.
slideshow_html = """
<style>
* {box-sizing: border-box}
body {font-family: Verdana, sans-serif; margin:0}
.mySlides {display: none}
img {vertical-align: middle; max-height: 700px; width: auto; max-width: 100%;}

/* Slideshow container */
.slideshow-container {
	max-width: 100%;
	height: 700px;
	position: relative;
	margin: auto;
}

/* Next & previous buttons */
.prev, .next {
	cursor: pointer;
	position: absolute;
	top: 50%;
	width: auto;
	padding: 16px;
	margin-top: -22px;
	color: white;
	font-weight: bold;
	font-size: 18px;
	transition: 0.6s ease;
	border-radius: 0 3px 3px 0;
	user-select: none;
}

/* Position the "next button" to the right */
.next {
	right: 0;
	border-radius: 3px 0 0 3px;
}

/* On hover, add a black background color with a little bit see-through */
.prev:hover, .next:hover {
	background-color: rgba(0,0,0,0.8);
}

/* Caption text */
.text {
	color: #f2f2f2;
	font-size: 15px;
	padding: 8px 12px;
	position: absolute;
	bottom: 8px;
	width: 100%;
	text-align: center;
}

/* Number text (1/3 etc) */
.numbertext {
	color: #f2f2f2;
	font-size: 12px;
	padding: 8px 12px;
	position: absolute;
	top: 0;
}

/* The dots/bullets/indicators */
.dot {
	cursor: pointer;
	height: 15px;
	width: 15px;
	margin: 0 2px;
	background-color: #bbb;
	border-radius: 50%;
	display: inline-block;
	transition: background-color 0.6s ease;
}

.active, .dot:hover {
	background-color: #717171;
}

/* Fading animation */
.fade {
	animation-name: fade;
	animation-duration: 1.5s;
}

@keyframes fade {
	from {opacity: .4} 
	to {opacity: 1}
}

/* On smaller screens, decrease text size */
@media only screen and (max-width: 300px) {
	.prev, .next,.text {font-size: 11px}
}
</style>

<body>

<div class="slideshow-container">

<div class="mySlides fade">
	<img src="https://drive.google.com/uc?export=view&id=1JlJjOEuenPbYiQBuqo2wFH6EcLQkFqW0">
</div>

<div class="mySlides fade">
	<img src="https://drive.google.com/uc?export=view&id=1ayrXoiHly0bLYGtSZ2MLX7ije097vJcO">
</div>

<div class="mySlides fade">
	<img src="https://drive.google.com/uc?export=view&id=1DgOto2L2UAxevzy0tLvTribS8vGMzp8U">
</div>

<div class="mySlides fade">
	<img src="https://drive.google.com/uc?export=view&id=1_bSenEsBxF_YauUxr7RTxpfwjKwchZM2">
</div>

<div class="mySlides fade">
	<img src="https://drive.google.com/uc?export=view&id=1K56emhtwnfhTcty4L6DkZS7vadfdavEE">
</div>

</div>
<br>

<div style="text-align:center">
	<span class="dot" onclick="currentSlide(1)"></span> 
	<span class="dot" onclick="currentSlide(2)"></span> 
	<span class="dot" onclick="currentSlide(3)"></span> 
</div>

<script>
let slideIndex = 0;
showSlides();

function plusSlides(n) {
	slideIndex += n;
	if (slideIndex > slides.length - 1) slideIndex = 0;
	if (slideIndex < 0) slideIndex = slides.length - 1;
	showSlide();
}

function currentSlide(n) {
	slideIndex = n;
	showSlide();
}

function showSlides() {
	let i;
	let slides = document.getElementsByClassName("mySlides");
	let dots = document.getElementsByClassName("dot");
	for (i = 0; i < slides.length; i++) {
		slides[i].style.display = "none";  
	}
	slideIndex++;
	if (slideIndex > slides.length) {slideIndex = 1}    
	for (i = 0; i < dots.length; i++) {
		dots[i].className = dots[i].className.replace(" active", "");
	}
	slides[slideIndex-1].style.display = "block";  
	dots[slideIndex-1].className += " active";
	setTimeout(showSlides, 10000); // Change image every 10 seconds
}

function showSlide() {
	let i;
	let slides = document.getElementsByClassName("mySlides");
	let dots = document.getElementsByClassName("dot");
	for (i = 0; i < slides.length; i++) {
		slides[i].style.display = "none";  
	}
	slides[slideIndex].style.display = "block";  
	dots[slideIndex].className += " active";
}
</script>
</body>
"""

custom_styles = """
<style>
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
		body {
				font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
				background-color: #f4f4f4;
		}
</style>
"""

def render_home_page():

	st.title("nextE@AI Forecasting")
	st.subheader("Forecast and analyze renewable energy production and consumption")
	stc.html(slideshow_html, height=700)
	st.markdown("""
	<style>
			.divider {
					border-bottom: 1px solid rgba(203, 228, 222, 0.2); /* Change color here */
					margin: 20px 0; /* Adjust margin to suit */
			}
	</style>
	<div class="divider"></div>
	""", unsafe_allow_html=True)
	st.markdown(custom_styles, unsafe_allow_html=True)
	st.write("Use the navigation menu to access forecasting and EDA tools.")
	st.markdown("""
	<style>
			.divider {
					border-bottom: 1px solid rgba(203, 228, 222, 0.2); /* Change color here */
					margin: 20px 0; /* Adjust margin to suit */
			}
	</style>
	<div class="divider"></div>
	""", unsafe_allow_html=True)

def main():

	st.sidebar.title("Navigation")

	# Initialize page in session state if not already initialized
	if "page" not in st.session_state:
		st.session_state['page'] = "Home"

	# Determine the index for the default value of the sidebar radio
	# default_index = 0 if st.session_state['page'] == "Home" else ["Forecast", "EDA"].index(st.session_state['page'])

	# Use session state to set default value for sidebar radio
	page = st.sidebar.radio(
			"Select a page:",
			options=["Home", "Forecast", "EDA", "Balancing Market"],
			index=None,
			key="page_select"
	)

	if page==None:
		render_home_page()
		st.session_state['page'] = "Home"

	# Update session state with new page selection
	st.session_state['page'] = page

	# Render the appropriate page based on session state
	if st.session_state['page'] == "Home":
		render_home_page()
	elif st.session_state['page'] == "Forecast":
		render_forecast_page()
	elif st.session_state['page'] == "EDA":
		render_eda_page()

if __name__ == "__main__":
		main()