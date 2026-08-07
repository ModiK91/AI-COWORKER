from dotenv import load_dotenv  # Lets us read secrets from .env
import os  # Lets us access those loaded secrets
import msal  # Imports Microsoft's authentication library

load_dotenv()  # Loads our .env values

tenant_id = os.getenv("AZURE_TENANT_ID")  # Gets your organization's ID
client_id = os.getenv("AZURE_CLIENT_ID")  # Gets this app's ID

authority = f"https://login.microsoftonline.com/{tenant_id}"  # Builds the address of your organization's login system

app = msal.PublicClientApplication(client_id, authority=authority)  # Creates a connection to Microsoft's sign-in system for this app

flow = app.initiate_device_flow(scopes=["User.Read"])  # Starts the login process, asking for basic permission to read the signed-in user's own profile

print(flow["message"])  # Prints Microsoft's instructions, including the code and the URL to visit

result = app.acquire_token_by_device_flow(flow)  # Waits until you complete sign-in in the browser, then retrieves the result

if "access_token" in result:  # Checks if sign-in succeeded
    print("Login successful!")  # Confirms success
    print(f"Signed in as: {result['id_token_claims']['name']}")  # Shows the actual signed-in user's name
    print(f"Email: {result['id_token_claims']['preferred_username']}")  # Shows their email
else:  # If sign-in failed
    print("Login failed:", result.get("error_description"))  # Shows what went wrong