import os
from typing import Optional

from core.llm.EngineOpenAI import EngineOpenAI
from core.llm.EngineGemini import EngineGemini

from common.Logger import logger


class TextGen:
    """
    공통 인터페이스 클래스: 다양한 LLM API를 사용하여 텍스트를 생성합니다.
    
    초기화 시 해당 provider 객체를 생성하며, 
    gen_text 메서드를 호출 시 prompt 로드 후 provider.generate 메서드를 호출합니다.
    
    Attributes:
        engine (str): 사용할 LLM 엔진 이름 ('gemini' 또는 'openai').
        provider (EngineGemini | EngineOpenAI): 선택된 LLM 엔진의 인스턴스.
    """

    SUPPORTED_ENGINES = {'gemini', 'openai'}

    def __init__(self, engine: str = 'gemini'):
        """
        TextGen 초기화 메서드.
        
        :param engine: 사용할 LLM 엔진 이름 ('gemini' 또는 'openai').
        :raises ValueError: 지원하지 않는 엔진 이름이 제공된 경우.
        :raises RuntimeError: 엔진 초기화 중 오류가 발생한 경우.
        """
        self.engine = engine.lower()
        self.provider: Optional[object] = None

        if self.engine == 'gemini':
            try:
                self.provider = EngineGemini()
                logger.info("TextGen: Gemini 엔진 초기화 완료.")
            except Exception as e:
                logger.error(f"TextGen: Gemini 엔진 초기화 실패: {e}")
                raise RuntimeError(f"TextGen: Gemini 엔진 초기화 실패: {e}")
        elif self.engine == 'openai':
            try:
                self.provider = EngineOpenAI()
                logger.info("TextGen: OpenAI 엔진 초기화 완료.")
            except Exception as e:
                logger.error(f"TextGen: OpenAI 엔진 초기화 실패: {e}")
                raise RuntimeError(f"TextGen: OpenAI 엔진 초기화 실패: {e}")
        else:
            logger.error(f"TextGen: 지원하지 않는 API: {engine}")
            raise ValueError(f"TextGen: 지원하지 않는 API: {engine}")

    def gen_text(
        self,
        prompt_type: str = 'speech_time',
        who: str = '',
        time_sec: int = 30,
        contents: str = ''
    ) -> Optional[str]:
        """
        지정된 프롬프트 타입과 매개변수를 사용하여 텍스트를 생성합니다.
        
        :param prompt_type: 프롬프트 타입 (예: 'speech_time').
        :param who: 대상자 이름.
        :param time_sec: 시간(초).
        :param contents: 내용.
        :return: 생성된 텍스트. 실패 시 None.
        :raises RuntimeError: Provider가 설정되지 않은 경우.
        """
        if not self.provider:
            logger.error("TextGen: Provider가 설정되지 않았습니다.")
            raise RuntimeError("TextGen: Provider가 설정되지 않았습니다.")
        
        try:
            logger.info(f"TextGen: {self.engine} 엔진을 사용하여 텍스트 생성 시도.")
            response_text = self.provider.generate(
                type=prompt_type, 
                who=who, 
                time=time_sec, 
                contents=contents
            )
            if response_text:
                logger.info("TextGen: 텍스트 생성 성공.")
            else:
                logger.warning("TextGen: 텍스트 생성 실패.")
            return response_text
        except Exception as e:
            logger.error(f"TextGen: 텍스트 생성 중 오류 발생: {e}")
            return None