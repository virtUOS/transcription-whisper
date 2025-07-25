import streamlit as st
import requests
import time
import os
from io import BytesIO
import subprocess
from dotenv import load_dotenv
from streamlit_quill import st_quill
import uuid
from enum import Enum

# Import metrics
from metrics import metrics, get_metrics_enabled, get_metrics_port, start_metrics_server

load_dotenv()

# Initialize metrics server if enabled
if get_metrics_enabled():
    metrics_port = get_metrics_port()
    if start_metrics_server(metrics_port):
        print(f"Metrics server started on port {metrics_port}")
    else:
        print(f"Failed to start metrics server on port {metrics_port}")

# Initialize language in session state
if 'lang' not in st.session_state:
    st.session_state.lang = 'de'  # Default UI language is German

# Translation dictionary
translations = {
    'de': {
        'title': "Transkriptionsdienst",
        'choose_input_type': "Wählen Sie den Eingabetyp",
        'upload_file': "Datei hochladen",
        'uploaded_file': "Hochgeladene Datei",
        'delete_file': "Datei löschen",
        'choose_file': "Wählen Sie eine Datei",
        'select_language': "Sprache für die Transkription auswählen",
        'select_model': "Modell auswählen",
        'detect_speakers': "Verschiedene Sprecher erkennen",
        'detect_speakers_help': "Das Transkript wird in Segmente basierend auf den Sprechern unterteilt, um verschiedene Sprecher anzuzeigen.",
        'advanced_options': "Erweiterte Optionen",
        'set_num_speakers': "Anzahl der Sprecher festlegen",
        'min_speakers': "Minimale Anzahl der Sprecher",
        'max_speakers': "Maximale Anzahl der Sprecher",
        'validate_number_speakers': "Die Mindestanzahl an Sprechern darf die maximale Anzahl an Sprechern nicht überschreiten!",
        'transcribe': "Transkribieren",
        'delete_transcription': "Transkription löschen",
        'transcription_in_progress': "Die Transkription läuft. Bitte warten...",
        'tracking_task': "Transkriptionsaufgabe mit ID verfolgen:",
        'transcription_success': "Transkription erfolgreich!",
        'transcription_failed': "Transkription fehlgeschlagen. Fehler:",
        'transcription_result': "Transkriptionsergebnis:",
        'media_player': "Mediaplayer",
        'select_format': "Format zum Anzeigen/Bearbeiten auswählen",
        'txt_format_help': "**txt**: Reines Textformat. Enthält den transkribierten Text ohne Formatierung oder Zeitstempel.",
        'json_format_help': "**json**: JSON-Format. Enthält strukturierte Daten, einschließlich Transkription mit Metadaten wie Zeitstempeln und Sprecherinformationen.",
        'srt_format_help': "**srt**: SubRip-Untertitel-Format. Wird für Videountertitel verwendet. Enthält transkribierten Text mit Timing zur Synchronisierung mit Videos.",
        'vtt_format_help': "**vtt**: WebVTT-Format. Wird für Webvideountertitel verwendet. Ähnlich wie SRT, aber unterstützt zusätzliche Formatierungen und Metadaten.",
        'save_changes': "Änderungen speichern",
        'download_file': "Datei herunterladen",
        'changes_saved': "Änderungen erfolgreich gespeichert!",
        'processing_uploaded_file': "Hochgeladene Datei wird verarbeitet...",
        'converting_file_to_mp3': "Datei wird in mp3 konvertiert...",
        'task_status': "Aufgabenstatus:",
        'elapsed_time': "Verstrichene Zeit:",
        'checking_again_in': "Erneutes Überprüfen in 30 Sekunden...",
        'logout': "Abmelden",
    },
    'en': {
        'title': "Transcription Service",
        'choose_input_type': "Choose input type",
        'upload_file': "Upload File",
        'uploaded_file': "Uploaded File",
        'delete_file': "Delete File",
        'choose_file': "Choose a file",
        'select_language': "Select Language for the Transcription",
        'select_model': "Select Model",
        'detect_speakers': "Detect different speakers",
        'detect_speakers_help': "The transcript will be split into segments based on who is speaking to indicate different speakers.",
        'advanced_options': "Advanced Options",
        'set_num_speakers': "Set number of speakers",
        'min_speakers': "Minimum Number of Speakers",
        'max_speakers': "Maximum Number of Speakers",
        'validate_number_speakers': "Minimum speakers cannot exceed maximum speakers!",
        'transcribe': "Transcribe",
        'delete_transcription': "Delete Transcription",
        'transcription_in_progress': "Transcription is in progress. Please wait...",
        'tracking_task': "Tracking transcription task with ID:",
        'transcription_success': "Transcription successful!",
        'transcription_failed': "Transcription failed. Error:",
        'transcription_result': "Transcription Result:",
        'media_player': "Media Player",
        'select_format': "Select format to view/edit",
        'txt_format_help': "**txt**: Plain text format. Contains the raw transcribed text without any formatting or timing information.",
        'json_format_help': "**json**: JSON format. Provides structured data, including the transcription along with metadata such as timestamps and speaker info.",
        'srt_format_help': "**srt**: SubRip Subtitle format. Used for video subtitles. Includes transcribed text with timing for synchronization with videos.",
        'vtt_format_help': "**vtt**: WebVTT format. Used for web video subtitles. Similar to SRT but supports additional styling and metadata.",
        'save_changes': "Save Changes",
        'download_file': "Download File",
        'changes_saved': "Changes saved successfully!",
        'processing_uploaded_file': "Processing uploaded file...",
        'converting_file_to_mp3': "Converting file to mp3...",
        'task_status': "Task Status:",
        'elapsed_time': "Elapsed time:",
        'checking_again_in': "Checking again in 30 seconds...",
        'logout': "Logout",
    }
}


def __(text_key):
    return translations.get(st.session_state.lang, translations['de']).get(text_key, text_key)


st.set_page_config(
    page_title="Transcription Service",
    page_icon="assets/whisper-logo.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL")
FFMPEG_PATH = os.getenv("FFMPEG_PATH") or "ffmpeg"
TEMP_PATH = os.getenv("TEMP_PATH") or "tmp/transcription-files"
LOGOUT_URL = os.getenv("LOGOUT_URL")

# Configurable Whisper models
WHISPER_MODELS = os.getenv("WHISPER_MODELS", "base,large-v3,large-v3-turbo").split(",")
DEFAULT_WHISPER_MODEL = os.getenv("DEFAULT_WHISPER_MODEL", "base")

# Ensure default model is in the available models list
if DEFAULT_WHISPER_MODEL not in WHISPER_MODELS:
    DEFAULT_WHISPER_MODEL = WHISPER_MODELS[0]

# Model descriptions for help text
MODEL_DESCRIPTIONS = {
    'tiny': {
        'de': "Tiny Modell: Schnellstes Modell mit geringster Genauigkeit",
        'en': "Tiny Model: Fastest model with lowest accuracy"
    },
    'base': {
        'de': "Base Modell: Gute Balance zwischen Geschwindigkeit und Genauigkeit",
        'en': "Base Model: Good balance between speed and accuracy"
    },
    'small': {
        'de': "Small Modell: Bessere Genauigkeit, langsamer",
        'en': "Small Model: Better accuracy, slower"
    },
    'medium': {
        'de': "Medium Modell: Hohe Genauigkeit",
        'en': "Medium Model: High accuracy"
    },
    'large-v1': {
        'de': "Large-v1 Modell: Sehr hohe Genauigkeit",
        'en': "Large-v1 Model: Very high accuracy"
    },
    'large-v2': {
        'de': "Large-v2 Modell: Verbesserte Version von Large-v1",
        'en': "Large-v2 Model: Improved version of Large-v1"
    },
    'large-v3': {
        'de': "Large-v3 Modell: Neuestes Large-Modell mit bester Genauigkeit",
        'en': "Large-v3 Model: Latest large model with best accuracy"
    },
    'large-v3-turbo': {
        'de': "Large-v3 Turbo Modell: Schnelle Version von Large-v3 mit ähnlicher Genauigkeit",
        'en': "Large-v3 Turbo Model: Fast version of Large-v3 with similar accuracy"
    }
}

def generate_model_help_text(lang_code):
    """Generate dynamic help text based on configured models"""
    help_texts = []
    for model in WHISPER_MODELS:
        if model in MODEL_DESCRIPTIONS:
            help_texts.append(MODEL_DESCRIPTIONS[model].get(lang_code, MODEL_DESCRIPTIONS[model]['en']))
    return ". ".join(help_texts) + "."

base_temp_dir = os.path.expanduser(TEMP_PATH)
os.makedirs(base_temp_dir, exist_ok=True)

# Language selector in the sidebar
language_options = {'Deutsch': 'de', 'English': 'en'}
selected_language = st.sidebar.selectbox('Sprache der Oberfläche / UI Language', options=list(language_options.keys()))
st.session_state.lang = language_options[selected_language]

# Track page views and session management
if get_metrics_enabled():
    # Track page view
    metrics.track_page_view(st.session_state.lang)
    
    # Update active sessions count (approximate based on session state)
    if 'session_tracked' not in st.session_state:
        st.session_state.session_tracked = True
        # This is a simple approximation - in production you might want a more sophisticated session tracking
        metrics.active_sessions.inc()

# Application title
st.title(__("title"))

# Define the Language Enum with language codes and display names
class Language(Enum):
    ARABIC = ("ar", {"de": "Arabisch", "en": "Arabic"})
    BASQUE = ("eu", {"de": "Baskisch", "en": "Basque"})
    CATALAN = ("ca", {"de": "Katalanisch", "en": "Catalan"})
    CHINESE = ("zh", {"de": "Chinesisch", "en": "Chinese"})
    CROATIAN = ("hr", {"de": "Kroatisch", "en": "Croatian"})
    CZECH = ("cs", {"de": "Tschechisch", "en": "Czech"})
    DANISH = ("da", {"de": "Dänisch", "en": "Danish"})
    DUTCH = ("nl", {"de": "Niederländisch", "en": "Dutch"})
    ENGLISH = ("en", {"de": "Englisch", "en": "English"})
    FILIPINO = ("tl", {"de": "Filipino", "en": "Filipino"})
    FINNISH = ("fi", {"de": "Finnisch", "en": "Finnish"})
    FRENCH = ("fr", {"de": "Französisch", "en": "French"})
    GALICIAN = ("gl", {"de": "Galicisch", "en": "Galician"})
    GEORGIAN = ("ka", {"de": "Georgisch", "en": "Georgian"})
    GERMAN = ("de", {"de": "Deutsch", "en": "German"})
    GREEK = ("el", {"de": "Griechisch", "en": "Greek"})
    HEBREW = ("he", {"de": "Hebräisch", "en": "Hebrew"})
    HINDI = ("hi", {"de": "Hindi", "en": "Hindi"})
    HUNGARIAN = ("hu", {"de": "Ungarisch", "en": "Hungarian"})
    ITALIAN = ("it", {"de": "Italienisch", "en": "Italian"})
    JAPANESE = ("ja", {"de": "Japanisch", "en": "Japanese"})
    KOREAN = ("ko", {"de": "Koreanisch", "en": "Korean"})
    LATVIAN = ("lv", {"de": "Lettisch", "en": "Latvian"})
    MALAYALAM = ("ml", {"de": "Malayalam", "en": "Malayalam"})
    NORWEGIAN_NO = ("no", {"de": "Norwegisch (Bokmål)", "en": "Norwegian (Bokmål)"})
    NORWEGIAN_NN = ("nn", {"de": "Norwegisch (Nynorsk)", "en": "Norwegian (Nynorsk)"})
    PERSIAN = ("fa", {"de": "Persisch", "en": "Persian"})
    POLISH = ("pl", {"de": "Polnisch", "en": "Polish"})
    PORTUGUESE = ("pt", {"de": "Portugiesisch", "en": "Portuguese"})
    ROMANIAN = ("ro", {"de": "Rumänisch", "en": "Romanian"})
    RUSSIAN = ("ru", {"de": "Russisch", "en": "Russian"})
    SLOVAK = ("sk", {"de": "Slowakisch", "en": "Slovak"})
    SLOVENIAN = ("sl", {"de": "Slowenisch", "en": "Slovenian"})
    SPANISH = ("es", {"de": "Spanisch", "en": "Spanish"})
    TELUGU = ("te", {"de": "Telugu", "en": "Telugu"})
    TURKISH = ("tr", {"de": "Türkisch", "en": "Turkish"})
    UKRAINIAN = ("uk", {"de": "Ukrainisch", "en": "Ukrainian"})
    URDU = ("ur", {"de": "Urdu", "en": "Urdu"})
    VIETNAMESE = ("vi", {"de": "Vietnamesisch", "en": "Vietnamese"})

    def __init__(self, code, names):
        self.code = code
        self.names = names

    def get_display_name(self, lang_code):
        return self.names.get(lang_code, self.names.get('de'))


def upload_file(file, lang, model, min_speakers, max_speakers):
    files = {'file': file}
    data = {
        'lang': lang,
        'model': model,
        'min_speakers': min_speakers,
        'max_speakers': max_speakers,
    }
    
    # Track transcription start
    if get_metrics_enabled():
        metrics.track_transcription_start(lang, model, min_speakers, max_speakers)
    
    start_time = time.time()
    try:
        response = requests.post(f"{API_URL}/jobs", files=files, data=data)
        response.raise_for_status()
        
        # Track API request metrics
        if get_metrics_enabled():
            duration = time.time() - start_time
            metrics.track_api_request("/jobs", "POST", response.status_code, duration)
        
        return response.json()
    except Exception as e:
        if get_metrics_enabled():
            duration = time.time() - start_time
            metrics.track_api_request("/jobs", "POST", getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500, duration)
            metrics.track_error(type(e).__name__, 'upload_file')
        raise


def check_status(task_id):
    start_time = time.time()
    try:
        response = requests.get(f"{API_URL}/jobs/{task_id}")
        response.raise_for_status()
        
        # Track API request metrics
        if get_metrics_enabled():
            duration = time.time() - start_time
            metrics.track_api_request(f"/jobs/{task_id}", "GET", response.status_code, duration)
        
        return response.json()
    except Exception as e:
        if get_metrics_enabled():
            duration = time.time() - start_time
            metrics.track_api_request(f"/jobs/{task_id}", "GET", getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500, duration)
            metrics.track_error(type(e).__name__, 'check_status')
        raise


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
    message_placeholder = st.empty()
    unique_id = str(uuid.uuid4())  # Generate a unique ID for the file
    file_extension = os.path.splitext(uploaded_file.name)[1]
    temp_input_path = os.path.join(base_temp_dir, f"{unique_id}{file_extension}")
    
    # Track file upload metrics
    file_size = len(uploaded_file.getvalue())
    if get_metrics_enabled():
        metrics.track_file_upload(file_size, file_extension.lower(), 'success')
    
    with open(temp_input_path, "wb") as temp_file:
        temp_file.write(uploaded_file.getvalue())

    if file_extension.lower() != '.mp3':
        temp_output_path = os.path.join(base_temp_dir, f"{unique_id}.mp3")
        message_placeholder.info(__("converting_file_to_mp3"))
        try:
            convert_audio(temp_input_path, temp_output_path)
            message_placeholder.empty()
            return temp_input_path, temp_output_path, uploaded_file.name
        except Exception as e:
            if get_metrics_enabled():
                metrics.track_error(type(e).__name__, 'audio_conversion')
            raise
    else:
        return temp_input_path, temp_input_path, uploaded_file.name


if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.task_id = None
    st.session_state.result = None
    st.session_state.status = None
    st.session_state.error = None
    st.session_state.input_path = None
    st.session_state.unique_file_path = None
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
    st.session_state.processing = False
    st.session_state.speaker_error = False
    st.session_state.transcription_language_code = ""  # Will be set when transcription starts

def reset_transcription_complete():
    st.session_state.task_id = None
    st.session_state.result = None
    st.session_state.status = None
    st.session_state.error = None
    st.session_state.input_path = None
    st.session_state.unique_file_path = None
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
    st.session_state.processing = False
    st.session_state.speaker_error = False
    # Keep selected_transcription_language_code
    st.session_state.transcription_language_code = ""

def reset_transcription_except_uploaded_file():
    st.session_state.task_id = None
    st.session_state.result = None
    st.session_state.status = None
    st.session_state.error = None
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
    st.session_state.processing = False
    st.session_state.speaker_error = False
    # Keep selected_transcription_language_code
    st.session_state.transcription_language_code = ""

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


def callback_validate_speakers_and_disable_controls():
    min_val = st.session_state.get("min_speakers", 1)
    max_val = st.session_state.get("max_speakers", 2)

    # Validate speaker range, set an error if needed
    if min_val > max_val:
        st.session_state.speaker_error = True
    else:
        st.session_state.speaker_error = False
        st.session_state.processing = True

def callback_extract_file():
    message_placeholder = st.empty()
    message_placeholder.info(__("processing_uploaded_file"))
    input_path, unique_file_path, original_file_name = process_uploaded_file(st.session_state.uploaded_file)
    st.session_state.media_file_data = st.session_state.uploaded_file
    st.session_state.original_file_name = original_file_name
    st.session_state.input_path = input_path
    st.session_state.unique_file_path = unique_file_path
    message_placeholder.empty()


with st.sidebar:

    if st.session_state.media_file_data:
        st.write(f"{__("uploaded_file")}: {st.session_state.original_file_name}.")
        st.button(__("delete_file"), on_click=reset_transcription_complete)
    else:
        uploaded_file = st.file_uploader(__("choose_file"),
                                         type=["mp4", "wav", "mp3"],
                                         key='uploaded_file',
                                         on_change=callback_extract_file)

    # Map language codes to display names
    language_code_list = [language.code for language in Language]
    language_code_to_display_name = {language.code: language.get_display_name(st.session_state.lang) for language in
                                        Language}

    # Compute the index from the current selection
    if 'selected_transcription_language_code' in st.session_state:
        current_selection = st.session_state.selected_transcription_language_code
    else:
        current_selection = "de"

    current_index = language_code_list.index(current_selection)

    # Render the selectbox using the index parameter on first render.
    # Note: If the key already exists, the index parameter is ignored.
    st.selectbox(
        __("select_language"),
        options=language_code_list,
        format_func=lambda code: language_code_to_display_name[code],
        index=current_index,
        key="selected_transcription_language_code"
    )

    # Get the index of the default model for the selectbox
    try:
        default_index = WHISPER_MODELS.index(DEFAULT_WHISPER_MODEL)
    except ValueError:
        default_index = 0
    
    model = st.selectbox(__("select_model"), WHISPER_MODELS, index=default_index, help=generate_model_help_text(st.session_state.lang))

    with st.expander(__("set_num_speakers")):
        detect_speakers = st.toggle(__("detect_speakers"),
                                    value=True,
                                    help=__("detect_speakers_help"))
        if detect_speakers:
            min_speakers = st.number_input(__("min_speakers"),
                                            min_value=1,
                                            max_value=20,
                                            value=1,
                                            key="min_speakers")
            max_speakers = st.number_input(__("max_speakers"),
                                            min_value=1,
                                            max_value=20,
                                            value=2,
                                            key="max_speakers")
        else:
            min_speakers = 0
            max_speakers = 0

    if st.session_state.result:
        transcribe_button_clicked = False
        st.button(__("delete_transcription"), 
                  disabled=(st.session_state.processing or not st.session_state.media_file_data),
                  on_click=reset_transcription_except_uploaded_file)
    else:
        transcribe_button_clicked = st.button(__("transcribe"),
                                            disabled=(st.session_state.processing or not st.session_state.media_file_data),
                                            on_click=callback_validate_speakers_and_disable_controls)

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
                ">{__("logout")}</button>
            </a>
        """, unsafe_allow_html=True)

if st.session_state.speaker_error:
    st.error(__("validate_number_speakers"))
elif st.session_state.media_file_data and transcribe_button_clicked:

    # Store the transcription language code and model used for this transcription
    st.session_state.transcription_language_code = st.session_state.selected_transcription_language_code
    st.session_state.selected_model = model

    lang = st.session_state.transcription_language_code

    with open(st.session_state.unique_file_path, "rb") as file_to_transcribe:
        upload_response = upload_file(file_to_transcribe, lang, model, min_speakers, max_speakers)
    upload_placeholder = st.empty()  # Placeholder for upload message

    task_id = upload_response.get("task_id")
    if task_id:
        st.session_state.task_id = task_id
        st.session_state.status = "PENDING"
        upload_placeholder.info(f"{__('tracking_task')} {task_id}")

if st.session_state.status and st.session_state.status != "SUCCESS":
    st.info(__("transcription_in_progress"))

    start_time = time.time()
    placeholder_task = st.empty()

    while True:
        status = check_status(st.session_state.task_id)
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)

        if status['status'] == "SUCCESS":
            st.session_state.status = "SUCCESS"
            st.session_state.result = status.get('result', {})
            
            # Track successful transcription completion
            if get_metrics_enabled():
                transcription_duration = elapsed_time
                lang = st.session_state.get('transcription_language_code', 'unknown')
                model = st.session_state.get('selected_model', 'unknown')
                metrics.track_transcription_complete(lang, model, transcription_duration, 'success')
            
            st.success(__("transcription_success"))
            time.sleep(1)
            st.rerun()
        elif status['status'] == "FAILURE":
            st.session_state.status = "FAILURE"
            st.session_state.error = status  # We want all the information about the failure to display in next refresh
            
            # Track failed transcription
            if get_metrics_enabled():
                lang = st.session_state.get('transcription_language_code', 'unknown')
                model = st.session_state.get('selected_model', 'unknown')
                metrics.track_transcription_complete(lang, model, elapsed_time, 'failure')
                metrics.track_error('TranscriptionFailure', 'transcription_job')
            
            st.error(f"{__('transcription_failed')} {status.get('error', 'Unknown error')}")
            break
        else:
            st.session_state.status = status['status']
            placeholder_task.info(
                f"{__('task_status')} {status['status']}. {__('elapsed_time')} {int(minutes)} min {int(seconds)} sec. "
                f"{__('checking_again_in')}"
            )
            time.sleep(30)

st.session_state.processing = False


# Display result if transcription is successful
if st.session_state.status == "SUCCESS" and st.session_state.result:

    base_name = os.path.splitext(st.session_state.original_file_name)[0]

    result = st.session_state.result

    st.write(__("transcription_result"))

    # Expander around the media player
    with st.expander(__("media_player"), expanded=True):
        # Display the media player at the top
        if st.session_state.media_file_data:
            ext = os.path.splitext(st.session_state.original_file_name)[1].lower()
            if ext in ['.mp3', '.wav']:
                st.audio(st.session_state.media_file_data)
            elif ext in ['.mp4']:
                subtitle_content = result.get('vtt_content', '') or result.get('srt_content', '') or None
                if subtitle_content:
                    st.video(st.session_state.media_file_data,
                             subtitles={st.session_state.transcription_language_code: subtitle_content})
                else:
                    st.video(st.session_state.media_file_data)

    # Define format options with fixed identifiers
    format_options = ['srt', 'json', 'txt', 'vtt']
    format_label_map = {
        'srt': __("srt"),
        'json': __("json"),
        'txt': __("txt"),
        'vtt': __("vtt")
    }

    st.selectbox(
        __("select_format"),
        options=format_options,
        format_func=lambda x: format_label_map.get(x, x),
        key='selected_tab'
    )

    # Add help text for each format
    format_help_texts = {
        'txt': __("txt_format_help"),
        'json': __("json_format_help"),
        'srt': __("srt_format_help"),
        'vtt': __("vtt_format_help")
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
        st_quill(value=st.session_state.txt_edit, key="txt_edit_key")

    elif st.session_state.selected_tab == "json":
        if st.session_state.json_edit == "":
            st.session_state.json_edit = normalize_text(result.get('json_content', ''))
            st.session_state.original_json = st.session_state.json_edit
        st_quill(value=st.session_state.json_edit, key="json_edit_key")

    elif st.session_state.selected_tab == "srt":
        if st.session_state.srt_edit == "":
            st.session_state.srt_edit = normalize_text(result.get('srt_content', ''))
            st.text(st.session_state.srt_edit)
            st.session_state.original_srt = st.session_state.srt_edit
        st_quill(value=st.session_state.srt_edit, key="srt_edit_key")

    elif st.session_state.selected_tab == "vtt":
        if st.session_state.vtt_edit == "":
            st.session_state.vtt_edit = normalize_text(result.get('vtt_content', ''))
            st.session_state.original_vtt = st.session_state.vtt_edit
        st_quill(value=st.session_state.vtt_edit, key="vtt_edit_key")

    # Compare the current content with the original content
    is_modified = False

    if st.session_state.selected_tab == "txt":
        is_modified = normalize_text(st.session_state.txt_edit_key) != normalize_text(st.session_state.original_txt)
    elif st.session_state.selected_tab == "json":
        is_modified = normalize_text(st.session_state.json_edit_key) != normalize_text(st.session_state.original_json)
    elif st.session_state.selected_tab == "srt":
        is_modified = normalize_text(st.session_state.srt_edit_key) != normalize_text(st.session_state.original_srt)
    elif st.session_state.selected_tab == "vtt":
        is_modified = normalize_text(st.session_state.vtt_edit_key) != normalize_text(st.session_state.original_vtt)

    st.session_state.is_modified = is_modified

    # Create two columns for the Save and Download buttons
    save_col, download_col = st.columns(2)

    with save_col:
        if st.button(__("save_changes"), disabled=not st.session_state.is_modified):
            save_changes()
            
            # Track save action
            if get_metrics_enabled():
                metrics.track_user_action('save_changes', st.session_state.selected_tab)
            
            st.success(__("changes_saved"))
            time.sleep(1)
            st.rerun()

    with download_col:
        # Prepare the current content and file information based on selected tab
        current_format = st.session_state.selected_tab
        current_content = ''
        file_extension = ''
        mime_type = ''

        if current_format == 'txt':
            current_content = st.session_state.txt_edit_key
            file_extension = 'txt'
            mime_type = 'text/plain'
        elif current_format == 'json':
            current_content = st.session_state.json_edit_key
            file_extension = 'json'
            mime_type = 'application/json'
        elif current_format == 'srt':
            current_content = st.session_state.srt_edit_key
            file_extension = 'srt'
            mime_type = 'text/srt'
        elif current_format == 'vtt':
            current_content = st.session_state.vtt_edit_key
            file_extension = 'vtt'
            mime_type = 'text/vtt'

        download_button_label = f"{__('download_file')} {current_format.upper()}"

        transcription_lang = st.session_state.transcription_language_code

        if current_content:
            data = BytesIO(current_content.encode('utf-8'))
        else:
            data = BytesIO(b'')  # pass empty bytes to avoid NoneType error
        
        download_clicked = st.download_button(
            label=download_button_label,
            data=data,
            file_name=f"{base_name}_{transcription_lang}.{file_extension}",
            mime=mime_type,
            disabled=(not current_content)
        )
        
        # Track download action
        if download_clicked and get_metrics_enabled():
            metrics.track_download(current_format)

elif st.session_state.status == "FAILURE" and 'status' in st.session_state.error:
    st.error(f"{__('transcription_failed')} {st.session_state.error.get('error', 'Unknown error')}")
