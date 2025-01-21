import os
from dotenv import load_dotenv

from elevenlabs import Voice, VoiceSettings, play, save
from elevenlabs.client import ElevenLabs

class ElevenlabsClient:
    def __init__(self):
        self.client = ElevenLabs(
            api_key=self._getApiKey()
        )
        # defulat voice setting
        self.setVoiceSettings()

    def _getApiKey(self):
        return os.getenv("ELEVENLABS_API_KEY")
    
    def setVoiceSettings(self, stability=0.71, similarity=0.5, style=0.0, speaker=True):
        self.voice_settings = VoiceSettings(
                                stability=stability, 
                                similarity_boost=similarity, 
                                style=style, 
                                use_speaker_boost=speaker
                              )

    def setVoiceId(self, vid):
        self.voice_id = vid

    def clone(self, name, desc, fpath):
        voice = self.client.clone(
            name=name,
            description=desc,
            files=[fpath],
        )
        self.setVoiceId(voice.voice_id)

    def generate(self, content):
        self.audio = self.client.generate(
                        text=content,
                        voice=Voice(
                                voice_id=self.voice_id,
                                settings=self.voice_settings
                            )
                     )

    def saveAudio(self, path):
        if (self.audio):
            save(self.audio, path)

    def playAudio(self):
        if (self.audio):
            play(self.audio)
