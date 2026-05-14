import whisper
from tinytag import TinyTag


class Audio2text:
    _models = {}

    def __init__(self, *, model_name: str = "base") -> None:
        self.model_name = model_name

    def generate_transcript(self, *, audio_file: str):
        if self.model_name not in self._models:
            self._models[self.model_name] = whisper.load_model(self.model_name)
        model = self._models[self.model_name]
        return model.transcribe(audio_file)

    def mapping_content_and_timestamp_from_transcript(
        self, *, transcript, max_length: int = 2000
    ):
        mapping = []
        tmp_text = ""
        start_time = 0
        for text in transcript["segments"]:
            tmp_text += f'{text["text"]} '
            if len(tmp_text) >= max_length:
                tmp_element = {
                    "content": tmp_text,
                    "start_time": start_time,
                    "end_time": text["end"],
                }
                mapping.append(tmp_element)
                tmp_text = ""
                start_time = text["end"]
        if tmp_text and transcript["segments"]:
            mapping.append(
                {
                    "content": tmp_text,
                    "start_time": start_time,
                    "end_time": transcript["segments"][-1]["end"],
                }
            )

        return mapping

    def extract(self, *, audio_file: str, max_length: int = 2000):
        transcript = self.generate_transcript(audio_file=audio_file)
        mapping = self.mapping_content_and_timestamp_from_transcript(
            transcript=transcript, max_length=max_length
        )
        audio_info = TinyTag.get(audio_file)

        audio_mapping = {
            "file_name": audio_file,
            "title": audio_info.title,
            "duration": audio_info.duration,
            "language": transcript["language"],
            "transcription": transcript["text"],
            "timestamp_and_content_mapping": mapping,
        }

        return audio_mapping
