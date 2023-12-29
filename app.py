from youtube_video_processing import YT2text

video_id = "-24JrpF01PM"
video_content = YT2text.extract(video_id=video_id)
print(video_content)
