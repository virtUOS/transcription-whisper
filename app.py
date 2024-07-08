import streamlit as st
import requests
import time
from io import BytesIO
import os  # Add this import
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_URL = os.getenv("API_URL")


def upload_file(file, lang, model, min_speakers, max_speakers):
    files = {'file': file}
    data = {
        'lang': lang,
        'model': model,
        'min_speakers': min_speakers,
        'max_speakers': max_speakers,
    }
    response = requests.post(f"{API_URL}/jobs", files=files, data=data)
    return response.json()


def check_status(task_id):
    response = requests.get(f"{API_URL}/jobs/{task_id}")
    return response.json()


st.title("Transcription Service")
st.write("Upload a video or audio file to get a transcription.")

uploaded_file = st.file_uploader("Choose a file", type=["mp4", "wav", "mp3"])
lang = st.selectbox("Select Language", ["de", "en", "es", "fr", "pt"])
model = st.selectbox("Select Model", ["base", "large-v2", "large-v3"])
min_speakers = st.number_input("Minimum Number of Speakers", min_value=1, max_value=10, value=1)
max_speakers = st.number_input("Maximum Number of Speakers", min_value=1, max_value=10, value=2)

if uploaded_file and st.button("Transcribe"):
    st.info("Uploading file...")
    upload_response = upload_file(uploaded_file, lang, model, min_speakers, max_speakers)
    task_id = upload_response.get("task_id")
    if task_id:
        st.info(f"File uploaded. Tracking task with ID: {task_id}")

        st.info("Transcription is in progress. Please wait...")

        while True:
            status = check_status(task_id)
            if status['status'] == "SUCCESS":
                st.success("Transcription successful!")

                # Prepare original file name
                original_file_name = uploaded_file.name
                base_name = os.path.splitext(original_file_name)[0]

                # Prepare files for download
                vtt_content = status['result']['vtt_content']
                txt_content = status['result']['txt_content']
                json_content = status['result']['json_content']
                srt_content = status['result']['srt_content']

                # Create BytesIO objects for download
                vtt_file = BytesIO(vtt_content.encode('utf-8'))
                vtt_file.name = f"{base_name}.vtt"

                txt_file = BytesIO(txt_content.encode('utf-8'))
                txt_file.name = f"{base_name}.txt"

                json_file = BytesIO(json_content.encode('utf-8'))
                json_file.name = f"{base_name}.json"

                srt_file = BytesIO(srt_content.encode('utf-8'))
                srt_file.name = f"{base_name}.srt"

                # Display download buttons for each format
                st.download_button(label="Download VTT File",
                                   data=vtt_file,
                                   file_name=f"{base_name}.vtt",
                                   mime="text/vtt")

                st.download_button(label="Download TXT File",
                                   data=txt_file,
                                   file_name=f"{base_name}.txt",
                                   mime="text/plain")

                st.download_button(label="Download JSON File",
                                   data=json_file,
                                   file_name=f"{base_name}.json",
                                   mime="application/json")

                st.download_button(label="Download SRT File",
                                   data=srt_file,
                                   file_name=f"{base_name}.srt",
                                   mime="text/srt")

                st.write("Transcription Result:")
                st.text_area("Transcription", value=txt_content, height=200, max_chars=None)

                break
            elif status['status'] == "FAILURE":
                st.error(f"Transcription failed. Error: {status.get('error', 'Unknown error')}")
                break
            else:
                st.info(f"Task Status: {status['status']}. Checking again in 30 seconds...")
                time.sleep(30)
