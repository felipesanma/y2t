from youtube_video_processing import YT2text
import streamlit as st
from PIL import Image
import json
from streamlit_extras.stylable_container import stylable_container

# SETUP ------------------------------------------------------------------------
favicon = Image.open("favicon.ico")
st.set_page_config(
    page_title="Y2T - Transcription from Youtube Videos",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="auto",
)


# Sidebar contents ------------------------------------------------------------------------
with st.sidebar:
    st.title("Y2T - Transcription from Youtube Videos")
    st.markdown(
        """
    ## About
    This app is a Youtube Video transcriptor, built using:
    - [Streamlit](https://streamlit.io/)
    - [Whisper](https://openai.com/research/whisper)
    - youtube_transcript_api
    - youtubesearchpython
    - pytube
    - tinytag
    """
    )
    st.write(
        "Made with ❤️ by [Chasquilla Engineer](https://resume.chasquillaengineer.com/)"
    )


# ROW 1 ------------------------------------------------------------------------

st.header("Transcription from Youtube Videos")
st.markdown(
    "_Get transcripts from videos even if there is no automatically generated from youtube_"
)

youtube_url = st.text_input(
    "Youtube URL, sample: https://www.youtube.com/watch?v=ojQdVM-nbDg",
    key="youtube_url",
)
button1 = st.button("Get Transcription")
if not st.session_state.get("button1"):
    st.session_state["button1"] = button1

if st.session_state["button1"]:
    if not youtube_url:
        st.warning("Youtube URL is missing")
        st.stop()

    with st.spinner("Getting Transcription...."):
        st.session_state.video_id = youtube_url.split("=")[-1]
        try:
            st.session_state.video_content = YT2text().extract(
                video_id=st.session_state.video_id
            )
        except Exception as e:
            st.error("Something went grong...")
            st.exception(e)
            st.stop()
    print(st.session_state.video_content)
    st.snow()
    row2_spacer1, row2_1, row2_spacer2, row2_2, row2_spacer3 = st.columns(
        (0.3, 1.5, 0.3, 1.5, 0.3)
    )
    with row2_1:
        st.video(youtube_url)

    with row2_2:
        if type(st.session_state.video_content) is dict:
            st.session_state.video_content_is_dict = True
            st.header(st.session_state.video_content["title"])
            st.write(st.session_state.video_content["description"])
            if st.download_button(
                "Download Transcription",
                st.session_state.video_content["transcription"],
                file_name=f"{st.session_state.video_id}_transcription.txt",
            ):
                st.success("Thanks for downloading!")
        else:
            st.session_state.video_content_is_dict = False
    st.subheader(":blue[Transcription] :sunglasses:", divider="rainbow")

    with stylable_container(
        "codeblock",
        """
    code {
        white-space: pre-wrap !important;
    }
    """,
    ):
        if st.session_state.video_content_is_dict:
            st.code(st.session_state.video_content["transcription"])
        else:
            st.code("No transcription found")
    if st.session_state.video_content_is_dict:
        st.subheader("Youtube Video Information as JSON object", divider="blue")
        if st.download_button(
            "Download JSON",
            json.dumps(st.session_state.video_content),
            file_name=f"{st.session_state.video_id}.json",
            key="1",
        ):
            st.success("Thanks for downloading!")
        st.json(st.session_state.video_content)

    if st.button("Transcript video with Whisper"):
        with st.spinner("Getting Transcription using Whisper...."):
            try:
                st.session_state.video_content_whisper = (
                    YT2text().extract_content_from_youtube_video_without_transcription(
                        video_id=st.session_state.video_id,
                        video_info=st.session_state.video_content,
                    )
                )
            except Exception as e:
                st.error("Something went grong...")
                st.exception(e)
                st.stop()
        st.balloons()

        st.subheader(
            ":blue[Transcription] with Whisper :sunglasses:", divider="rainbow"
        )
        if type(st.session_state.video_content_whisper) is dict:
            with stylable_container(
                "codeblock",
                """
            code {
                white-space: pre-wrap !important;
            }
            """,
            ):
                st.code(st.session_state.video_content_whisper["transcription"])

            st.subheader(
                "Youtube Video Information as JSON object using Whisper", divider="blue"
            )
            if st.download_button(
                "Download JSON",
                json.dumps(st.session_state.video_content_whisper),
                file_name=f"{st.session_state.video_id}.json",
                key="2",
            ):
                st.success("Thanks for downloading!")
            st.json(st.session_state.video_content)
        else:
            st.error(
                "The video is age restricted, and can't be accessed without logging in."
            )
