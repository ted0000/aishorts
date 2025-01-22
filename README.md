# Project 개요
이 프로젝트는 사용자가 업로드한 약 30~50초 분량의 음성 데이터(또는 비디오)를 기반으로 새로운 TTS(텍스트-음성 변환) 음성을 생성하고, 기존에 업로드된 비디오 템플릿과 결합하여, 사용자가 입력한 텍스트만으로 새로운 쇼츠 영상을 자동으로 제작하는것을 목표로함.

# 동작 설명
### 1. voice clone
사용자가 본인 자신이나 특정인물의 voice를 30초~50초 분량의 audio file을 입력하면 해당 인물의 voice가 준비가됨.
### 2. Text tune
사용자가 aishorts에 들어갈 대사의 내용을 입력하면 llm api로 지정한 시간에 맞춰서 대사를 재구성함.
### 3. aiShorts Gen
재구성한 aiShorts의 대사, 그리고 인물의 voice, 그리고 인물의 Video Template을 입력하면 새로운 Shorts를 생성함.
### 4. SNS Platform upload
사용자의 Youtube, Intagram, Tiktok등 여러 SNS에 생성된 Shorts를 업로드함.

# 코드 설명
aishorts.py - main (아직 개발중)
test_main.py - test main
gr_test.py - Gradio UI main
```python
python gr_test.py
```

# 사용한 Named Library
- voice clone, tts : 11labs
- lipsync : sync.so