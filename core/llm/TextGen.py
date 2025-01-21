import os
from core.llm.EngineOpenAI import EngineOpenAI
from core.llm.EngineGemini import EngineGemini

class TextGen:
    """
    공통 인터페이스: api='gemini' or 'openai' 등
    - 초기화 시 해당 provider 객체를 생성
    - genText(contents) 호출 시 prompt load -> provider.generate(...)
    """

    def __init__(self, engine: str = 'gemini'):
        """
        :param engine: 'gemini' or 'openai' 등
        """
        self.engine = engine
        self.provider = None

        if engine == 'gemini':
            self.provider = EngineGemini()
        elif engine == 'openai':
            self.provider = EngineOpenAI()
        else:
            raise ValueError(f"지원하지 않는 API: {engine}")

    def genText(self, type='speech_time', who='', time=30, contents='') -> str:

        if not self.provider:
            raise RuntimeError("Provider가 설정되지 않았습니다.")

        response_text = self.provider.generate(type='speech_time', who=who, time=time, contents=contents)
        return response_text