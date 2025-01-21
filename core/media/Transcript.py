import os
import time
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from common.Logger import logger


class Transcript:
    """
    AWS Transcribe를 통해 S3에 있는 음성/영상 파일을 텍스트로 변환하는 클래스.
    비동기 잡을 생성한 뒤, 잡 상태를 폴링하여 결과(Transcript) 경로를 가져온다.
    """

    def __init__(self, audio_path: str = None):
        # boto3 client 생성
        self.transcribe_client = boto3.client(
            'transcribe',
            region_name='ap-northeast-2',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.audio_s3key = self._upload_to_s3(audio_path, 
                                              os.getenv('AWS_BUCKET_NAME'), 
                                              os.path.basename(audio_path))
        self.generated_transcription_s3key = ''
        self.job_name = ''

    def _upload_to_s3(self, local_file_path: str, bucket_name: str, key: str) -> str:
        """
        로컬 파일을 S3에 업로드한다.
        :param local_file_path: 로컬 파일 경로
        :param bucket_name: S3 버킷 이름
        :param key: S3 키(파일 경로)
        :return: 업로드가 성공하면 s3://bucket_name/key 형태의 URI 문자열, 실패하면 None
        """
        s3 = boto3.client('s3')

        try:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            key = f"{os.getenv('AWS_BASE_TRANSCRIPT_DIR')}/{os.path.basename(local_file_path)}"
            s3.upload_file(local_file_path, bucket_name, key)
            logger.info(f"Uploaded to S3: s3://{bucket_name}/{key}")

            self.audio_s3key = key
            return f"s3://{bucket_name}/{key}"
        except ClientError as e:
            print(f"Error uploading to S3: {str(e)}")
            return None

    def _start_transcription_job(self):
        """
        새 Transcribe 잡을 생성한다.
        :param job_name: 유니크한 잡 이름
        :param media_file_uri: S3 URI (s3://bucket/yourfile.mp3 등)
        :param media_format: 'mp3', 'mp4', 'wav', 'flac' 등
        :param language_code: 기본 'ko-KR' (한국어)
        :param output_bucket_name: (선택) 결과물(Transcript json) 저장할 버킷
        :param output_key: (선택) 결과물 저장 경로/접두사
        """
        self.job_name = datetime.now().strftime('transcript_%Y%m%d_%H%M%S')
        output_bucket_name = os.getenv('AWS_BUCKET_NAME')
        # Transcribe에 전달할 파라미터 구성
        params = {
            "TranscriptionJobName": self.job_name,
            "LanguageCode": 'ko-KR',
            "MediaFormat": 'mp3',
            "Media": {
                "MediaFileUri": self.audio_s3key
            }
        }

        output_bucket_name = os.getenv('AWS_BUCKET_NAME')
        output_key = f"{os.getenv('AWS_BASE_TRANSCRIPT_DIR')}/{self.job_name}.json"
        # 만약 결과물을 특정 S3 버킷/key에 저장하고 싶다면:
        if output_bucket_name:
            params["OutputBucketName"] = output_bucket_name
            if output_key:
                params["OutputKey"] = output_key
                self.generated_transcription_s3key = f"s3://{output_bucket_name}/{output_key}"

        # 잡 생성
        try:
            response = self.transcribe_client.start_transcription_job(**params)
            logger.info(f"Transcription job started: {response}")
            return response
        except ClientError as e:
            logger.error(f"Transcription job start error: {str(e)}")
            return None

    def get_transcription_job_status(self):
        """
        특정 job_name의 상태를 가져온다.
        :return: { 'TranscriptionJobName': ..., 'TranscriptionJobStatus': 'IN_PROGRESS'|'FAILED'|'COMPLETED', ...}
        """
        try:
            response = self.transcribe_client.get_transcription_job(
                TranscriptionJobName=self.job_name
            )
            return response.get('TranscriptionJob', {})
        except ClientError as e:
            print(f"Error getting job status: {str(e)}")
            return {}

    def wait_for_completion(self, job_name: str, poll_interval=30, timeout=3600):
        """
        job_name에 해당하는 Transcribe 잡이 COMPLETED 혹은 FAILED 될 때까지 폴링.
        :param job_name: 잡 이름
        :param poll_interval: 폴링 주기(초)
        :param timeout: 최대 대기 시간(초)
        :return: 최종 job status dict (COMPLETED or FAILED)
        """
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.info(f"Transcription job {job_name} timed out after {timeout} seconds.")
                return None

            job_info = self.get_transcription_job_status(job_name)
            status = job_info.get('TranscriptionJobStatus')
            if not status:
                logger.info("No job status found, waiting...")
            elif status == 'COMPLETED':
                logger.info(f"Job {job_name} completed.")
                return job_info
            elif status == 'FAILED':
                logger.info(f"Job {job_name} failed.")
                return job_info
            else:
                logger.info(f"Job {job_name} status: {status}, waiting...")

            time.sleep(poll_interval)

    def fetch_transcript(
        self,
        transcription_job_info: dict
    ) -> dict:
        """
        TranscriptionJobInfo에서 TranscriptFileUri를 파싱하여,
        해당 JSON을 다운로드 & 파싱.
        :param transcription_job_info: wait_for_completion() 반환된 job info
        :return: transcript JSON 파싱 결과
        """
        if not transcription_job_info:
            logger.info("No job info to fetch transcript.")
            return {}

        status = transcription_job_info.get("TranscriptionJobStatus")
        if status != "COMPLETED":
            logger.info(f"Cannot fetch transcript, job status is {status}")
            return {}

        transcript_uri = transcription_job_info.get("Transcript", {}).get("TranscriptFileUri")
        if not transcript_uri:
            logger.info("No TranscriptFileUri found.")
            return {}

        # TranscriptFileUri는 S3 presigned URL 형태
        # requests로 GET
        import requests
        try:
            r = requests.get(transcript_uri)
            if r.status_code == 200:
                data = r.json()
                return data
            else:
                logger.error(f"Error fetching transcript: {r.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Failed to fetch transcript: {e}")
            return {}

    def transcribe_and_get_srt(self) -> str:
        """
        편의 메서드:
          1) start_transcription_job
          2) wait_for_completion
          3) fetch_transcript
          4) SRT로 변환하여 문자열 반환 (실제 파일 저장은 사용자 몫)

        :return: srt_str
        """
        # 1) 잡 생성
        _ = self._start_transcription_job()

        # 2) 폴링
        job_info = self.wait_for_completion(self.job_name)
        if not job_info:
            return ""

        status = job_info.get('TranscriptionJobStatus')
        if status != 'COMPLETED':
            logger.info(f"Job finished with status={status}, cannot produce SRT.")
            return ""

        # 3) transcript fetch
        data = self.fetch_transcript(job_info)
        # AWS Transcribe의 JSON 구조:
        # {
        #   "results": {
        #     "transcripts": [{"transcript": "..."}],
        #     "items": [
        #       {
        #         "start_time": "1.23",
        #         "end_time": "2.34",
        #         "alternatives": [{"content":"Hello","confidence":"0.9"}],
        #         "type":"pronunciation"
        #       },
        #       ...
        #     ]
        #   }
        #   ...
        # }
        results = data.get("results", {})
        items = results.get("items", [])

        # 4) SRT 변환
        srt_str = self._convert_to_srt(items)
        return srt_str

    def _convert_to_srt(self, items: list) -> str:
        """
        AWS Transcribe 항목 -> SRT 형식으로 변환.
        아주 단순하게, 'punctuation'을 만나면 문장 끝으로 치고,
        문장 단위 start_time~end_time은 첫 단어~마지막 단어 시각으로 계산

        실제로는 더욱 정교한 로직(문장부호, 일정 길이, etc)이 필요할 수 있음
        """
        import math

        # 임시 구조:
        # 문장 = [ (start, end, text) ]
        subtitles = []
        current_sentence_words = []
        sentence_start = None

        def srt_timestamp(seconds_float):
            hours = int(seconds_float // 3600)
            mins = int((seconds_float % 3600) // 60)
            secs = int(seconds_float % 60)
            millis = int((seconds_float - math.floor(seconds_float)) * 1000)
            return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        for item in items:
            itype = item.get("type")
            start_time = item.get("start_time")
            end_time   = item.get("end_time")
            alternatives = item.get("alternatives",[{}])
            content = alternatives[0].get("content","")

            if itype == "pronunciation":
                # 단어
                st = float(start_time) if start_time else 0.0
                et = float(end_time)   if end_time else st
                if sentence_start is None:
                    sentence_start = st
                current_sentence_words.append((content, st, et))

            elif itype == "punctuation":
                # 문장부호 -> 여기서 문장 경계라고 가정
                # 예: '.', '?', '!'
                # sentence_start ~ 마지막 단어 end_time
                if current_sentence_words:
                    # 문장 시작 ~ 문장 끝
                    start_st = sentence_start
                    end_et = current_sentence_words[-1][2]
                    text_str = " ".join([w[0] for w in current_sentence_words]) + content
                    subtitles.append((start_st, end_et, text_str))
                    current_sentence_words = []
                    sentence_start = None
                else:
                    # 문장부호만 나왔으면 무시
                    pass

        # 끝에 남은 단어가 있으면 문장으로 처리
        if current_sentence_words:
            start_st = sentence_start if sentence_start else 0
            end_et = current_sentence_words[-1][2]
            text_str = " ".join([w[0] for w in current_sentence_words])
            subtitles.append((start_st, end_et, text_str))

        # 이제 subtitles = [(start, end, "문장"), ...]
        # SRT로 변환
        srt_lines = []
        for i, (st, et, txt) in enumerate(subtitles, start=1):
            start_s = srt_timestamp(st)
            end_s   = srt_timestamp(et)
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_s} --> {end_s}")
            srt_lines.append(txt)
            srt_lines.append("")  # blank line

        return "\n".join(srt_lines)