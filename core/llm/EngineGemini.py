import os
import google.generativeai as genai
from typing import Optional

from common.Logger import logger


class EngineGemini:
    """
    Gemini API와 연동하여 텍스트를 생성하는 클래스.
    """

    SUPPORTED_MODEL_NAMES = {
        'gemini-1.5-flash': 'gemini-1.5-flash',
        'gemini-2.0-flash-exp': 'gemini-2.0-flash-exp'
    }

    def __init__(self, model_name: str = 'gemini-1.5-flash'):
        """
        EngineGemini 초기화 메서드.

        :param model_name: 사용할 Gemini 모델 이름. 기본값은 'gemini-1.5-flash'.
        """
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("EngineGemini: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
            raise ValueError("EngineGemini: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

        genai.configure(api_key=api_key)
        if model_name not in self.SUPPORTED_MODEL_NAMES:
            logger.error(f"EngineGemini: 지원하지 않는 모델 이름입니다: {model_name}")
            raise ValueError(f"EngineGemini: 지원하지 않는 모델 이름입니다: {model_name}")

        try:
            self.client = genai.GenerativeModel(model_name=self.SUPPORTED_MODEL_NAMES[model_name])
            logger.info(f"EngineGemini: 모델 '{model_name}' 초기화 완료.")
        except Exception as e:
            logger.error(f"EngineGemini: 모델 초기화 실패: {e}")
            raise RuntimeError(f"EngineGemini: 모델 초기화 실패: {e}")

    def _load_prompt(
        self,
        prompt_type: str = 'speech_time',
        who: str = '',
        time_sec: int = 30,
        contents: str = ''
    ) -> Optional[str]:
        """
        지정된 타입에 따라 프롬프트를 로드하고 포맷합니다.

        :param prompt_type: 프롬프트 타입 (예: 'speech_time').
        :param who: 대상자 이름.
        :param time_sec: 시간(초).
        :param contents: 내용.
        :return: 포맷된 프롬프트 문자열. 실패 시 None.
        """
        project_root = os.getcwd()
        prompt = ''

        if prompt_type == 'speech_time':
            prompt_path = os.path.join(project_root, 'prompt', 'SpeechTime_Gemini.txt')
            if not os.path.isfile(prompt_path):
                logger.error(f"EngineGemini: 프롬프트 파일을 찾을 수 없습니다: {prompt_path}")
                return None

            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt = f.read()
                prompt = prompt.format(who=who, time=time_sec, contents=contents)
                logger.info("EngineGemini: 프롬프트 로드 및 포맷 성공.")
            except Exception as e:
                logger.error(f"EngineGemini: 프롬프트 로드/포맷 중 오류 발생: {e}")
                return None
        else:
            logger.error(f"EngineGemini: 지원하지 않는 프롬프트 타입입니다: {prompt_type}")
            return None

        return prompt

    def generate(
        self,
        prompt_type: str = 'speech_time',
        who: str = '',
        time_sec: int = 30,
        contents: str = ''
    ) -> Optional[str]:
        """
        지정된 프롬프트를 기반으로 Gemini API를 호출하여 텍스트를 생성합니다.

        :param prompt_type: 프롬프트 타입 (예: 'speech_time').
        :param who: 대상자 이름.
        :param time_sec: 시간(초).
        :param contents: 내용.
        :return: 생성된 텍스트. 실패 시 None.
        """
        prompt = self._load_prompt(prompt_type, who, time_sec, contents)
        if not prompt:
            logger.error("EngineGemini: 프롬프트 준비 과정에서 오류가 발생했습니다.")
            return None

        try:
            logger.info("EngineGemini: Gemini API 호출 시작.")
            response = self.client.generate_content(str(prompt))
            logger.info("EngineGemini: Gemini API 호출 완료.")
            return response.text
        except Exception as e:
            logger.error(f"EngineGemini: Gemini API 호출 중 오류 발생: {e}")
            return None