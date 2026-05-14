import json
from urllib.parse import parse_qs, urlparse

import streamlit as st
from PIL import Image
from yt_dlp.utils import DownloadError

from youtube_video_processing import (
    AudioDownloadError,
    VideoUnavailableError,
    YT2text,
    to_markdown,
    to_srt,
    to_vtt,
)


SAMPLE_URL = "https://www.youtube.com/watch?v=VXFkjxPvqfU"
LANGUAGE_OPTIONS = {
    "Spanish": "es",
    "English": "en",
    "Portuguese": "pt",
    "French": "fr",
    "German": "de",
    "Italian": "it",
}
MODE_OPTIONS = {
    "Auto: captions, then Whisper": "auto",
    "YouTube captions only": "youtube",
    "Force Whisper": "whisper",
}


def get_youtube_video_id(youtube_url: str) -> str | None:
    parsed_url = urlparse(youtube_url)
    hostname = parsed_url.hostname or ""

    if hostname.endswith("youtu.be"):
        return parsed_url.path.lstrip("/") or None

    if "youtube.com" in hostname:
        if parsed_url.path == "/watch":
            return parse_qs(parsed_url.query).get("v", [None])[0]
        if parsed_url.path.startswith("/shorts/") or parsed_url.path.startswith(
            "/embed/"
        ):
            return parsed_url.path.split("/")[2] or None

    return youtube_url.strip() or None


def format_duration(seconds):
    if seconds is None:
        return "Unknown"

    minutes, remaining_seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes}:{remaining_seconds:02d}"


def source_label(source):
    if source == "youtube_transcript":
        return "YouTube captions"
    if source == "whisper":
        return "Whisper"
    return "Unknown"


def copy_transcript_button(transcription):
    st.iframe(
        f"""
        <button id="copy-transcript" type="button">Copy transcript</button>
        <script>
        const button = document.getElementById("copy-transcript");
        button.addEventListener("click", async () => {{
            await navigator.clipboard.writeText({json.dumps(transcription)});
            const originalText = button.textContent;
            button.textContent = "Copied";
            setTimeout(() => {{
                button.textContent = originalText;
            }}, 1400);
        }});
        </script>
        <style>
        body {{
            margin: 0;
            background: transparent;
        }}
        #copy-transcript {{
            width: 100%;
            height: 38px;
            border: 1px solid rgba(250, 250, 250, 0.2);
            border-radius: 0.5rem;
            background: rgb(255, 75, 75);
            color: white;
            font-family: "Source Sans Pro", sans-serif;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
        }}
        #copy-transcript:hover {{
            background: rgb(255, 106, 106);
        }}
        </style>
        """,
        width="stretch",
        height=42,
    )


def friendly_error(error):
    message = str(error)

    if isinstance(error, VideoUnavailableError) or "Video unavailable" in message:
        return (
            "This video is unavailable, private, removed, or blocked for this runtime."
        )
    if isinstance(error, AudioDownloadError):
        return "The app could not download audio for Whisper transcription."
    if isinstance(error, DownloadError):
        return "YouTube metadata or audio extraction failed. Updating yt-dlp often fixes this."
    if "CERTIFICATE_VERIFY_FAILED" in message:
        return "Python could not verify HTTPS certificates while downloading the Whisper model."
    if "ffmpeg" in message.lower():
        return "ffmpeg is missing or not available on the system path."

    return "Something went wrong while processing this video."


@st.cache_data(show_spinner=False)
def extract_video(video_id, languages, mode, whisper_model):
    return YT2text().extract(
        video_id=video_id,
        languages=list(languages),
        mode=mode,
        whisper_model=whisper_model,
    )


favicon = Image.open("favicon.ico")
st.set_page_config(
    page_title="Y2T - Transcription from Youtube Videos",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <style>
    code {
        white-space: pre-wrap !important;
    }
    .transcript-actions [data-testid="column"] {
        min-width: 0;
    }
    .stTextArea textarea {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("Y2T")
    st.caption("YouTube video to transcript")

    st.subheader("Settings")
    mode_label = st.radio(
        "Transcription mode",
        list(MODE_OPTIONS.keys()),
        index=0,
    )
    selected_language_labels = st.multiselect(
        "Caption language preference",
        list(LANGUAGE_OPTIONS.keys()),
        default=["Spanish", "English"],
    )
    whisper_model = st.selectbox(
        "Whisper model",
        ["tiny", "base", "small", "medium"],
        index=1,
        help="Larger models can be more accurate, but are slower and download more data.",
    )
    max_preview_height = st.slider(
        "Transcript preview height",
        min_value=180,
        max_value=700,
        value=360,
        step=40,
    )

    st.subheader("About")
    st.markdown(
        """
        Built with Streamlit, Whisper, youtube-transcript-api, yt-dlp, and tinytag.
        """
    )
    st.write(
        "Made with ❤️ by [Chasquilla Engineer](https://resume.chasquillaengineer.com/)"
    )

st.title("Transcription from YouTube Videos")
st.caption("Get captions when available, or transcribe the audio locally with Whisper.")

with st.form("transcription_form"):
    youtube_url = st.text_input(
        "YouTube URL",
        value=st.session_state.get("youtube_url_value", ""),
        placeholder=SAMPLE_URL,
    )
    submitted = st.form_submit_button("Get Transcription", type="primary")

if submitted:
    st.session_state.youtube_url_value = youtube_url
    st.session_state.video_content = None
    st.session_state.video_error = None

    if not youtube_url:
        st.session_state.video_error = ("Youtube URL is missing", None)
    else:
        video_id = get_youtube_video_id(youtube_url)
        if not video_id:
            st.session_state.video_error = ("Youtube URL is not valid", None)
        else:
            st.session_state.video_id = video_id
            languages = [
                LANGUAGE_OPTIONS[label] for label in selected_language_labels
            ] or ["es", "en"]
            mode = MODE_OPTIONS[mode_label]

            try:
                with st.status("Processing video", expanded=True) as status:
                    st.write("Reading YouTube metadata")
                    if mode in {"auto", "youtube"}:
                        st.write("Checking YouTube captions")
                    if mode in {"auto", "whisper"}:
                        st.write("Preparing Whisper fallback if needed")

                    st.session_state.video_content = extract_video(
                        video_id,
                        tuple(languages),
                        mode,
                        whisper_model,
                    )
                    status.update(label="Transcription ready", state="complete")
            except Exception as exc:
                st.session_state.video_error = (friendly_error(exc), exc)

if st.session_state.get("video_error"):
    error_message, raw_error = st.session_state.video_error
    st.error(error_message)
    if raw_error is not None:
        with st.expander("Advanced details"):
            st.exception(raw_error)

video_content = st.session_state.get("video_content")

if isinstance(video_content, dict):
    video_id = video_content.get("id", st.session_state.get("video_id", "video"))
    transcription = video_content.get("transcription") or ""
    timestamp_mapping = video_content.get("timestamp_and_content_mapping") or []

    top_left, top_right = st.columns((1.35, 1))
    with top_left:
        st.video(video_content.get("webpage_url") or youtube_url)
    with top_right:
        st.subheader(video_content.get("title") or "Untitled video")
        st.caption(video_content.get("webpage_url") or "")
        metric_cols = st.columns(3)
        metric_cols[0].metric("Source", source_label(video_content.get("source")))
        metric_cols[1].metric("Language", video_content.get("language") or "Unknown")
        metric_cols[2].metric("Duration", format_duration(video_content.get("duration")))

    transcript_tab, timestamps_tab, metadata_tab = st.tabs(
        ["Transcript", "Timestamps", "Metadata"]
    )

    with transcript_tab:
        if transcription:
            st.markdown('<div class="transcript-actions">', unsafe_allow_html=True)
            action_cols = st.columns([1.35, 1, 1, 1, 1, 1.25])
            with action_cols[0]:
                copy_transcript_button(transcription)
            action_cols[1].download_button(
                "TXT",
                transcription,
                file_name=f"{video_id}_transcription.txt",
                mime="text/plain",
                use_container_width=True,
            )
            action_cols[2].download_button(
                "SRT",
                to_srt(timestamp_mapping),
                file_name=f"{video_id}.srt",
                mime="text/plain",
                disabled=not timestamp_mapping,
                use_container_width=True,
            )
            action_cols[3].download_button(
                "VTT",
                to_vtt(timestamp_mapping),
                file_name=f"{video_id}.vtt",
                mime="text/vtt",
                disabled=not timestamp_mapping,
                use_container_width=True,
            )
            action_cols[4].download_button(
                "MD",
                to_markdown(video_content),
                file_name=f"{video_id}.md",
                mime="text/markdown",
                use_container_width=True,
            )
            action_cols[5].download_button(
                "JSON",
                json.dumps(video_content, ensure_ascii=False, indent=2),
                file_name=f"{video_id}.json",
                mime="application/json",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.text_area(
                "Copyable transcript",
                transcription,
                height=max_preview_height,
                label_visibility="collapsed",
            )
        else:
            st.info("No transcription found.")

    with timestamps_tab:
        if timestamp_mapping:
            st.dataframe(
                timestamp_mapping,
                width="stretch",
                hide_index=True,
                column_config={
                    "content": st.column_config.TextColumn(
                        "Content", width="large"
                    ),
                    "start_time": st.column_config.NumberColumn(
                        "Start", format="%.2f"
                    ),
                    "end_time": st.column_config.NumberColumn("End", format="%.2f"),
                },
            )
        else:
            st.info("No timestamp mapping available.")

    with metadata_tab:
        st.write(video_content.get("description") or "No description available.")
elif submitted and not st.session_state.get("video_error"):
    st.info("No transcription found.")
