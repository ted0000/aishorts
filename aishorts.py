import os
import sys
import argparse
import yaml

from dotenv import load_dotenv

from common.Logger import logger
from core.media.MediaEditor import MediaEditor
from core.lipsync.LipSync import LibSync

# .env 파일 로드
load_dotenv(override=True)

def main(args):
    # if args.file:
    #     process_urls_from_file(args.file)
    video_path = "data/dr_m_02_vertical.mp4"
    # audio_path = "result/save.mp3"
    audio_path = "temp/woman_voice_50sec.mp3"

    audio_editor = MediaEditor(audio_path)
    info = audio_editor.get_info()
    audio_duration = info.get("duration", 0)

    if audio_duration > 0:
        logger.error("Audio duration should be less than 10 seconds")
        sys.exit(1)

    video_editor = MediaEditor(video_path)
    cutoff_video_path = video_editor.cut_duration(audio_duration)
    print(cutoff_video_path)

    lipsync = LibSync()
    response = lipsync.runSyncAndMonitor(cutoff_video_path, audio_path)
    print(response)

    # download to local



if __name__ == "__main__":
    # ArgumentParser를 사용하여 커맨드라인 인자 받아오기
    parser = argparse.ArgumentParser(description="Generate short AI videos")
    # parser.add_argument("--conf", required=False, help="The URL to process")
    # parser.add_argument("--file", required=False, help="File containing a list of URLs to process")
    # parser.add_argument("--txt", required=False, help="contents file")
        
    args = parser.parse_args()
    
    # main 함수 호출
    main(args)