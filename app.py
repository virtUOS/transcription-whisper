import streamlit as st
import requests
import time
import os
from io import BytesIO
import subprocess
from dotenv import load_dotenv
from streamlit_quill import st_quill
import uuid


load_dotenv()

st.set_page_config(
    page_title="Transkriptiondienst",
    page_icon="assets/whisper-logo.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL")
FFMPEG_PATH = os.getenv("FFMPEG_PATH") or "ffmpeg"
TEMP_PATH = os.getenv("TEMP_PATH") or "/tmp/transcription-whisper"
LOGOUT_URL = os.getenv("LOGOUT_URL")

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
    unique_id = str(uuid.uuid4())  # Generate a unique ID for the file
    file_extension = os.path.splitext(uploaded_file.name)[1]
    temp_input_path = os.path.join(base_temp_dir, f"{unique_id}{file_extension}")
    with open(temp_input_path, "wb") as temp_file:
        temp_file.write(uploaded_file.getvalue())

    if file_extension.lower() != '.mp3':
        temp_output_path = os.path.join(base_temp_dir, f"{unique_id}.mp3")
        return temp_input_path, temp_output_path, uploaded_file.name
    else:
        return temp_input_path, temp_input_path, uploaded_file.name


if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.task_id = None
    st.session_state.result = None
    st.session_state.status = None
    st.session_state.error = None
    st.session_state.original_file_name = None
    st.session_state.media_file_data = None
    st.session_state.txt_edit = ""
    st.session_state.json_edit = ""
    st.session_state.srt_edit = ""
    st.session_state.vtt_edit = ""
    st.session_state.selected_tab = "srt"
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
    st.session_state.error = None
    st.session_state.original_file_name = None
    st.session_state.media_file_data = None
    st.session_state.txt_edit = ""
    st.session_state.json_edit = ""
    st.session_state.srt_edit = ""
    st.session_state.vtt_edit = ""
    st.session_state.selected_tab = "srt"
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

    st.write("Upload a video or audio file to get a transcription.")

    form_key = "transcription_form"

    with st.form(key=form_key):

        uploaded_file = st.file_uploader("Choose a file", type=["mp4", "wav", "mp3"])

        lang = st.selectbox("Select Language", ["de", "en", "es", "fr", "it", "ja", "nl", "pt", "uk", "zh"])
        model = st.selectbox("Select Model", ["base", "large-v3"], index=0,
                             help="Base Model: for quick and low effort versions of your audio file "
                                  "(balance between accuracy and speed of transcription). "
                                  "Large-v3 Model: for a first detailed glance on research data "
                                  "(slower transcription but with higher accuracy).")
        detect_speakers = st.toggle("Detect different speakers",
                                    value=True,
                                    help="The transcript will be split into segments based on who is speaking"
                                         " to indicate different speakers.")

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

    # Add Logout button if LOGOUT_URL is set
    if LOGOUT_URL:
        st.sidebar.markdown(f"""
            <a href="{LOGOUT_URL}" target="_self">
                <button style="
                    background-color:#f44336;
                    border:none;
                    color:white;
                    padding:10px 20px;
                    text-align:center;
                    text-decoration:none;
                    display:inline-block;
                    font-size:16px;
                    margin:4px 2px;
                    cursor:pointer;
                    border-radius:4px;
                ">Logout</button>
            </a>
        """, unsafe_allow_html=True)

conversion_placeholder = st.empty()  # Placeholder for conversion message
upload_placeholder = st.empty()  # Placeholder for upload message

if uploaded_file and transcribe_button_clicked:
    reset_transcription_state()

    upload_placeholder.info("Processing uploaded file...")
    input_path, unique_file_path, original_file_name = process_uploaded_file(uploaded_file)
    st.session_state.media_file_data = uploaded_file  # Store media file data

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
            st.success("Transcription successful!")
            break
        elif status['status'] == "FAILURE":
            st.session_state.status = "FAILURE"
            st.session_state.error = status  # We want all the information about the failure to display in next refresh
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

    base_name = os.path.splitext(st.session_state.original_file_name)[0]

    result = st.session_state.result

    st.write("Transcription Result:")

    # Expander around the media player
    with st.expander("Media Player", expanded=True):
        # Display the media player at the top
        if st.session_state.media_file_data:
            ext = os.path.splitext(st.session_state.original_file_name)[1].lower()
            if ext in ['.mp3', '.wav']:
                st.audio(st.session_state.media_file_data)
            elif ext in ['.mp4']:
                subtitle_content = result.get('vtt_content', '') or result.get('srt_content', '') or None
                if subtitle_content:
                    st.video(st.session_state.media_file_data, subtitles={lang: subtitle_content})
                else:
                    st.video(st.session_state.media_file_data)

    st.selectbox("Select format to view/edit", ["srt", "json", "txt", "vtt"], key="selected_tab")

    # Add help text for each format
    format_help_texts = {
        'txt': "**txt**: Plain text format. "
               "Contains the raw transcribed text without any formatting or timing information.",
        'json': "**json**: JSON format. "
                "Provides structured data, including the transcription along with metadata such as timestamps "
                "and speaker info.",
        'srt': "**srt**: SubRip Subtitle format. Used for video subtitles. "
               "Includes transcribed text with timing for synchronization with videos.",
        'vtt': "**vtt**: WebVTT format. Used for web video subtitles. "
               "Similar to SRT but supports additional styling and metadata."
    }

    # Display the help text for the selected format
    st.write(format_help_texts[st.session_state.selected_tab])

    # Adjust the CSS for the editor if needed
    st.markdown("""
        <style>
        .element-container:has(> iframe) {
            height: 400px;
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

    # Create two columns for the Save and Download buttons
    save_col, download_col = st.columns(2)

    with save_col:
        if st.button("Save Changes", disabled=not st.session_state.is_modified):
            save_changes()
            st.success("Changes saved successfully!")
            time.sleep(1)
            st.rerun()

    with download_col:
        # Prepare the current content and file information based on selected tab
        current_format = st.session_state.selected_tab
        current_content = ''
        file_extension = ''
        mime_type = ''

        if current_format == 'txt':
            current_content = st.session_state.txt_edit
            file_extension = 'txt'
            mime_type = 'text/plain'
        elif current_format == 'json':
            current_content = st.session_state.json_edit
            file_extension = 'json'
            mime_type = 'application/json'
        elif current_format == 'srt':
            current_content = st.session_state.srt_edit
            file_extension = 'srt'
            mime_type = 'text/srt'
        elif current_format == 'vtt':
            current_content = st.session_state.vtt_edit
            file_extension = 'vtt'
            mime_type = 'text/vtt'

        download_button_label = f"Download {current_format.upper()} File"

        st.download_button(
            label=download_button_label,
            data=BytesIO(current_content.encode('utf-8')),
            file_name=f"{base_name}_{lang}.{file_extension}",
            mime=mime_type
        )
elif st.session_state.status == "FAILURE" and 'status' in st.session_state.error:
    st.error(f"Transcription failed. Error: {st.session_state.error.get('error', 'Unknown error')}")
