import os
import tempfile

from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL

from audio_processing import Audio2text


class YT2text:
    def __init__(self) -> None:
        pass

    def generate_transcript(self, *, id, lan="en"):
        try:
            languages = [lan]
            if lan != "en":
                languages.append("en")

            transcript = YouTubeTranscriptApi().fetch(id, languages=languages)
            if hasattr(transcript, "to_raw_data"):
                return transcript.to_raw_data()

            return transcript
        except Exception:
            return None

    def get_videos_ids_from_playlist_id(self, *, playlist_id: str):
        playlist_link = f"https://www.youtube.com/playlist?list={playlist_id}"
        ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "noplaylist": False,
        }

        with YoutubeDL(ydl_opts) as ydl:
            playlist = ydl.extract_info(playlist_link, download=False)

        return [entry["id"] for entry in playlist.get("entries", []) if entry.get("id")]

    def download_youtube_video_to_audio(self, *, video_id: str, output_dir: str):
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(output_dir, f"{video_id}.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(video_link, download=True)
                return ydl.prepare_filename(video_info)

        except Exception as e:
            print("Connection Error")
            print(e)
            return None

    def get_youtube_video_info(self, *, video_id: str):
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "skip_download": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(video_link, download=False)

        return {
            "id": video_info.get("id", video_id),
            "title": video_info.get("title", ""),
            "description": video_info.get("description", ""),
        }

    def get_content_from_transcript(self, *, transcript):
        content = "".join(
            [text["text"] + " " for text in transcript if text["text"] != "[Music]"]
        )
        return content

    def mapping_content_and_timestamp_from_transcript(
        self, *, transcript, max_length: int = 2000
    ):
        mapping = []
        tmp_text = ""
        start_time = 0
        for text in transcript:
            tmp_text += f'{text["text"]} '
            if len(tmp_text) >= max_length:
                tmp_element = {
                    "content": tmp_text,
                    "start_time": start_time,
                    "end_time": text["start"],
                }
                mapping.append(tmp_element)
                tmp_text = ""
                start_time = text["start"]
        if tmp_text:
            mapping.append(
                {
                    "content": tmp_text,
                    "start_time": start_time,
                    "end_time": transcript[-1]["start"]
                    + transcript[-1].get("duration", 0),
                }
            )
        return mapping

    def extract_content_from_youtube_video_with_transcription(
        self, *, video_id: str, language: str = "es", max_length: int = 2000
    ):
        video_info = self.get_youtube_video_info(video_id=video_id)
        video_mapping = {
            "id": video_info["id"],
            "title": video_info["title"],
            "description": video_info["description"],
            "transcription": None,
            "timestamp_and_content_mapping": None,
        }

        transcript = self.generate_transcript(id=video_id, lan=language)

        if transcript is not None:
            video_mapping["transcription"] = self.get_content_from_transcript(
                transcript=transcript
            )
            video_mapping[
                "timestamp_and_content_mapping"
            ] = self.mapping_content_and_timestamp_from_transcript(
                transcript=transcript, max_length=max_length
            )

        return video_mapping

    def extract_content_from_youtube_video_without_transcription(
        self, *, video_id: str, video_info: dict
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            downloaded_audio = self.download_youtube_video_to_audio(
                video_id=video_id, output_dir=tmpdir
            )
            if not downloaded_audio:
                print("ERROR: youtube video not converted to audio")
                return False

            audio_content = Audio2text().extract(audio_file=downloaded_audio)

        video_info["transcription"] = audio_content["transcription"]
        video_info["language"] = audio_content["language"]
        video_info["timestamp_and_content_mapping"] = audio_content[
            "timestamp_and_content_mapping"
        ]

        return video_info

    def extract(self, *, video_id: str, language: str = "es"):
        video_info = self.extract_content_from_youtube_video_with_transcription(
            video_id=video_id, language=language
        )
        if video_info["transcription"] is not None:
            return video_info
        video_content = self.extract_content_from_youtube_video_without_transcription(
            video_id=video_id, video_info=video_info
        )
        return video_content
