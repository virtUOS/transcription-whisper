import streamlit as st
import requests
import time
import os
from io import BytesIO
from urllib.parse import urlparse, parse_qs
import yt_dlp
import tempfile
import subprocess

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")

# Define the base directory for temp files
base_temp_dir = os.path.expanduser("~/transcription-whisper-temp")
os.makedirs(base_temp_dir, exist_ok=True)

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


def get_youtube_video_id(url):
    query = urlparse(url).query
    params = parse_qs(query)
    return params.get("v", [None])[0]


def download_youtube_video(youtube_url):
    video_id = get_youtube_video_id(youtube_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    temp_file_path = os.path.join(base_temp_dir, f"{video_id}.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_file_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=True)
        downloaded_file_path = ydl.prepare_filename(info_dict)

    return downloaded_file_path


def convert_audio(input_path, output_path):
    try:
        # Ensure absolute paths
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)

        # Log the paths
        print(f"ffmpeg input path: {input_path}")
        print(f"ffmpeg output path: {output_path}")

        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        # Call ffmpeg
        result = subprocess.run(['/snap/bin/ffmpeg', '-y', '-i', input_path, output_path], capture_output=True, text=True, check=True)
        print(f"ffmpeg output: {result.stdout}")
        print(f"ffmpeg error (if any): {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed: {e.stderr}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


st.title("Transcription Service")
st.write("Upload a video or audio file or provide a YouTube link to get a transcription.")

input_type = st.radio("Choose input type", ["Upload File", "YouTube Link"])

uploaded_file = None
youtube_link = None

if input_type == "Upload File":
    uploaded_file = st.file_uploader("Choose a file", type=["mp4", "wav", "mp3"])
elif input_type == "YouTube Link":
    youtube_link = st.text_input("Enter YouTube video link")

lang = st.selectbox("Select Language", ["de", "en", "es", "fr", "pt"])
model = st.selectbox("Select Model", ["base", "large-v2", "large-v3"])
min_speakers = st.number_input("Minimum Number of Speakers", min_value=1, max_value=20, value=1)
max_speakers = st.number_input("Maximum Number of Speakers", min_value=1, max_value=20, value=2)

# Initialize session state
if "task_id" not in st.session_state:
    st.session_state.task_id = None
if "result" not in st.session_state:
    st.session_state.result = None
if "status" not in st.session_state:
    st.session_state.status = None
if "original_file_name" not in st.session_state:
    st.session_state.original_file_name = None


def process_uploaded_file(uploaded_file):
    file_name, file_extension = os.path.splitext(uploaded_file.name)

    temp_input_path = os.path.join(base_temp_dir, f"{file_name}{file_extension}")
    with open(temp_input_path, "wb") as temp_file:
        temp_file.write(uploaded_file.getvalue())

    # Check if file is not mp3
    if file_extension.lower() != '.mp3':
        temp_output_path = os.path.join(base_temp_dir, f"{file_name}.mp3")
        st.info("Converting file to mp3...")
        convert_audio(temp_input_path, temp_output_path)
        return temp_output_path, uploaded_file.name
    else:
        st.info("MP3 file detected. Skipping conversion.")
        return temp_input_path, uploaded_file.name


def process_youtube_link(youtube_link):
    st.info("Downloading YouTube video...")
    downloaded_file_path = download_youtube_video(youtube_link)

    temp_output_path = f"{os.path.splitext(downloaded_file_path)[0]}.mp3"
    st.info("Converting video to mp3...")
    convert_audio(downloaded_file_path, temp_output_path)

    original_file_name = f"{get_youtube_video_id(youtube_link)}{os.path.splitext(downloaded_file_path)[1]}"
    return temp_output_path, original_file_name


if (uploaded_file or youtube_link) and st.button("Transcribe"):
    if uploaded_file:
        unique_file_path, original_file_name = process_uploaded_file(uploaded_file)
    elif youtube_link:
        unique_file_path, original_file_name = process_youtube_link(youtube_link)

    st.info("Uploading file...")
    with open(unique_file_path, "rb") as file_to_transcribe:
        upload_response = upload_file(file_to_transcribe, lang, model, min_speakers, max_speakers)
    task_id = upload_response.get("task_id")
    if task_id:
        st.session_state.task_id = task_id
        st.session_state.original_file_name = original_file_name
        st.info(f"File uploaded. Tracking task with ID: {task_id}")

# Process existing task_id from session state
if st.session_state.task_id and st.session_state.status != "SUCCESS":
    st.info("Transcription is in progress. Please wait...")

    status_placeholder = st.empty()
    start_time = time.time()

    while True:
        status = check_status(st.session_state.task_id)
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)

        if status['status'] == "SUCCESS":
            st.session_state.status = "SUCCESS"
            st.session_state.result = status['result']
            break
        elif status['status'] == "FAILURE":
            st.session_state.status = "FAILURE"
            st.error(f"Transcription failed. Error: {status.get('error', 'Unknown error')}")
            break
        else:
            st.session_state.status = status['status']
            status_placeholder.info(
                f"Task Status: {status['status']}. Elapsed time: {int(minutes)} min {int(seconds)} sec. Checking again in 30 seconds..."
            )
            time.sleep(30)

# Display result if transcription is successful
if st.session_state.status == "SUCCESS" and st.session_state.result:
    st.success("Transcription successful!")

    base_name = os.path.splitext(st.session_state.original_file_name)[0]

    result = st.session_state.result
    vtt_content = result['vtt_content']
    txt_content = result['txt_content']
    json_content = result['json_content']
    srt_content = result['srt_content']

    vtt_file = BytesIO(vtt_content.encode('utf-8'))
    vtt_file.name = f"{base_name}.vtt"

    txt_file = BytesIO(txt_content.encode('utf-8'))
    txt_file.name = f"{base_name}.txt"

    json_file = BytesIO(json_content.encode('utf-8'))
    json_file.name = f"{base_name}.json"

    srt_file = BytesIO(srt_content.encode('utf-8'))
    srt_file.name = f"{base_name}.srt"

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

