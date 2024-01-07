from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from apiclient import discovery
from apiclient import errors
from flask import session
from httplib2 import Http
from oauth2client import file, client, tools
import base64
from bs4 import BeautifulSoup
import dateutil.parser as parser
from bard_api import *
from task_manager import TaskManager
from datetime import datetime
from flask import session
from bs4 import BeautifulSoup

def authenticate_gmail():
    SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
    storage_path = os.path.join(os.path.dirname(__file__), 'storage.json')
    client_secret_path = os.path.join(os.path.dirname(__file__), 'client_secret.json')

    store = file.Storage(storage_path)
    creds = store.get()

    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(client_secret_path, SCOPES)
        creds = tools.run_flow(flow, store)

    GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))
    user_info = GMAIL.users().getProfile(userId='me').execute()
    email_address = user_info['emailAddress']
    print(f"Authenticated as: {email_address}")

    session['user_email'] = email_address

    return GMAIL, email_address

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
            mssg_body = soup.body
            temp_dict['Message_body'] = mssg_body.get_text(separator=' ', strip=True)  # Extract text content

        except Exception as e:
            print(f"Error fetching message body: {e}")

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


from gmail_handler import fetch_unread_emails
def parse_date(date_str):
    # Define a list of potential date formats
    date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']

    # Try parsing the date using each format
    for date_format in date_formats:
        try:
            formatted_date = datetime.strptime(date_str, date_format).date()
            return formatted_date
        except ValueError:
            pass  # Continue to the next format if the current one fails

    # If none of the formats are successful
    return None

def strip_html_tags(html):
    # If html is not a string, convert it to a string
    if not isinstance(html, str):
        html = str(html)

    # Use BeautifulSoup to parse and then get text content
    soup = BeautifulSoup(html, 'html.parser')
    text_content = soup.get_text(separator=' ', strip=True)
    
    # Remove extra whitespaces
    clean_text = ' '.join(text_content.split())

    return clean_text


bard_prompt = "Summarize the following email in 30 words:\n\n"
GOOGLE_API_KEY = 'AIzaSyCbPhOCx7wcrm_Y_z6FtR5lMKYhKkPSOsk'
model = initialize_genai(GOOGLE_API_KEY)

def get_meeting_data(email_data):
    

    subject = email_data.get('Subject', 'No Subject')
    date_str = email_data.get('Date', '')
    body = email_data.get('Message_body', 'No Body')

    # Parse the date using multiple formats
    formatted_date = parse_date(date_str)

    if formatted_date is None:
        return None  # Unable to parse the date
    summary = body
    summary  = process_email(summary, model, bard_prompt)
    print("Summary in gmail_handler:", summary)

    return {
        'subject': subject,
        'date': formatted_date,
        'summary': summary
    }

def add_meeting_to_db():
    task_manager = TaskManager('mongodb+srv://test:test123@cluster0.htaswor.mongodb.net/?retryWrites=true&w=majority', 'DB_PFA')
    user_email = session.get('user_email')

    if not user_email:
        return "User not authenticated. Cannot add a meeting from the email to the database."

    # Fetch unread emails
    unread_emails = fetch_unread_emails()

    if not unread_emails:
        return "No unread emails found."

    # Process the first unread email
    email_data = unread_emails[0]
    subject = email_data.get('Subject', 'No Subject')
    date_str = email_data.get('Date', '')
    body = email_data.get('Message_body', 'No Body')

    # Parse the date using multiple formats
    formatted_date = parse_date(date_str)

    if formatted_date is None:
        return "Unable to parse the date from the email. Please provide a valid date format."

    # Summarize the email content
    summary = summarize_email_content(model, body, bard_prompt)

    # Add the meeting to the database
    category = 'Meeting'
    result = task_manager.add_task(
        user_email=user_email,
        name=subject,
        description=summary,
        category=category,
        finish_date=formatted_date
    )

    return result
def generate_and_send_response(email_data, response_subject=None):
    try:
        # Assuming that the email_data dictionary has the necessary information
        sender_name = email_data.get('Sender', 'No Sender')
        sender_email = email_data.get('SenderEmail', 'sender@example.com')
        original_subject = email_data.get('Subject', 'No Subject')
        original_message = generate_confirmation_response(sender_name, meeting_date=email_data.get('Date', ''))

        # Generate the response subject
        subject_prefix = "Re: " if response_subject is None else ""
        response_subject = f"{subject_prefix}{original_subject}"

        # Generate your response based on the original message
        response_body = f"Dear {sender_name},\n\nThank you for your email. I have received your message:\n\n{original_message}\n\nBest regards,\n[Your Name]"

        # Send the response email
        send_email(sender_email, response_subject, response_body)

        print(f"Response email sent to {sender_name} ({sender_email}) with subject: {response_subject}.")
    except Exception as e:
        print(f"Error generating and sending response: {e}")

print("|---------Starting gmail_handler script-------|")
