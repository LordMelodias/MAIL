# app.py
import os
from flask import Flask, render_template
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import email

app = Flask(__name__)

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def fetch_gmail_inbox():
    # Load the credentials from the JSON file (generated from the Google Developer Console)
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If credentials don't exist or are invalid, initiate the OAuth 2.0 flow to authorize the application
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('api.json', SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Create the Gmail API service
    service = build('gmail', 'v1', credentials=creds)

    # Fetch the inbox messages
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])

    inbox_details = []
    if messages:
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            msg_data = {'subject': '', 'from': '', 'time': '', 'body': ''}
            for header in msg['payload']['headers']:
                if header['name'] == 'Subject':
                    msg_data['subject'] = header['value']
                elif header['name'] == 'From':
                    msg_data['from'] = header['value']
                elif header['name'] == 'Date':
                    msg_data['time'] = header['value']

            def get_message_body(msg):
                msg_parts = msg['payload'].get('parts', [])
                msg_body = ''
                for part in msg_parts:
                    if part['mimeType'] == "text/plain" or part['mimeType'] == "text":
                        msg_body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                return msg_body
            msg_body = get_message_body(msg)
            msg_data['body'] = email.message_from_string(msg_body).get_payload()
            inbox_details.append(msg_data)

    return inbox_details

@app.route("/")
def login():
    return render_template('login.html')


@app.route("/signup")
def register():
    return render_template('sigup.html')

@app.route('/home')
def index():
    inbox_details = fetch_gmail_inbox()
    return render_template('inbox.html', inbox_details=inbox_details)

if __name__ == "__main__":
    app.run(debug=True)
