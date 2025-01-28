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

load_dotenv()

# Initialize language in session state
if 'lang' not in st.session_state:
    st.session_state.lang = 'de'  # Default UI language is German

# Translation dictionary
translations = {
    'de': {
        'title': "Transkriptionsdienst",
        'upload_instructions': "Laden Sie eine Video- oder Audiodatei hoch, um eine Transkription zu erhalten.",
        'choose_input_type': "Wählen Sie den Eingabetyp",
        'upload_file': "Datei hochladen",
        'choose_file': "Wählen Sie eine Datei",
        'select_language': "Sprache auswählen",
        'select_model': "Modell auswählen",
        'model_help': "Base Modell: Für schnelle und ressourcenschonende Transkriptionen (Balance zwischen Genauigkeit und Geschwindigkeit). Large-v3 Modell: Für detailliertere Analysen (langsamere Transkription mit höherer Genauigkeit).",
        'detect_speakers': "Verschiedene Sprecher erkennen",
        'detect_speakers_help': "Das Transkript wird in Segmente basierend auf den Sprechern unterteilt, um verschiedene Sprecher anzuzeigen.",
        'advanced_options': "Erweiterte Optionen",
        'set_num_speakers': "Anzahl der Sprecher festlegen",
        'min_speakers': "Minimale Anzahl der Sprecher",
        'max_speakers': "Maximale Anzahl der Sprecher",
        'enter_prompt': "Prompt eingeben (optional)",
        'prompt_help': "Geben Sie einen Prompt ein, um die Transkription zu leiten (optional).",
        'transcribe': "Transkribieren",
        'redo_transcription': "Transkription erneut durchführen",
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
        'upload_instructions': "Upload a video or audio file.",
        'choose_input_type': "Choose input type",
        'upload_file': "Upload File",
        'choose_file': "Choose a file",
        'select_language': "Select Language",
        'select_model': "Select Model",
        'model_help': "Base Model: For quick and low effort transcriptions (balance between accuracy and speed). Large-v3 Model: For detailed analysis (slower transcription with higher accuracy).",
        'detect_speakers': "Detect different speakers",
        'detect_speakers_help': "The transcript will be split into segments based on who is speaking to indicate different speakers.",
        'advanced_options': "Advanced Options",
        'set_num_speakers': "Set number of speakers",
        'min_speakers': "Minimum Number of Speakers",
        'max_speakers': "Maximum Number of Speakers",
        'enter_prompt': "Enter Prompt (optional)",
        'prompt_help': "Provide a prompt to guide the transcription (optional).",
        'transcribe': "Transcribe",
        'redo_transcription': "Redo Transcription",
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


def _(text_key):
    return translations.get(st.session_state.lang, translations['de']).get(text_key, text_key)


st.set_page_config(
    page_title=_("title"),
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
    MALAYALAM = ("lv", {"de": "Malayalam", "en": "Malayalam"})
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
        return self.names.get(lang_code, self.names.get('en'))


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
    st.session_state.selected_transcription_language_code = "de"  # Default transcription language code
    st.session_state.transcription_language_code = ""  # Will be set when transcription starts

# Language selector in the sidebar
language_options = {'Deutsch': 'de', 'English': 'en'}
selected_language = st.sidebar.selectbox('Sprache / Language', options=list(language_options.keys()))
st.session_state.lang = language_options[selected_language]

# Application title
st.title(_("title"))


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


def callback_disable_controls():
    st.session_state.processing = True


with st.sidebar:
    st.write(_("upload_instructions"))

    form_key = "transcription_form"

    with st.form(key=form_key):

        uploaded_file = st.file_uploader(_("choose_file"), type=["mp4", "wav", "mp3"])

        # Map language codes to display names
        language_code_list = [language.code for language in Language]
        language_code_to_display_name = {language.code: language.get_display_name(st.session_state.lang) for language in
                                         Language}

        # Use language codes as options and display names using format_func
        selected_transcription_language_code = st.selectbox(
            _("select_language"),
            options=language_code_list,
            format_func=lambda code: language_code_to_display_name[code],
            key='selected_transcription_language_code'
        )

        model = st.selectbox(_("select_model"), ["base", "large-v3"], index=0, help=_("model_help"))

        with st.expander(_("set_num_speakers")):
            detect_speakers = st.toggle(_("detect_speakers"),
                                        value=True,
                                        help=_("detect_speakers_help"))
            if detect_speakers:
                min_speakers = st.number_input(_("min_speakers"), min_value=1, max_value=20, value=1)
                max_speakers = st.number_input(_("max_speakers"), min_value=1, max_value=20, value=2)
            else:
                min_speakers = 0
                max_speakers = 0

        transcribe_button_label = _("redo_transcription") if st.session_state.result else _("transcribe")
        transcribe_button_clicked = st.form_submit_button(transcribe_button_label,
                                                          disabled=st.session_state.processing,
                                                          on_click=callback_disable_controls)

    if st.session_state.result:
        delete_button_clicked = st.button(_("delete_transcription"), disabled=st.session_state.processing)
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
                ">{_("logout")}</button>
            </a>
        """, unsafe_allow_html=True)

conversion_placeholder = st.empty()  # Placeholder for conversion message
upload_placeholder = st.empty()  # Placeholder for upload message

if uploaded_file and transcribe_button_clicked:
    reset_transcription_state()

    upload_placeholder.info(_("processing_uploaded_file"))
    input_path, unique_file_path, original_file_name = process_uploaded_file(uploaded_file)
    st.session_state.media_file_data = uploaded_file  # Store media file data

    st.session_state.original_file_name = original_file_name  # Store the original file name

    # Store the transcription language code used for this transcription
    st.session_state.transcription_language_code = st.session_state.selected_transcription_language_code

    lang = st.session_state.transcription_language_code

    if uploaded_file and os.path.splitext(uploaded_file.name)[1].lower() != '.mp3':
        conversion_placeholder.info(_("converting_file_to_mp3"))
        input_path, unique_file_path, _ = process_uploaded_file(uploaded_file)
        convert_audio(input_path, unique_file_path)

    with open(unique_file_path, "rb") as file_to_transcribe:
        upload_response = upload_file(file_to_transcribe, lang, model, min_speakers, max_speakers)

    task_id = upload_response.get("task_id")
    if task_id:
        st.session_state.task_id = task_id
        st.session_state.status = "PENDING"
        upload_placeholder.info(f"{_('tracking_task')} {task_id}")

if st.session_state.status and st.session_state.status != "SUCCESS":
    st.info(_("transcription_in_progress"))

    status_placeholder = st.empty()
    start_time = time.time()

    while True:
        status = check_status(st.session_state.task_id)
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)

        if status['status'] == "SUCCESS":
            st.session_state.status = "SUCCESS"
            st.session_state.result = status.get('result', {})
            st.success(_("transcription_success"))
            break
        elif status['status'] == "FAILURE":
            st.session_state.status = "FAILURE"
            st.session_state.error = status  # We want all the information about the failure to display in next refresh
            st.error(f"{_('transcription_failed')} {status.get('error', 'Unknown error')}")
            break
        else:
            st.session_state.status = status['status']
            status_placeholder.info(
                f"{_('task_status')} {status['status']}. {_('elapsed_time')} {int(minutes)} min {int(seconds)} sec. "
                f"{_('checking_again_in')}"
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

    st.write(_("transcription_result"))

    # Expander around the media player
    with st.expander(_("media_player"), expanded=True):
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
        'srt': _("srt"),
        'json': _("json"),
        'txt': _("txt"),
        'vtt': _("vtt")
    }

    st.selectbox(
        _("select_format"),
        options=format_options,
        format_func=lambda x: format_label_map.get(x, x),
        key='selected_tab'
    )

    # Add help text for each format
    format_help_texts = {
        'txt': _("txt_format_help"),
        'json': _("json_format_help"),
        'srt': _("srt_format_help"),
        'vtt': _("vtt_format_help")
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
        if st.button(_("save_changes"), disabled=not st.session_state.is_modified):
            save_changes()
            st.success(_("changes_saved"))
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

        download_button_label = f"{_('download_file')} {current_format.upper()}"

        transcription_lang = st.session_state.transcription_language_code

        st.download_button(
            label=download_button_label,
            data=BytesIO(current_content.encode('utf-8')),
            file_name=f"{base_name}_{transcription_lang}.{file_extension}",
            mime=mime_type
        )

elif st.session_state.status == "FAILURE" and 'status' in st.session_state.error:
    st.error(f"{_('transcription_failed')} {st.session_state.error.get('error', 'Unknown error')}")