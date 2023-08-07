from oauth2client.service_account import ServiceAccountCredentials
import gspread

# The client ID and client secret
scope = ['https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials/client_secret_732661881343'
                                                         '-tfkhdb1c7ov6ns6lnvhdoo4gbias077a.apps.googleusercontent'
                                                         '.com.json',scope)
client = gspread.authorize(creds)

# Get the user's authorization code
authorization_code = "your-authorization-code"

# Authorize the user
access_token, refresh_token = client.authorize(authorization_code,
                                               scopes=["https://www.googleapis.com/auth/drive.file"])

# Print the user's access token
print(access_token)
