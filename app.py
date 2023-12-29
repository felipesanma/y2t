from youtube_video_processing import YT2text
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# SETUP ------------------------------------------------------------------------
favicon = Image.open("favicon.ico")
st.set_page_config(
    page_title="PDF Comparison - LLM",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="auto",
)


# Sidebar contents ------------------------------------------------------------------------
with st.sidebar:
    st.title("LLM - PDF Comparison App")
    st.markdown(
        """
    ## About
    This app is an pdf comparison (LLM-powered), built using:
    - [Streamlit](https://streamlit.io/)
    - [LangChain](https://python.langchain.com/)
    - [OpenAI LLM model](https://platform.openai.com/docs/models) 
    """
    )
    st.write(
        "Made with ❤️ by [Chasquilla Engineer](https://resume.chasquillaengineer.com/)"
    )


# ROW 1 ------------------------------------------------------------------------

Title_html = """
    <style>
        .title h1{
          user-select: none;
          font-size: 43px;
          color: white;
          background: repeating-linear-gradient(-45deg, red 0%, yellow 7.14%, rgb(0,255,0) 14.28%, rgb(0,255,255) 21.4%, cyan 28.56%, blue 35.7%, magenta 42.84%, red 50%);
          background-size: 300vw 300vw;
          -webkit-text-fill-color: transparent;
          -webkit-background-clip: text;
          animation: slide 10s linear infinite forwards;
        }
        @keyframes slide {
          0%{
            background-position-x: 0%;
          }
          100%{
            background-position-x: 600vw;
          }
        }
    </style> 
    
    <div class="title">
        <h1>Super PDF Comparison</h1>
    </div>
    """
components.html(Title_html)

video_id = "-24JrpF01PM"
video_id = "sc3EjrZf4QA"
video_id = "-24JrpF01PM"
video_content = YT2text().extract(video_id=video_id)
print(video_content)
