import os
import requests
import time
from datetime import datetime, timezone, timedelta

from common.Logger import logger

class LibSync():
    def __init__(self):
        self.endpoint = self._getEndpoint()
        self.apikey = self._getApiKey()

    def _getEndpoint(self):
        return os.getenv("SYNC_SO_API_ENDPOINT")
    
    def _getApiKey(self):
        return os.getenv("SYNC_SO_KEY")
    
    def _getGeneratedEndpoint(self, id: str) -> str:
        return f'{self.endpoint}/{id}'
    
    def reqLibSync(self, video_url, audio_url):
        payload = {
            "model": os.getenv("SYNC_SO_MODEL"),
            "input": [
                {
                    "type": "video",
                    "url": video_url
                },
                {
                    "type": "audio",
                    "url": audio_url
                }
            ],
            "options": {"output_format": "mp4"},
            "webhookUrl": os.getenv("SYNC_SO_WEBHOOK")
        }
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.apikey
        }

        logger.info(f"Requesting LipSync API...")
        response = requests.request("POST", self.endpoint, json=payload, headers=headers)
        return response.json()
    
    def monitor_status(self, generation_id: str, poll_interval=60, max_duration=1200):
        """
        1) poll_interval 간격으로 GET 요청하여 상태를 확인
        2) 최대 max_duration(초)까지만 폴링 (기본값 900초 = 15분)
        3) 상태가 'COMPLETED'면 outputUrl, status, total_time 반환
        4) 상태가 'CANCELED', 'FAILED', 'REJECTED'면 즉시 반환
        5) 'PENDING', 'PROCESSING'는 poll_interval만큼 대기 후 재시도
        6) 15분 넘으면 TIMEOUT 처리
        """
        import time
        from datetime import datetime, timezone, timedelta

        headers = {"x-api-key": self.apikey}

        start_time = time.time()  # 폴링 시작 시점 (epoch time)

        while True:
            # 진행 시간 계산
            elapsed = time.time() - start_time
            if elapsed > max_duration:
                # 15분(900초) 초과 시 타임아웃 처리
                logger.error("Polling timed out (exceeded 15 minutes).")
                return {
                    "outputUrl": None,
                    "status": "TIMEOUT",
                    "total_time": None
                }

            url = self._getGeneratedEndpoint(generation_id)
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(f"Error: {response.status_code} - {response.text}")
                time.sleep(poll_interval)
                continue
            
            data = response.json()
            current_status = data.get("status", "UNKNOWN")
            
            logger.info(f"Now status: {current_status}")
            
            if current_status == "COMPLETED":
                output_url = data.get("outputUrl")
                created_at_utc = data.get("createdAt")  # 예: "2025-01-10T04:04:53.706Z"

                total_time_str = "N/A"
                if created_at_utc:
                    created_at_dt = datetime.fromisoformat(created_at_utc.replace("Z", "+00:00"))
                    now_local = datetime.now(timezone(timedelta(hours=9)))
                    diff = now_local - created_at_dt
                    total_time_str = str(diff)

                return {
                    "outputUrl": output_url,
                    "status": current_status,
                    "total_time": total_time_str
                }

            elif current_status in ["CANCELED", "FAILED", "REJECTED", "PENDING"]:
                return {
                    "outputUrl": None,
                    "status": current_status,
                    "total_time": None
                }
            elif current_status == "PROCESSING":
                time.sleep(poll_interval)
                continue
            
            else:
                # 예기치 못한 상태
                logger.warning(f"Unexpected status: {current_status}. Retrying...")
                time.sleep(poll_interval)
                continue
    
    def runSyncAndMonitor(self, video_url, audio_url, poll_interval=60):
        """
        1) reqLibSync() 호출 -> generation_id 획득
        2) generation_id 기반으로 monitor_status() 진행
        3) 최종 결과(완료 시점 정보) 반환
        """
        # 1) 비디오/오디오를 합성(또는 싱크)하도록 요청
        initial_response = self.reqLibSync(video_url, audio_url)

        # 응답에서 id 추출
        generation_id = initial_response.get("id")
        if not generation_id:
            logger.error("No 'id' found in response from reqLibSync.")
            return None
        
        # 2) 특정 id가 COMPLETED 될 때까지 모니터링
        final_result = self.monitor_status(generation_id, poll_interval)
        
        # 3) 최종 완료 정보를 반환
        return final_result