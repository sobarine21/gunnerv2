import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests
from googletrans import Translator
import asyncio

# Function to check API key
def check_api_key(user_key):
    valid_keys = [
        st.secrets["api_keys"].get("key_1"),
        st.secrets["api_keys"].get("key_2"),
        st.secrets["api_keys"].get("key_3"),
        st.secrets["api_keys"].get("key_4"),
        st.secrets["api_keys"].get("key_5")
    ]
    return user_key in valid_keys

# Function to send email using Mailgun
MAILGUN_DOMAIN = "evertechcms.in"
MAILGUN_FROM = "Ever CMS <mailgun@evertechcms.in>"

def send_email(to_email, subject, html_content, api_key):
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", api_key),
            data={
                "from": MAILGUN_FROM,
                "to": to_email,
                "subject": subject,
                "html": html_content  # Send HTML content
            }
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send email to {to_email}: {e}")
        return False

# Function for Multilingual Support using Google Translate (Asynchronous)
async def translate_text(text, target_language):
    translator = Translator()
    try:
        translation = await translator.translate(text, dest=target_language)
        return translation.text
    except Exception as e:
        st.error(f"Error translating text: {e}")
        return text

# Streamlit app
user_key = st.text_input("Enter your API key to access the app:", type="password")

if user_key:
    if not check_api_key(user_key):
        st.error("Invalid API Key! Access Denied.")
    else:
        st.title("AI Powered Newsletter & Email Automation")

        # Upload CSV
        uploaded_file = st.file_uploader("Upload CSV file (columns: email, first_name)", type="csv")

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                if 'email' not in df.columns or 'first_name' not in df.columns:
                    st.error("CSV must contain 'email' and 'first_name' columns.")
                else:
                    email_list = df['email'].tolist()
                    first_name_list = df['first_name'].tolist()

                    subject = st.text_input("Email Subject", "Your Newsletter")

                    # HTML Template Upload
                    html_file = st.file_uploader("Upload HTML Email Template", type="html")
                    html_content = ""
                    if html_file is not None:
                        try:
                            html_content = html_file.read().decode("utf-8")
                            st.markdown("**Uploaded HTML Template Preview**:")
                            st.markdown(html_content, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error reading HTML file: {e}")

                    # Language selection
                    language_options = ["en", "es", "fr", "de", "it", "pt", "ru", "hi"]
                    selected_language = st.selectbox("Select Email Language", language_options)

                    # Translate email content if needed
                    if selected_language != "en" and html_content:
                        translated_body = asyncio.run(translate_text(html_content, selected_language))
                        st.session_state.translated_body = translated_body  # Store translated body in session state

                    # Show the translated body if available
                    if 'translated_body' in st.session_state:
                        st.markdown("**Translated HTML Template Preview**:")
                        st.markdown(st.session_state.translated_body, unsafe_allow_html=True)

                    preview_email = st.checkbox("Preview Email with First Record")
                    if preview_email and len(email_list) > 0:
                        preview_text = st.session_state.translated_body if 'translated_body' in st.session_state else html_content
                        personalized_preview = preview_text.replace("{first_name}", first_name_list[0])
                        st.markdown("**Preview:**")
                        st.markdown(personalized_preview, unsafe_allow_html=True)

                    confirm_send = st.checkbox("Confirm and Send Campaign")

                    if confirm_send and st.button("Send Emails"):
                        api_key = st.secrets["MAILGUN_API_KEY"]
                        success_count = 0
                        failure_count = 0
                        for email, first_name in zip(email_list, first_name_list):
                            personalized_body = st.session_state.translated_body if 'translated_body' in st.session_state else html_content
                            personalized_body = personalized_body.replace("{first_name}", first_name)
                            if send_email(email, subject, personalized_body, api_key):
                                success_count += 1
                            else:
                                failure_count += 1

                        st.success(f"Emails sent successfully: {success_count}")
                        if failure_count > 0:
                            st.warning(f"Emails failed to send: {failure_count}")

            except Exception as e:
                st.error(f"Error processing CSV: {e}")
