import requests

# Access token from your previous script
access_token = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6IlAzT1d5eURGUk1rWDhPakpkaTVWLTF2TUY3V09ZZmRtS2VyTVNNU2prQk0iLCJhbGciOiJSUzI1NiIsIng1dCI6Ikg5bmo1QU9Tc3dNcGhnMVNGeDdqYVYtbEI5dyIsImtpZCI6Ikg5bmo1QU9Tc3dNcGhnMVNGeDdqYVYtbEI5dyJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9mNTc5YmQ4My1jMTgwLTQ2Y2ItYmQwOS0wNWYxYmE4NTE0OTkvIiwiaWF0IjoxNzI3MjY1MjIzLCJuYmYiOjE3MjcyNjUyMjMsImV4cCI6MTcyNzI2OTEyMywiYWlvIjoiRTJkZ1lJajhLL2h1MGZ4Sm0vYTJmVGp2dGozUEhBQT0iLCJhcHBfZGlzcGxheW5hbWUiOiJUcmFkaW5nQXBwIiwiYXBwaWQiOiI4ZmVkNjNlMS01MWNmLTQ2MzctOWRhZi0zYmI3NDdkNzRiODQiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9mNTc5YmQ4My1jMTgwLTQ2Y2ItYmQwOS0wNWYxYmE4NTE0OTkvIiwiaWR0eXAiOiJhcHAiLCJvaWQiOiIwYTVjNzEwYy0wOWRiLTRhZjMtYmQxYS1iMmQ4NWFmNTAxZTciLCJyaCI6IjAuQVlFQWc3MTU5WURCeTBhOUNRWHh1b1VVbVFNQUFBQUFBQUFBd0FBQUFBQUFBQUNCQUFBLiIsInN1YiI6IjBhNWM3MTBjLTA5ZGItNGFmMy1iZDFhLWIyZDg1YWY1MDFlNyIsInRlbmFudF9yZWdpb25fc2NvcGUiOiJFVSIsInRpZCI6ImY1NzliZDgzLWMxODAtNDZjYi1iZDA5LTA1ZjFiYTg1MTQ5OSIsInV0aSI6IjdqVVNobWZXRTBtYy1QWlFheE9uQUEiLCJ2ZXIiOiIxLjAiLCJ3aWRzIjpbIjA5OTdhMWQwLTBkMWQtNGFjYi1iNDA4LWQ1Y2E3MzEyMWU5MCJdLCJ4bXNfaWRyZWwiOiI3IDIyIiwieG1zX3RjZHQiOjE2MTc3MTA4OTEsInhtc190ZGJyIjoiRVUifQ.eWAGeklkXVsDH43Jk_J6Y-Kf9UgPibIzA0M0YCuQETlK7sZp2raWCq9phNy07Pn66zcDISj559zWIprUQ3mJnoCU5GKOUKu34Zhc058AawCAQH2zAkWu7DvwiD94TuTTYLDCtAPDBI74JbPLOVLm1fKZK5k9Zh7LnM6J4oIGnK4ENKjHXTGYDbxYDZoomyn6v6vTo3a2yFj8duSgEoORmp_79RBUubJmlskhmW5c72W0IlJk9cJOQHD5UbU1I49mF3E4IlJBQvC8Cwf0pcb2dnumJiiiWddcBCh-SGRo4xR9r06_He0Dk1QmAIpn2zyeIVTD6TRScoqqdb4uyu29uw'

# User email or ID (replace with actual user email or user ID)
user_principal_name = 'andrei.ionita@mynexte.com'

# File you want to upload
file_path = "./Market Fundamentals/Spot_Price_Forecast/Results_Price_Forecast.xlsx"
upload_url = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}/drive/root:/0453_2_Energy_markets/000. Trade/Trading_Tools/test.xlsx:/content"

# Read the file content
with open(file_path, 'rb') as file:
    file_content = file.read()

# Set headers
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/octet-stream"
}

# Make the PUT request to upload the file
response = requests.put(upload_url, headers=headers, data=file_content)

if response.status_code == 201:
    print("File uploaded successfully!")
else:
    print(f"Failed to upload file. Status code: {response.status_code}")
    print(response.json())


https://login.microsoftonline.com/f579bd83-c180-46cb-bd09-05f1ba851499/adminconsent?client_id=8fed63e1-51cf-4637-9daf-3bb747d74b84&state=12345&redirect_uri=https://nexteai.streamlit.app/

