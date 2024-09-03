import streamlit as st
import requests
import time
import os
from io import BytesIO
from urllib.parse import urlparse, parse_qs
import yt_dlp
import subprocess
from dotenv import load_dotenv
from streamlit_quill import st_quill

load_dotenv()

st.set_page_config(
    page_title="Transkriptiondienst",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL")
FFMPEG_PATH = os.getenv("FFMPEG_PATH")

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
    response.raise_for_status()
    return response.json()


def check_status(task_id):
    response = requests.get(f"{API_URL}/jobs/{task_id}")
    response.raise_for_status()
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
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        subprocess.run([FFMPEG_PATH, '-y', '-i', input_path, output_path], capture_output=True, text=True, check=True)

    except subprocess.CalledProcessError:
        st.error("Audio conversion failed.")
        raise
    except Exception as e:
        st.error(f"An error occurred: {e}")
        raise


def process_uploaded_file(uploaded_file):
    file_name, file_extension = os.path.splitext(uploaded_file.name)

    temp_input_path = os.path.join(base_temp_dir, f"{file_name}{file_extension}")
    with open(temp_input_path, "wb") as temp_file:
        temp_file.write(uploaded_file.getvalue())

    if file_extension.lower() != '.mp3':
        temp_output_path = os.path.join(base_temp_dir, f"{file_name}.mp3")
        return temp_input_path, temp_output_path, uploaded_file.name
    else:
        return temp_input_path, temp_input_path, uploaded_file.name


def process_youtube_link(youtube_link):
    downloaded_file_path = download_youtube_video(youtube_link)

    temp_output_path = f"{os.path.splitext(downloaded_file_path)[0]}.mp3"

    original_file_name = f"{get_youtube_video_id(youtube_link)}{os.path.splitext(downloaded_file_path)[1]}"
    return temp_output_path, original_file_name


st.title("Transcription Service")

left_col, divider_col, right_col = st.columns([2, 0.2, 8])

with left_col:
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

    if (uploaded_file or youtube_link) and st.button("Transcribe"):
        if uploaded_file:
            input_path, unique_file_path, original_file_name = process_uploaded_file(uploaded_file)
        elif youtube_link:
            unique_file_path, original_file_name = process_youtube_link(youtube_link)

        st.session_state.result = None  # Reset previous results

        with right_col:
            if uploaded_file and os.path.splitext(uploaded_file.name)[1].lower() != '.mp3':
                st.info("Converting file to mp3...")
                input_path, unique_file_path, original_file_name = process_uploaded_file(uploaded_file)
                convert_audio(input_path, unique_file_path)

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
    with divider_col:
        st.html(
            '''
                <div class="divider-vertical-line"></div>
                <style>
                    .divider-vertical-line {
                        border-left: 2px solid rgba(49, 51, 63, 0.2);
                        height: 320px;
                        margin: auto;
                    }
                </style>
            '''
        )
    with right_col:
        st.info("Transcription is in progress. Please wait...")

        status_placeholder = st.empty()
        start_time = time.time()

        while True:
            status = check_status(st.session_state.task_id)
            elapsed_time = time.time() - start_time
            minutes, seconds = divmod(elapsed_time, 60)

            if status['status'] == "SUCCESS":
                st.session_state.status = "SUCCESS"
                st.session_state.result = status.get('result', {})
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
    with right_col:
        st.success("Transcription successful!")

        base_name = os.path.splitext(st.session_state.original_file_name)[0]

        result = st.session_state.result
        vtt_content = result.get('vtt_content', "")
        txt_content = result.get('txt_content', "")
        json_content = result.get('json_content', "")
        srt_content = result.get('srt_content', "")

        button1_col, button2_col, button3_col, button4_col = st.columns(4)

        button1_col.download_button(label="Download VTT File",
                                    data=BytesIO(vtt_content.encode('utf-8')) if vtt_content else BytesIO(),
                                    file_name=f"{base_name}.vtt",
                                    mime="text/vtt")

        button2_col.download_button(label="Download TXT File",
                                    data=BytesIO(txt_content.encode('utf-8')) if txt_content else BytesIO(),
                                    file_name=f"{base_name}.txt",
                                    mime="text/plain")

        button3_col.download_button(label="Download JSON File",
                                    data=BytesIO(json_content.encode('utf-8')) if json_content else BytesIO(),
                                    file_name=f"{base_name}.json",
                                    mime="application/json")

        button4_col.download_button(label="Download SRT File",
                                    data=BytesIO(srt_content.encode('utf-8')) if srt_content else BytesIO(),
                                    file_name=f"{base_name}.srt",
                                    mime="text/srt")

        st.write("Transcription Result:")
        selected_tab = st.selectbox("Select format to view/edit", ["txt", "json", "srt"])

        # Add custom CSS to set max height for the Quill editor
        st.markdown("""
            <style>
                .ql-editor {
                    max-height: 400px;
                    overflow-y: auto;
                }
            </style>
        """, unsafe_allow_html=True)

        if selected_tab == "txt":
            edited_content = st_quill(value=txt_content, key="txt_edit")
        elif selected_tab == "json":
            edited_content = st_quill(value=json_content, key="json_edit")
        elif selected_tab == "srt":
            edited_content = st_quill(value=srt_content, key="srt_edit")

        # Update session state with edited content
        if 'txt_edit' in st.session_state:
            st.session_state.result['txt_content'] = st.session_state['txt_edit']
        elif 'json_edit' in st.session_state:
            st.session_state.result['json_content'] = st.session_state['json_edit']
        elif 'srt_edit' in st.session_state:
            st.session_state.result['srt_content'] = st.session_state['srt_edit']
