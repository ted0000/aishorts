import os
from pathlib import Path

from dotenv import load_dotenv

from common.Logger import logger
from core.media.MediaEditor import MediaEditor
from core.lipsync.LipSync import LibSync
from core.media.S3Uploader import S3Uploader
from core.media.SceneMixer import SceneMixer
from core.elevenlabs.ElevenlabsClient import ElevenlabsClient
from core.llm.TextGen import TextGen

from common.Logger import logger

# .env 파일 로드
load_dotenv(override=True)

def test_S3Upload():
    # response
    current_directory = os.getcwd()
    video_file = os.path.join(current_directory, "data", "dr_m_02_vertical.mp4")
    s3uploader = S3Uploader()
    s3_key = s3uploader.upload(video_file)
    filename = Path(s3_key).name

    # presigned_url = s3uploader.gen_presigned_url(s3_key)
    download_path = s3uploader.download(s3_key, filename)

    guess = os.path.join(current_directory, filename)
    if os.path.exists(guess):
        logger.info('S3Upload test passed')
    else:
        logger.error('S3Upload test failed')

    # s3 object remove
    s3uploader.remove(s3_key)

    # delete download_path
    os.remove(download_path)

def test_LipSync():
    # video_url = 'https://videos.files.wordpress.com/C7ZiEpy8/dr_m_02_vertical.mp4'
    # audio_url = 'https://klutz91.com/wp-content/uploads/2025/01/woman_voice_50sec.mp3'

    # lipsync = LibSync()
    # response = lipsync.runSyncAndMonitor(video_url, audio_url)
    pass

def test_cut_audio():
    # 현재디렉토리 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    media_path = os.path.join(current_dir, "data", "woman_voice.m4a")
    me = MediaEditor(media_path=media_path)

    output_path = me.cut_duration(15)
    logger.info(f"Cut audio: {output_path}")

    os.remove(output_path)

def test_genshorts():
    video_path = "temp/experiment2/dr_m_02_vertical.mp4"
    audio_path = "temp/experiment2/1.mp3"

    audio_editor = MediaEditor(audio_path)
    info = audio_editor.get_info()
    audio_duration = info.get("duration", 0)

    if audio_duration <= 0:
        logger.error("Audio duration should be less than 10 seconds")
        return

    video_editor = MediaEditor(video_path)
    cutoff_video_path = video_editor.cut_duration(audio_duration)
    logger.info(f"{cutoff_video_path}")

    # upload to s3
    uploader = S3Uploader()
    s3_paths = uploader.upload_av(audio_path, cutoff_video_path, audio_duration)
    logger.info(f"Uploaded to S3: {s3_paths}")

    # lipsync
    lipsync = LibSync()
    response = lipsync.runSyncAndMonitor(s3_paths["video"]["presigned_url"], s3_paths["audio"]["presigned_url"])
    logger.info(f"LipSync response: {response}")

def test_scenemixer():
    root = os.getcwd()
    video = os.path.join(root, "data", "dr_m_02_vertical.mp4")
    audio = os.path.join(root, "temp", "woman_voice_30sec.mp3")
    images = [os.path.join(root, "temp", "scene1.jpeg"), os.path.join(root, "temp", "scene2.jpeg")]
    smixer = SceneMixer(video, audio, images)
    mixed_video = smixer.create_edited_video()
    print(mixed_video)

def test_genaudio():
    resource_path = "./temp/experiment2/1.mp3"
    target_path = "./result/test01.mp3"
    script_path = "./data/script_15s.txt"

    with open(script_path, 'r') as file:
        content = file.read()

    el_client = ElevenlabsClient()

    # clone voice
    el_client.clone("woman_voice", "", resource_path)

    # generate audio
    el_client.generate(content)

    # play
    #el_client.playAudio()

    # save
    el_client.saveAudio()

def test_gemini():
    tgen = TextGen(engine='gemini')
    who = '유재석 원장'
    contents = '임신했을때 예방주사에 대해서'
    gentext = tgen.gen_text(prompt_type='speech_time', who=who, time_sec=30, contents=contents)
    logger.info(gentext)
    return gentext

def test_openai():
    tgen = TextGen(engine='openai')
    who = '유재석 원장'
    contents = '임신했을때 예방주사에 대해서'
    gentext = tgen.gen_text(prompt_type='speech_time', who=who, time_sec=30, contents=contents)
    print(gentext)
    return gentext

if __name__ == "__main__":
    # test_S3Upload()
    # test_cut_audio()
    # test_genshorts()
    # test_scenemixer()
    # test_genaudio()
    # gentext = test_gemini()
    gettext = test_openai()
