import streamlit as st
from openai import OpenAI
import openai
import shelve
from dotenv import load_dotenv
import os
import time
import pandas as pd
from io import BytesIO

load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
client = OpenAI(api_key=OPEN_AI_API_KEY)

# --------------------------------------------------------------
# Upload file
# --------------------------------------------------------------
file_id_array = []
file_array = []
def upload_file(uploaded_file):
	for file in file_array:
		file = client.files.create(
			file = file,
			purpose = "assistants"
		)
		file_id_array.append(file.id)
# file = upload_file("./docs/IPOL_STU(2023)740094_EN.pdf")

# def file_exists(file_name):
# 	try:
# 		# Set initial parameters for pagination
# 		next_cursor = None
# 		while True:
# 			# Fetch a list of files, respecting pagination
# 			files_response = openai.File.list(cursor=next_cursor)
# 			for file in files_response.data:
# 				print(file)
# 				if file.filename == file_name:
# 					return True
# 			# Update the cursor for the next page, if any
# 			next_cursor = files_response.get('next_cursor')
# 			if not next_cursor:
# 				break
# 		return False
# 	except Exception as e:
# 		print(f"An error occurred: {e}")
# 		return False


# --------------------------------------------------------------
# Create assistant
# --------------------------------------------------------------
def create_assistant(file):
	"""
	You currently cannot set the temperature for Assistant via the API.
	"""
	assistant = client.beta.assistants.create(
		name="EnergyMarketsAssistant",
		instructions="You are an absolute Energy Markets guru and Power Trader. You provide detailed, accurate, and well-argued information about everything in the Energy field.",
		# tools=[{"type": "retrieval, code_interpreter"}],
		tools=[{"type": "code_interpreter"}],
		model="gpt-4-1106-preview"
		# file_ids=[file.id],
	)
	return assistant

# assistant = create_assistant(file)


# # --------------------------------------------------------------
# # Thread management
# # --------------------------------------------------------------
def check_if_thread_exists(user_id):
	with shelve.open("threads_db") as threads_shelf:
		return threads_shelf.get(user_id, None)


def store_thread(user_id, thread_id):
	with shelve.open("threads_db", writeback=True) as threads_shelf:
		threads_shelf[user_id] = thread_id


# # --------------------------------------------------------------
# # Generate response
# # --------------------------------------------------------------
def generate_response_files(message_body, user_id, name, file_id_array):
	try:
		# Ensure file_id_array does not exceed 10 items
		if len(file_id_array) > 10:
			print("Error: You can only include up to 10 file IDs per request.")
			# Optionally, split the array and handle in batches, or just use the first 10
			file_id_array = file_id_array[:10]  # Using only the first 10 items if more than 10

		# Check if there is already a thread_id for the user_id
		thread_id = check_if_thread_exists(user_id)

		# If a thread doesn't exist, create one and store it
		if thread_id is None:
			print(f"Creating new thread for {name} with user_id {user_id}")
			thread = client.beta.threads.create()
			store_thread(user_id, thread.id)
			thread_id = thread.id
		else:
			# Retrieving existing thread for the user
			print(f"Retrieving existing thread for {name} with user_id {user_id}")
			thread = client.beta.threads.retrieve(thread_id)

		# Add message to thread with file_ids, ensuring it doesn't exceed the limit
		message = client.beta.threads.messages.create(
			thread_id=thread_id,
			role="user",
			content=message_body,
			file_ids=file_id_array
		)

		# Run the assistant and get the new message
		new_message = run_assistant(thread)
		print(f"To {name}:", new_message)
		return new_message
	except Exception as e:
		print(f"An error occurred: {e}")


def generate_response(message_body, user_id, name):
	# Check if there is already a thread_id for the wa_id
	thread_id = check_if_thread_exists(user_id)

	# If a thread doesn't exist, create one and store it
	if thread_id is None:
		print(f"Creating new thread for {name} with user_id {user_id}")
		thread = client.beta.threads.create()
		store_thread(user_id, thread.id)
		thread_id = thread.id

	# Otherwise, retrieve the existing thread
	else:
		print(f"Retrieving existing thread for {name} with user_id {user_id}")
		thread = client.beta.threads.retrieve(thread_id)

	# Add message to thread
	message = client.beta.threads.messages.create(
		thread_id=thread_id,
		role="user",
		content=message_body
	)

	# Run the assistant and get the new message
	new_message = run_assistant(thread)
	print(f"To {name}:", new_message)
	return new_message

# # --------------------------------------------------------------
# # Run assistant
# # --------------------------------------------------------------
def run_assistant(thread):
	# Retrieve the Assistant
	# assistant = client.beta.assistants.retrieve(thread.id)

	# Run the assistant
	run = client.beta.threads.runs.create(
		thread_id=thread.id,
		assistant_id="asst_hLMuf98Ed8lA2RFIiuDE2uuG",
	)

	# Wait for completion
	while run.status != "completed":
		# Be nice to the API
		time.sleep(0.5)
		run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

	# Retrieve the Messages
	messages = client.beta.threads.messages.list(thread_id=thread.id)
	new_message = messages.data[0].content[0].text.value
	# print(f"Generated message: {new_message}")
	return new_message


# --------------------------------------------------------------
# Test assistant
# --------------------------------------------------------------

# new_message = generate_response("What's the check in time?", "123", "John")

# new_message = generate_response("What's the pin for the lockbox?", "456", "Sarah")

# new_message = generate_response("What was my previous question?", "123", "John")

# new_message = generate_response("What was my previous question?", "456", "Sarah")

def clear_input():
	st.session_state['user_query'] = ''


def get_openai_response(user_input):
	# This is a placeholder function. Replace with actual OpenAI API call

	message = client.beta.threads.messages.create(
		thread_id=thread.id,
		role="user",
		content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
	)

	run = client.beta.threads.runs.create(
	  thread_id=thread.id,
	  assistant_id="asst_hLMuf98Ed8lA2RFIiuDE2uuG",
	  instructions="Please address the user as Jane Doe. The user has a premium account."
	)

	# Wait for completion
	while run.status != "completed":
		# Be nice to the API
		time.sleep(0.5)
		run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

	messages = client.beta.threads.messages.list(
	  thread_id=thread.id
	)
	response = "OpenAI response to: " + user_input
	return response

# Initialize page in session state if not already initialized
if "page" not in st.session_state:
	st.session_state['page'] = "Home"

# Initialize 'user_query' in session state if it's not already present
if "user_query" not in st.session_state:
	st.session_state.user_query = ""

if 'file_array' not in st.session_state:
	st.session_state.file_array = []

# Use st.session_state.file_array for operations
if 'file_array' not in st.session_state:
	st.session_state.file_array = []

def render_assistant_page():
	# Initialize 'user_query' in session state if it's not already present
	if "user_query" not in st.session_state:
		st.session_state.user_query = ""
	# st.write(st.session_state)
	st.title("OpenAI Assistant")

	# File Uploader
	uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "docx", "csv", "xlsx"], key="file_uploader")

	# Process file upload
	if uploaded_file != None:
		#Adding the file to the array files
		if uploaded_file not in file_array:
			file_array.append(uploaded_file)
			upload_file(uploaded_file)
		st.subheader("OpenAI Assistant for Data Analysis")

		# Read the file based on its type
		if uploaded_file.type == "csv":
			df = pd.read_csv(uploaded_file)
		elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
			df = pd.read_excel(uploaded_file)

		# Display the uploaded data (optional)
		# st.write("Uploaded Data:")
		# st.write(df)

		# Process the data with OpenAI (placeholder function)
		# response = generate_response(user_query, "123", "Andrei")
		

	# Chat Area
	st.write("Ask me anything about coding, programming, or AI.")
	user_query = st.text_area("Your Query", value=st.session_state['user_query'], placeholder="Type your question here...", key="user_query")

	if st.button("Submit Query"):
		if user_query.strip():
			# Append user query to conversation
			st.session_state['conversation'].append(f"You: {user_query}")
			# Get response from OpenAI
			if len(file_id_array) > 0:
				print("No files")
				response = generate_response_files(user_query, "123", "Andrei", file_id_array)
			else:
				response = generate_response(user_query, "123", "Andrei")
			while uploaded_file != None:
				st.write("Analysis Result:")
				st.text_area("OpenAI Analysis", value=response, height=150, disabled=True)
			st.session_state['conversation'].append(f"AI: {response}")

		# Clear the input box after submission
		user_query = ''

	# Combine conversation into a single string
	conversation_text = "\n".join(st.session_state['conversation'])

	# Display conversation in a text area
	st.text_area("Conversation", value=conversation_text, height=300, disabled=True)
