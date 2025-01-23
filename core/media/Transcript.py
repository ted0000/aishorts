import os
import time
from datetime import datetime
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError
import requests

from common.Logger import logger


class Transcript:
    """
    AWS Transcribe를 통해 S3에 있는 음성/영상 파일을 텍스트로 변환하는 클래스.
    비동기 잡을 생성한 뒤, 잡 상태를 폴링하여 결과(Transcript) 경로를 가져옵니다.
    """

    SUPPORTED_MEDIA_FORMATS = {
        ".mp3": "mp3",
        ".mp4": "mp4",
        ".wav": "wav",
        ".m4a": "m4a",
        ".flac": "flac"
    }

    def __init__(self, audio_path: Optional[str] = None):
        """
        Transcript 초기화 메서드.

        :param audio_path: 편집할 미디어(오디오/비디오) 파일의 로컬 경로. None이면 업로드하지 않음.
        """
        self.transcribe_client = boto3.client(
            'transcribe',
            region_name='ap-northeast-2',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        self.base_transcript_dir = os.getenv('AWS_BASE_TRANSCRIPT_DIR', 'transcripts')

        if not self.bucket_name:
            logger.error("Transcript: AWS_BUCKET_NAME 환경 변수가 설정되지 않았습니다.")
            raise ValueError("Transcript: AWS_BUCKET_NAME 환경 변수가 설정되지 않았습니다.")

        self.audio_s3key: Optional[str] = None
        self.generated_transcription_s3key: Optional[str] = None
        self.job_name: Optional[str] = None

        if audio_path:
            self.audio_s3key = self._upload_to_s3(audio_path)
            logger.info(f"Transcript: Audio 파일이 S3에 업로드되었습니다: {self.audio_s3key}")

    def _upload_to_s3(self, local_file_path: str) -> str:
        """
        로컬 파일을 S3에 업로드합니다.

        :param local_file_path: 업로드할 로컬 파일 경로.
        :return: 업로드된 S3 object key.
        """
        if not os.path.isfile(local_file_path):
            logger.error(f"Transcript: 파일을 찾을 수 없습니다: {local_file_path}")
            raise FileNotFoundError(f"Transcript: 파일을 찾을 수 없습니다: {local_file_path}")

        ext = os.path.splitext(local_file_path.lower())[1]
        if ext not in self.SUPPORTED_MEDIA_FORMATS:
            logger.error(f"Transcript: 지원하지 않는 파일 형식입니다: {ext}")
            raise ValueError(f"Transcript: 지원하지 않는 파일 형식입니다: {ext}")

        object_key = f"{self.base_transcript_dir}/{os.path.basename(local_file_path)}"
        s3_client = boto3.client('s3')

        try:
            s3_client.upload_file(local_file_path, self.bucket_name, object_key)
            logger.info(f"Transcript: S3에 파일 업로드 성공: s3://{self.bucket_name}/{object_key}")
        except ClientError as e:
            logger.error(f"Transcript: S3 업로드 실패: {e}")
            raise RuntimeError(f"Transcript: S3 업로드 실패: {e}")

        return object_key

    def _start_transcription_job(self, media_format: str = "mp3", language_code: str = "ko-KR") -> Optional[Dict[str, Any]]:
        """
        새로운 Transcribe 잡을 생성합니다.

        :param media_format: 미디어 파일 형식 (예: 'mp3', 'mp4').
        :param language_code: 언어 코드 (기본값 'ko-KR').
        :return: 잡 생성 응답. 실패 시 None.
        """
        if not self.audio_s3key:
            logger.error("Transcript: S3에 업로드된 오디오 키가 없습니다.")
            raise RuntimeError("Transcript: S3에 업로드된 오디오 키가 없습니다.")

        self.job_name = datetime.now().strftime('transcript_%Y%m%d_%H%M%S')
        output_key = f"{self.base_transcript_dir}/{self.job_name}.json"

        params = {
            "TranscriptionJobName": self.job_name,
            "LanguageCode": language_code,
            "MediaFormat": media_format,
            "Media": {
                "MediaFileUri": f"s3://{self.bucket_name}/{self.audio_s3key}"
            },
            "OutputBucketName": self.bucket_name,
            "OutputKey": output_key
        }

        try:
            response = self.transcribe_client.start_transcription_job(**params)
            self.generated_transcription_s3key = f"s3://{self.bucket_name}/{output_key}"
            logger.info(f"Transcript: Transcription 잡 시작: {self.job_name}")
            return response
        except ClientError as e:
            logger.error(f"Transcript: Transcription 잡 시작 실패: {e}")
            return None

    def get_transcription_job_status(self, job_name: str) -> Dict[str, Any]:
        """
        특정 Transcription 잡의 상태를 가져옵니다.

        :param job_name: 잡 이름.
        :return: 잡 상태 정보 딕셔너리.
        """
        try:
            response = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            logger.info(f"Transcript: 잡 상태 조회 성공: {job_name}")
            return response.get('TranscriptionJob', {})
        except ClientError as e:
            logger.error(f"Transcript: 잡 상태 조회 실패: {e}")
            return {}

    def wait_for_completion(self, job_name: str, poll_interval: int = 30, timeout: int = 3600) -> Optional[Dict[str, Any]]:
        """
        Transcription 잡이 COMPLETED 또는 FAILED 상태가 될 때까지 폴링합니다.

        :param job_name: 잡 이름.
        :param poll_interval: 폴링 주기 (초).
        :param timeout: 최대 대기 시간 (초).
        :return: 최종 잡 상태 정보 딕셔너리. 타임아웃 시 None.
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.warning(f"Transcript: Transcription 잡 {job_name}이(가) {timeout}초 후에 타임아웃되었습니다.")
                return None

            job_info = self.get_transcription_job_status(job_name)
            status = job_info.get('TranscriptionJobStatus')

            if status == 'COMPLETED':
                logger.info(f"Transcript: Transcription 잡 {job_name}이(가) 완료되었습니다.")
                return job_info
            elif status == 'FAILED':
                logger.error(f"Transcript: Transcription 잡 {job_name}이(가) 실패하였습니다.")
                return job_info
            else:
                logger.info(f"Transcript: Transcription 잡 {job_name} 상태: {status}. 대기 중...")

            time.sleep(poll_interval)

    def fetch_transcript(self, transcription_job_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transcription 잡 정보에서 TranscriptFileUri를 파싱하여 JSON을 다운로드 및 파싱합니다.

        :param transcription_job_info: Transcription 잡 정보 딕셔너리.
        :return: Transcript JSON 파싱 결과. 실패 시 None.
        """
        if not transcription_job_info:
            logger.warning("Transcript: Transcript를 가져올 잡 정보가 없습니다.")
            return None

        status = transcription_job_info.get("TranscriptionJobStatus")
        if status != "COMPLETED":
            logger.warning(f"Transcript: 잡 상태가 COMPLETED가 아닙니다: {status}")
            return None

        transcript_uri = transcription_job_info.get("Transcript", {}).get("TranscriptFileUri")
        if not transcript_uri:
            logger.warning("Transcript: TranscriptFileUri가 없습니다.")
            return None

        try:
            response = requests.get(transcript_uri)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Transcript: Transcript JSON 다운로드 성공: {transcript_uri}")
            return data
        except requests.RequestException as e:
            logger.error(f"Transcript: Transcript JSON 다운로드 실패: {e}")
            return None
        except ValueError as e:
            logger.error(f"Transcript: Transcript JSON 파싱 실패: {e}")
            return None

    def transcribe_and_get_srt(self) -> Optional[str]:
        """
        전체 Transcription 프로세스를 수행하고 SRT 형식의 문자열을 반환합니다.

        :return: SRT 문자열. 실패 시 None.
        """
        # 1. Transcription 잡 시작
        transcription_response = self._start_transcription_job()
        if not transcription_response:
            logger.error("Transcript: Transcription 잡 시작에 실패하였습니다.")
            return None

        # 2. 잡 완료 대기
        job_info = self.wait_for_completion(self.job_name)
        if not job_info:
            logger.error("Transcript: Transcription 잡이 완료되지 않았습니다.")
            return None

        status = job_info.get('TranscriptionJobStatus')
        if status != 'COMPLETED':
            logger.error(f"Transcript: Transcription 잡이 {status} 상태로 완료되었습니다.")
            return None

        # 3. Transcript JSON 가져오기
        transcript_data = self.fetch_transcript(job_info)
        if not transcript_data:
            logger.error("Transcript: Transcript 데이터를 가져오지 못했습니다.")
            return None

        # 4. SRT 변환
        srt_str = self._convert_to_srt(transcript_data.get("results", {}).get("items", []))
        if not srt_str:
            logger.error("Transcript: SRT 변환에 실패하였습니다.")
            return None

        logger.info("Transcript: Transcript를 SRT 형식으로 변환하였습니다.")
        return srt_str

    def _convert_to_srt(self, items: list) -> Optional[str]:
        """
        AWS Transcribe 항목을 SRT 형식으로 변환합니다.

        :param items: Transcribe 결과의 'items' 리스트.
        :return: SRT 형식의 문자열. 실패 시 None.
        """
        import math

        subtitles = []
        current_sentence = []
        sentence_start: Optional[float] = None

        def srt_timestamp(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds - math.floor(seconds)) * 1000)
            return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

        for item in items:
            item_type = item.get("type")
            start_time = float(item.get("start_time", 0.0))
            end_time = float(item.get("end_time", 0.0))
            content = item.get("alternatives", [{}])[0].get("content", "")

            if item_type == "pronunciation":
                if sentence_start is None:
                    sentence_start = start_time
                current_sentence.append((content, start_time, end_time))
            elif item_type == "punctuation":
                if current_sentence:
                    sentence_end = current_sentence[-1][2]
                    sentence_text = " ".join([word[0] for word in current_sentence]) + content
                    subtitles.append((sentence_start, sentence_end, sentence_text))
                    current_sentence = []
                    sentence_start = None

        # 남아있는 단어 처리
        if current_sentence:
            sentence_end = current_sentence[-1][2]
            sentence_text = " ".join([word[0] for word in current_sentence])
            subtitles.append((sentence_start, sentence_end, sentence_text))

        if not subtitles:
            logger.warning("Transcript: SRT 변환을 위한 자막이 없습니다.")
            return None

        srt_lines = []
        for idx, (start, end, text) in enumerate(subtitles, start=1):
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{srt_timestamp(start)} --> {srt_timestamp(end)}")
            srt_lines.append(text)
            srt_lines.append("")  # 빈 줄

        srt_content = "\n".join(srt_lines)
        logger.info("Transcript: SRT 변환 완료.")
        return srt_content