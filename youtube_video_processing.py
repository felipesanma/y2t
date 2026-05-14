import os
import tempfile

from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp.utils import DownloadError
from yt_dlp import YoutubeDL

from audio_processing import Audio2text


class YT2TextError(Exception):
    pass


class VideoUnavailableError(YT2TextError):
    pass


class AudioDownloadError(YT2TextError):
    pass


class YT2text:
    def __init__(self) -> None:
        pass

    def generate_transcript(self, *, id, languages=None):
        if languages is None:
            languages = ["en"]

        try:
            transcript = YouTubeTranscriptApi().fetch(id, languages=languages)
            language = getattr(transcript, "language_code", None)
            if hasattr(transcript, "to_raw_data"):
                return {
                    "language": language,
                    "items": transcript.to_raw_data(),
                }

            return {
                "language": language,
                "items": transcript,
            }
        except Exception:
            return None

    def get_videos_ids_from_playlist_id(self, *, playlist_id: str):
        playlist_link = f"https://www.youtube.com/playlist?list={playlist_id}"
        ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "noplaylist": False,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                playlist = ydl.extract_info(playlist_link, download=False)
        except DownloadError as exc:
            raise VideoUnavailableError(str(exc)) from exc

        return [entry["id"] for entry in playlist.get("entries", []) if entry.get("id")]

    def download_youtube_video_to_audio(self, *, video_id: str, output_dir: str):
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(output_dir, f"{video_id}.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(video_link, download=True)
            return ydl.prepare_filename(video_info)

    def get_youtube_video_info(self, *, video_id: str):
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "skip_download": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(video_link, download=False)
        except DownloadError as exc:
            raise VideoUnavailableError(str(exc)) from exc

        return {
            "id": video_info.get("id", video_id),
            "title": video_info.get("title", ""),
            "description": video_info.get("description", ""),
            "duration": video_info.get("duration"),
            "webpage_url": video_info.get("webpage_url", video_link),
            "thumbnail": video_info.get("thumbnail"),
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
        self, *, video_id: str, languages=None, max_length: int = 2000
    ):
        if languages is None:
            languages = ["es", "en"]

        video_info = self.get_youtube_video_info(video_id=video_id)
        video_mapping = {
            "id": video_info["id"],
            "title": video_info["title"],
            "description": video_info["description"],
            "duration": video_info.get("duration"),
            "webpage_url": video_info.get("webpage_url"),
            "thumbnail": video_info.get("thumbnail"),
            "source": "youtube_transcript",
            "language": None,
            "transcription": None,
            "timestamp_and_content_mapping": None,
        }

        transcript = self.generate_transcript(id=video_id, languages=languages)

        if transcript is not None:
            video_mapping["language"] = transcript.get("language") or languages[0]
            video_mapping["transcription"] = self.get_content_from_transcript(
                transcript=transcript["items"]
            )
            video_mapping[
                "timestamp_and_content_mapping"
            ] = self.mapping_content_and_timestamp_from_transcript(
                transcript=transcript["items"], max_length=max_length
            )

        return video_mapping

    def extract_content_from_youtube_video_without_transcription(
        self, *, video_id: str, video_info: dict, whisper_model: str = "base"
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                downloaded_audio = self.download_youtube_video_to_audio(
                    video_id=video_id, output_dir=tmpdir
                )
            except DownloadError as exc:
                raise AudioDownloadError(str(exc)) from exc

            if not downloaded_audio:
                raise AudioDownloadError("YouTube audio could not be downloaded.")

            audio_content = Audio2text(model_name=whisper_model).extract(
                audio_file=downloaded_audio
            )

        video_info["transcription"] = audio_content["transcription"]
        video_info["language"] = audio_content["language"]
        video_info["source"] = "whisper"
        video_info["whisper_model"] = whisper_model
        video_info["timestamp_and_content_mapping"] = audio_content[
            "timestamp_and_content_mapping"
        ]

        return video_info

    def extract(
        self,
        *,
        video_id: str,
        languages=None,
        mode: str = "auto",
        whisper_model: str = "base",
    ):
        if languages is None:
            languages = ["es", "en"]

        if mode == "whisper":
            video_info = self.get_youtube_video_info(video_id=video_id)
            video_info.update(
                {
                    "source": "whisper",
                    "language": None,
                    "transcription": None,
                    "timestamp_and_content_mapping": None,
                }
            )
        else:
            video_info = self.extract_content_from_youtube_video_with_transcription(
                video_id=video_id, languages=languages
            )

        if mode == "youtube":
            return video_info

        if video_info["transcription"] is not None and mode != "whisper":
            return video_info

        video_content = self.extract_content_from_youtube_video_without_transcription(
            video_id=video_id, video_info=video_info, whisper_model=whisper_model
        )
        return video_content


def format_timestamp(seconds, *, separator="."):
    if seconds is None:
        seconds = 0

    milliseconds = int(round(float(seconds) * 1000))
    total_seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"


def to_srt(timestamp_mapping):
    blocks = []
    for index, item in enumerate(timestamp_mapping or [], start=1):
        start = format_timestamp(item.get("start_time"), separator=",")
        end = format_timestamp(item.get("end_time"), separator=",")
        content = item.get("content", "").strip()
        blocks.append(f"{index}\n{start} --> {end}\n{content}")
    return "\n\n".join(blocks)


def to_vtt(timestamp_mapping):
    blocks = ["WEBVTT"]
    for item in timestamp_mapping or []:
        start = format_timestamp(item.get("start_time"))
        end = format_timestamp(item.get("end_time"))
        content = item.get("content", "").strip()
        blocks.append(f"{start} --> {end}\n{content}")
    return "\n\n".join(blocks)


def to_markdown(video_info):
    lines = [
        f"# {video_info.get('title', 'YouTube transcript')}",
        "",
        f"- Video ID: `{video_info.get('id', '')}`",
        f"- Source: `{video_info.get('source', '')}`",
        f"- Language: `{video_info.get('language', '')}`",
        "",
        "## Transcript",
        "",
        video_info.get("transcription", ""),
    ]
    return "\n".join(lines)
