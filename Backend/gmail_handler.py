from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import discovery
from apiclient import errors
from flask import session
from httplib2 import Http
from oauth2client import file, client, tools
import base64
from bs4 import BeautifulSoup
import dateutil.parser as parser

def authenticate_gmail():
    # Creating a storage.JSON file with authentication details
    SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))

    # Get the authenticated user's email address
    user_info = GMAIL.users().getProfile(userId='me').execute()
    email_address = user_info['emailAddress']
    print(f"Authenticated as: {email_address}")
   #the user to the session
    session['user_email'] = email_address

    return GMAIL , email_address
def fetch_unread_emails(num_emails=5):
    GMAIL, user_email = authenticate_gmail()

    user_id = 'me'
    label_id_one = 'INBOX'

    # Getting all the messages from Inbox
    all_msgs = GMAIL.users().messages().list(userId=user_id, labelIds=[label_id_one]).execute()

    # We get a dictionary. Now reading values for the key 'messages'
    mssg_list = all_msgs.get('messages', [])

    final_list = []

    message_number = 1  # Counter for message numbers

    for mssg in mssg_list[:num_emails]:  # Iterate through the latest emails
        temp_dict = {}
        m_id = mssg['id']  # get id of an individual message
        message = GMAIL.users().messages().get(userId=user_id, id=m_id).execute()  # fetch the message using API
        payld = message['payload']  # get payload of the message
        headr = payld['headers']  # get the header of the payload

        print(f"\nMessage Number: {message_number}")

        for one in headr:  # getting the Subject
            if one['name'] == 'Subject':
                msg_subject = one['value']
                temp_dict['Subject'] = msg_subject
                print(f"Subject: {msg_subject}")
            else:
                pass

        for two in headr:  # getting the date
            if two['name'] == 'Date':
                msg_date = two['value']
                date_parse = (parser.parse(msg_date))
                m_date = (date_parse.date())
                temp_dict['Date'] = str(m_date)
            else:
                pass

        for three in headr:  # getting the Sender
            if three['name'] == 'From':
                msg_from = three['value']
                temp_dict['Sender'] = msg_from
            else:
                pass

        temp_dict['Snippet'] = message['snippet']  # fetching message snippet

        try:
            # Fetching message body
            mssg_parts = payld['parts']  # fetching the message parts
            part_one = mssg_parts[0]  # fetching the first element of the part
            part_body = part_one['body']  # fetching the body of the message
            part_data = part_body['data']  # fetching data from the body
            clean_one = part_data.replace("-", "+")  # decoding from Base64 to UTF-8
            clean_one = clean_one.replace("_", "/")  # decoding from Base64 to UTF-8
            clean_two = base64.b64decode(bytes(clean_one, 'UTF-8'))  # decoding from Base64 to UTF-8
            soup = BeautifulSoup(clean_two, "lxml")
            mssg_body = soup.body()
            temp_dict['Message_body'] = mssg_body

        except:
            pass

        final_list.append(temp_dict)  # This will create a dictionary item in the final list

        message_number += 1  # Increment the message number counter

    return final_list


def send_email(to, subject, body):
    gmail_service, user_email = authenticate_gmail()

    message = create_message(user_email, to, subject, body)
    send_message(gmail_service, 'me', message)

def create_message(sender, to, subject, body):
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject

    # Attach the body as plain text
    msg_body = MIMEText(body)
    message.attach(msg_body)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_message(service, user_id, message):
    try:
        sent_message = service.users().messages().send(userId=user_id, body=message).execute()
        print('Message Id: %s' % sent_message['id'])
        return sent_message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
