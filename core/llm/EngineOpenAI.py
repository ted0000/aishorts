import os
from typing import Optional

from openai import OpenAI

from common.Logger import logger


class EngineOpenAI:
    """
    OpenAI API와 연동하여 텍스트를 생성하는 클래스.
    """

    SUPPORTED_PROMPT_TYPES = {'speech_time'}

    def __init__(self, model_name: str = 'gpt-4o-mini'):
        """
        EngineOpenAI 초기화 메서드.

        :param model_name: 사용할 OpenAI 모델 이름. 기본값은 'gpt-4o-mini'.
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("EngineOpenAI: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            raise ValueError("EngineOpenAI: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        self.model = model_name
        logger.info(f"EngineOpenAI: 모델 '{self.model}' 초기화 완료.")

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
        if prompt_type not in self.SUPPORTED_PROMPT_TYPES:
            logger.error(f"EngineOpenAI: 지원하지 않는 프롬프트 타입입니다: {prompt_type}")
            return None

        project_root = os.getcwd()
        prompt = ''
        prompt_path = os.path.join(project_root, 'prompt', f'SpeechTime_OpenAI.txt')

        if not os.path.isfile(prompt_path):
            logger.error(f"EngineOpenAI: 프롬프트 파일을 찾을 수 없습니다: {prompt_path}")
            return None

        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            prompt = prompt.format(who=who, time=time_sec, contents=contents)
            logger.info("EngineOpenAI: 프롬프트 로드 및 포맷 성공.")
        except Exception as e:
            logger.error(f"EngineOpenAI: 프롬프트 로드/포맷 중 오류 발생: {e}")
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
        지정된 프롬프트를 기반으로 OpenAI API를 호출하여 텍스트를 생성합니다.

        :param prompt_type: 프롬프트 타입 (예: 'speech_time').
        :param who: 대상자 이름.
        :param time_sec: 시간(초).
        :param contents: 내용.
        :return: 생성된 텍스트. 실패 시 None.
        """
        prompt = self._load_prompt(prompt_type, who, time_sec, contents)
        if not prompt:
            logger.error("EngineOpenAI: 프롬프트 준비 과정에서 오류가 발생했습니다.")
            return None

        try:
            logger.info("EngineOpenAI: OpenAI API 호출 시작.")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            generated_text = response.choices[0].message.content.strip()
            logger.info("EngineOpenAI: OpenAI API 호출 완료.")
            return generated_text
        except IndexError:
            logger.error("EngineOpenAI: OpenAI API 응답에서 생성된 텍스트를 찾을 수 없습니다.")
            return None