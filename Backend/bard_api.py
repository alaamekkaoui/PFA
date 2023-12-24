import google.generativeai as genai
import textwrap

def configure_api(api_key):
    genai.configure(api_key=api_key)

def initialize_model():
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            return genai.GenerativeModel(m.name)

def summarize_email(model, email_text):
    summary = model.generate_content(email_text).text
    return summary

def generate_confirmation_response(sender_name, meeting_date):
    response = f"Dear {sender_name},\n\nThank you for the meeting details. I have noted the following:\n- Meeting Date: {meeting_date}\n\nLooking forward to our collaboration.\n\nBest regards,\n[Your Name]"
    return response
def to_markdown(text):
    bullet_character = '•'
    replacement = '  *'
    indentation = ' | '

    formatted_text = text.replace(bullet_character, replacement)
    indented_text = textwrap.indent(formatted_text, indentation, predicate=lambda _: True)

    return indented_text


# Set up your API key
GOOGLE_API_KEY = 'Use your Damn Key'
configure_api(GOOGLE_API_KEY)

# Initialize the generative model
model = initialize_model()

# Example email text
user_input = " can you summarize the email for me into title , short description , and then date . and write me a confirmation email response. \
I trust this message finds you in good spirits. As we prepare for another day of collaboration, I wanted to remind you about our scheduled meeting tomorrow. \
Meeting Details: Date: January 25, 2023 Time: 10:00 AM Location: Conference Room A (or Virtual Meeting Link) \
Agenda: Project Updates Team Goals for Q1 Client Presentation Preparation \
Your active participation is crucial, and your insights will greatly contribute to our discussions. If you have any questions or need additional information, please don't hesitate to reach out. \
Looking forward to our fruitful meeting!"
user_input = user_input.replace('\n', ' ')
# Summarize the email
summary = summarize_email(model, user_input)

# Display the summarized email
print("Summary: \n", to_markdown(summary))

# Example sender information
sender_name = "John Doe"
meeting_date = "January 25, 2024"

# Generate a confirmation response
confirmation_response = generate_confirmation_response(sender_name, meeting_date)

# Display the confirmation response
print("Confirmation Response:\n", to_markdown(confirmation_response))
