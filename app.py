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
TEMP_PATH = os.getenv("TEMP_PATH")

base_temp_dir = os.path.expanduser(TEMP_PATH)
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
    original_file_name = f"{get_youtube_video_id(youtube_link)}.mp3"

    # Convert downloaded file to mp3
    convert_audio(downloaded_file_path, temp_output_path)

    return temp_output_path, original_file_name, os.path.abspath(downloaded_file_path)


if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.task_id = None
    st.session_state.result = None
    st.session_state.status = None
    st.session_state.original_file_name = None
    st.session_state.media_file_data = None
    st.session_state.input_type = None
    st.session_state.txt_edit = ""
    st.session_state.json_edit = ""
    st.session_state.srt_edit = ""
    st.session_state.vtt_edit = ""
    st.session_state.selected_tab = "txt"
    st.session_state.is_modified = False  # Initialize the modified flag
    st.session_state.original_txt = ""
    st.session_state.original_json = ""
    st.session_state.original_srt = ""
    st.session_state.original_vtt = ""
    st.session_state.first_txt = True
    st.session_state.first_json = True
    st.session_state.first_srt = True
    st.session_state.first_vtt = True
    st.session_state.processing = False

st.title("Transcription Service")


def reset_transcription_state():
    st.session_state.task_id = None
    st.session_state.result = None
    st.session_state.status = None
    st.session_state.original_file_name = None
    st.session_state.media_file_data = None
    st.session_state.input_type = None
    st.session_state.txt_edit = ""
    st.session_state.json_edit = ""
    st.session_state.srt_edit = ""
    st.session_state.vtt_edit = ""
    st.session_state.selected_tab = "txt"
    st.session_state.is_modified = False
    st.session_state.original_txt = ""
    st.session_state.original_json = ""
    st.session_state.original_srt = ""
    st.session_state.original_vtt = ""
    st.session_state.first_txt = True
    st.session_state.first_json = True
    st.session_state.first_srt = True
    st.session_state.first_vtt = True
    st.session_state.processing = False


def save_changes():
    if st.session_state.selected_tab == "txt":
        st.session_state.result['txt_content'] = st.session_state.txt_edit
    elif st.session_state.selected_tab == "json":
        st.session_state.result['json_content'] = st.session_state.json_edit
    elif st.session_state.selected_tab == "srt":
        st.session_state.result['srt_content'] = st.session_state.srt_edit
    elif st.session_state.selected_tab == "vtt":
        st.session_state.result['vtt_content'] = st.session_state.vtt_edit

    st.session_state.is_modified = False


def normalize_text(text):
    return text.strip() if text else ''


def callback_disable_controls():
    st.session_state.processing = True


with st.sidebar:
    st.write("Upload a video or audio file or provide a YouTube link to get a transcription.")

    form_key = "transcription_form"
    input_type = st.radio("Choose input type", ["Upload File", "YouTube Link"])

    uploaded_file = None
    st.session_state.youtube_link = None

    with st.form(key=form_key):

        if input_type == "Upload File":
            uploaded_file = st.file_uploader("Choose a file", type=["mp4", "wav", "mp3"])
        elif input_type == "YouTube Link":
            st.session_state.youtube_link = st.text_input("Enter YouTube video link")

        lang = st.selectbox("Select Language", ["de", "en", "es", "fr", "it", "ja", "nl", "pt", "uk", "zh"])
        model = st.selectbox("Select Model", ["tiny", "small", "base", "medium", "large-v2", "large-v3"], index=2)
        detect_speakers = st.toggle("Detect different speakers",
                                    value=True,
                                    help="This activates diarization for the transcription. Diarization "
                                         "is the process of splitting a transcription into segments "
                                         "based on who is speaking, so you can tell which parts of the "
                                         "text were spoken by different people.")

        with st.expander("Set number of speakers"):
            min_speakers = st.number_input("Minimum Number of Speakers",
                                           min_value=1, max_value=20, value=1)
            max_speakers = st.number_input("Maximum Number of Speakers",
                                           min_value=1, max_value=20, value=2)

        if not detect_speakers:
            min_speakers = 0
            max_speakers = 0

        transcribe_button_label = "Redo Transcription" if st.session_state.result else "Transcribe"
        transcribe_button_clicked = st.form_submit_button(transcribe_button_label,
                                                          disabled=st.session_state.processing,
                                                          on_click=callback_disable_controls)

    if st.session_state.result:
        delete_button_clicked = st.button("Delete Transcription", disabled=st.session_state.processing)
    else:
        delete_button_clicked = False

conversion_placeholder = st.empty()  # Placeholder for conversion message
upload_placeholder = st.empty()  # Placeholder for upload message

if (uploaded_file or st.session_state.youtube_link) and transcribe_button_clicked:
    reset_transcription_state()

    if uploaded_file:
        upload_placeholder.info("Processing uploaded file...")
        input_path, unique_file_path, original_file_name = process_uploaded_file(uploaded_file)
        st.session_state.media_file_data = uploaded_file  # Store media file data

    elif st.session_state.youtube_link:
        conversion_placeholder.info("Downloading YouTube video...")
        unique_file_path, original_file_name, downloaded_file_path = process_youtube_link(st.session_state.youtube_link)
        st.session_state.media_file_data = open(downloaded_file_path, "rb").read()  # Store media file data

    st.session_state.input_type = input_type  # Store the type of input
    st.session_state.original_file_name = original_file_name  # Store the original file name

    if uploaded_file and os.path.splitext(uploaded_file.name)[1].lower() != '.mp3':
        conversion_placeholder.info("Converting file to mp3...")
        input_path, unique_file_path, _ = process_uploaded_file(uploaded_file)
        convert_audio(input_path, unique_file_path)

    with open(unique_file_path, "rb") as file_to_transcribe:
        upload_response = upload_file(file_to_transcribe, lang, model, min_speakers, max_speakers)

    task_id = upload_response.get("task_id")
    if task_id:
        st.session_state.task_id = task_id
        st.session_state.status = "PENDING"
        upload_placeholder.info(f"Tracking transcription task with ID: {task_id}")

if st.session_state.status and st.session_state.status != "SUCCESS":
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
                f"Task Status: {status['status']}. Elapsed time: {int(minutes)} min {int(seconds)} sec. "
                f"Checking again in 30 seconds..."
            )
            time.sleep(30)

st.session_state.processing = False

# Delete transcription if delete button is clicked
if delete_button_clicked:
    reset_transcription_state()
    st.rerun()

# Display result if transcription is successful
if st.session_state.status == "SUCCESS" and st.session_state.result:
    st.success("Transcription successful!")

    base_name = os.path.splitext(st.session_state.original_file_name)[0]

    result = st.session_state.result

    button1_col, button2_col, button3_col, button4_col = st.columns(4)

    # Handle conditional checks for content before creating buttons
    if 'vtt_content' in result and result['vtt_content']:
        button1_col.download_button(
            label="Download VTT File",
            data=BytesIO(result['vtt_content'].encode('utf-8')),
            file_name=f"{base_name}_{lang}.vtt",
            mime="text/vtt"
        )

    if 'txt_content' in result and result['txt_content']:
        button2_col.download_button(
            label="Download TXT File",
            data=BytesIO(result['txt_content'].encode('utf-8')),
            file_name=f"{base_name}_{lang}.txt",
            mime="text/plain"
        )

    if 'json_content' in result and result['json_content']:
        button3_col.download_button(
            label="Download JSON File",
            data=BytesIO(result['json_content'].encode('utf-8')),
            file_name=f"{base_name}_{lang}.json",
            mime="application/json"
        )

    if 'srt_content' in result and result['srt_content']:
        button4_col.download_button(
            label="Download SRT File",
            data=BytesIO(result['srt_content'].encode('utf-8')),
            file_name=f"{base_name}_{lang}.srt",
            mime="text/srt"
        )

    st.write("Transcription Result:")

    # Create columns for the media and editor
    media_col, editor_col = st.columns([3, 7])

    with media_col:

        if st.session_state.media_file_data:
            ext = os.path.splitext(st.session_state.original_file_name)[1].lower()

            if st.session_state.input_type == "Upload File":
                if ext in ['.mp3', '.wav']:
                    st.audio(st.session_state.media_file_data)
                elif ext in ['.mp4']:
                    subtitle_content = result.get('vtt_content', '') or result.get('srt_content', '') or None
                    if subtitle_content:
                        st.video(st.session_state.media_file_data, subtitles={lang: subtitle_content})
                    else:
                        st.video(st.session_state.media_file_data)

            else:
                st.video(st.session_state.youtube_link)

    with editor_col:
        st.selectbox("Select format to view/edit", ["txt", "json", "srt", "vtt"], key="selected_tab")

        # Add CSS to limit editor height and enable scrolling
        st.markdown("""
        <style>
        .element-container:has(> iframe) {
          height: 1000px;
          overflow-y: scroll;
          overflow-x: hidden;
        }
        </style>
        """, unsafe_allow_html=True)

        # Load content into the editor
        if st.session_state.selected_tab == "txt":
            if st.session_state.txt_edit == "":
                st.session_state.txt_edit = normalize_text(result.get('txt_content', ''))
                st.session_state.original_txt = st.session_state.txt_edit
            st_quill(value=st.session_state.txt_edit, key="txt_edit")

        elif st.session_state.selected_tab == "json":
            if st.session_state.json_edit == "":
                st.session_state.json_edit = normalize_text(result.get('json_content', ''))
                st.session_state.original_json = st.session_state.json_edit
            st_quill(value=st.session_state.json_edit, key="json_edit")

        elif st.session_state.selected_tab == "srt":
            if st.session_state.srt_edit == "":
                st.session_state.srt_edit = normalize_text(result.get('srt_content', ''))
                st.session_state.original_srt = st.session_state.srt_edit
            st_quill(value=st.session_state.srt_edit, key="srt_edit")

        elif st.session_state.selected_tab == "vtt":
            if st.session_state.vtt_edit == "":
                st.session_state.vtt_edit = normalize_text(result.get('vtt_content', ''))
                st.session_state.original_vtt = st.session_state.vtt_edit
            st_quill(value=st.session_state.vtt_edit, key="vtt_edit")

        # Compare the current content with the original content
        is_modified = False

        if st.session_state.selected_tab == "txt":
            is_modified = normalize_text(st.session_state.txt_edit) != normalize_text(st.session_state.original_txt)
        elif st.session_state.selected_tab == "json":
            is_modified = normalize_text(st.session_state.json_edit) != normalize_text(st.session_state.original_json)
        elif st.session_state.selected_tab == "srt":
            is_modified = normalize_text(st.session_state.srt_edit) != normalize_text(st.session_state.original_srt)
        elif st.session_state.selected_tab == "vtt":
            is_modified = normalize_text(st.session_state.vtt_edit) != normalize_text(st.session_state.original_vtt)

        st.session_state.is_modified = is_modified

        if st.button("Save Changes", disabled=not st.session_state.is_modified):
            save_changes()
            st.success("Changes saved successfully!")
            time.sleep(1)
            st.rerun()
