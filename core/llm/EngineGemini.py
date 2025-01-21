import os
import google.generativeai as genai

from common.Logger import logger

class EngineGemini:
    """
    Gemini API와 연동하여 텍스트를 생성하는 클래스 (기본 틀)
    """
    def __init__(self):
        """
        :param api_key: Gemini 전용 API Key, 필요 시
        """
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        # gemini-2.0-flash-exp'
        # gemini-1.5-flash
        # self.client = genai.GenerativeModel(model_name='gemini-2.0-flash-exp')
        self.client = genai.GenerativeModel(model_name='gemini-1.5-flash')

    def _load_prompt(self, type='speech_time', who='', time=30, contents='') -> str:
        project_root = os.getcwd()
        prompt = ''

        if type == 'speech_time':
            prompt_path = os.path.join(project_root, 'prompt', 'SpeechTime_Gemini.txt')
        
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            prompt = prompt.format(who=who, time=time, contents=contents)
        
        return prompt
        
    def generate(self, type='speech_time', who='', time=30, contents='') -> str:
        prompt = self._load_prompt(type, who=who, time=time, contents=contents)
        if not prompt:
            logger.error("프롬프트 준비 과정에서 오류가 발생했습니다.")
            return None
        
        logger.info(f'Call Gemini API...')
        response = self.client.generate_content(str(prompt))
        logger.info(f'Done Gemini API.')
        return response.text

