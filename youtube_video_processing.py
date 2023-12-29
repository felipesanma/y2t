from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
from youtubesearchpython import Video, ResultMode
from pytube import YouTube, Playlist
import os
from audio_processing import Audio2text


class YT2text:
    def __init__(self) -> None:
        pass

    def generate_transcript(self, *, id, lan="en"):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(id, languages=[lan])
            return transcript
        except NoTranscriptFound:
            return None

    def get_videos_ids_from_playlist_id(self, *, playlist_id: str):
        playlist_link = f"https://www.youtube.com/playlist?list={playlist_id}"

        video_links = Playlist(playlist_link).video_urls

        return [url.split("=")[1] for url in video_links]

    def download_youtube_video_to_audio(self, *, video_id: str):
        video_link = f"https://www.youtube.com/watch?v={video_id}"

        try:
            video = YouTube(video_link)  # .streams.first().download(video_id)
            # filtering the audio. File extension can be mp4/webm
            # You can see all the available streams by print(video.streams)
            audio = video.streams.filter(only_audio=True)[0]
            audio.download(filename=f"{video_id}.mp3")
            return True

        except Exception as e:
            print("Connection Error")
            print(e)
            return False

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
        max_length = max_length
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
        return mapping

    def extract(self, *, video_id: str, language: str = "es", max_length: int = 2000):
        video_info = Video.getInfo(video_id, mode=ResultMode.json)
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

    def extract_content_from_youtube_video_wuthout_transcript(
        self, *, video_id: str, video_info: dict
    ):
        dowloadeed_audio = self.download_youtube_video_to_audio(video_id=video_id)
        if not dowloadeed_audio:
            print("ERROR: youtube video not converted to audio")
            return False

        audio_content = Audio2text.extract(audio_file=f"{video_id}.mp3")
        os.remove(f"{video_id}.mp3")
        video_info["transcription"] = audio_content["transcription"]
        video_info["language"] = audio_content["language"]
        video_info["timestamp_and_content_mapping"] = audio_content[
            "timestamp_and_content_mapping"
        ]

        return video_info
