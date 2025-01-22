# Instroduction
This project aims to automatically generate new short videos (shorts) by combining user-uploaded audio or video clips (approximately 30–50 seconds) with pre-existing video templates. Users can input text, and the system will create a new short video featuring the provided text, synthesized speech, and a selected video template.

# Operational Flow
## 1.Voice Cloning 
Users upload a 30–50 second audio file of their own voice or a specific individual’s voice. The system processes this audio to prepare the voice model.
## 2.Text Tuning
Users input the script intended for the short video. The system utilizes a large language model (LLM) API to restructure the text to fit the desired duration.
## 3. AI Shorts Generation
The restructured script, the prepared voice model, and the selected video template are combined to generate a new short video.
## 4. SNS Platform Upload
The generated short video is uploaded to various social media platforms, including YouTube, Instagram, and TikTok.

# Code Structure
• aishorts.py: Main script (currently under development)
• test_main.py: Test suite for the main script
• gr_test.py: Gradio UI main script

To run the Gradio UI:
```python
python gr_test.py
```

# Libraries Used
• Voice Cloning and TTS: 11labs
• Lip Sync: sync.so

This project leverages advanced AI technologies to streamline the creation of engaging short-form videos, enhancing content creation and distribution across multiple platforms.