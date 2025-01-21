import os
from openai import OpenAI

from common.Logger import logger

class EngineOpenAI:
    """
    OpenAI API와 연동하여 텍스트를 생성하는 클래스 (기본 틀)
    """
    def __init__(self):
        """
        :param api_key: Gemini 전용 API Key, 필요 시
        """
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # possible model list
        # gpt-4o
        # gpt-4o-mini
        # o1
        # o1-mini
        # self.model = 'o1-mini'
        self.model = 'gpt-4o-mini'

    def _load_prompt(self, type='speech_time', who='', time=30, contents='') -> str:
        project_root = os.getcwd()
        prompt = ''
        system_prompt = ''
        user_prompt = ''

        if type == 'speech_time':
            prompt_path = os.path.join(project_root, 'prompt', 'SpeechTime_OpenAI.txt')
        
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            prompt = prompt.format(who=who, time=time, contents=contents)
        
        return prompt

    def generate(self, type='speech_time', who='', time=30, contents='') -> str:
        prompt = self._load_prompt(type, who=who, time=time, contents=contents)
        if not prompt:
            logger.error("프롬프트 준비 과정에서 오류가 발생했습니다.")
            return None
        
        logger.info(f'Call OpenAI API...')        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info(f'Done OpenAI API.')
        
        return response.choices[0].message.content.strip()