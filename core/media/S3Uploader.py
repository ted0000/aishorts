import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import boto3
from botocore.exceptions import ClientError

from common.Logger import logger


class S3Uploader:
    """
    S3Uploader 클래스:

    1) upload:
       - 특정 파일을 S3에 업로드하고, 업로드된 S3 object key를 반환합니다.
    2) gen_presigned_url:
       - S3 object key를 기반으로 프리사인드 URL을 생성해 반환합니다 (기본 1시간 만료).
    3) upload_presigned_url:
       - 파일을 업로드한 뒤, 프리사인드 URL을 생성하여 반환합니다.
    4) download:
       - S3에서 특정 object를 지정된 로컬 경로에 다운로드합니다.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        base_dir: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "ap-northeast-2",
        endpoint_url: Optional[str] = None
    ):
        """
        S3Uploader 초기화 메서드.

        :param bucket_name: S3 버킷 이름. 환경 변수 'AWS_BUCKET_NAME'을 우선 사용.
        :param base_dir: 기본 미디어 디렉토리. 환경 변수 'AWS_BASE_MEDIA_DIR'을 우선 사용.
        :param aws_access_key_id: AWS 접근 키 ID. 환경 변수 'AWS_ACCESS_KEY_ID'을 우선 사용.
        :param aws_secret_access_key: AWS 비밀 접근 키. 환경 변수 'AWS_SECRET_ACCESS_KEY'을 우선 사용.
        :param region_name: AWS 리전 이름. 기본값 'ap-northeast-2'.
        :param endpoint_url: S3 엔드포인트 URL. 기본값 None.
        """
        self.bucket_name = bucket_name or os.getenv('AWS_BUCKET_NAME')
        self.base_dir = base_dir or os.getenv('AWS_BASE_MEDIA_DIR')

        aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        endpoint_url = endpoint_url or 'https://s3.ap-northeast-2.amazonaws.com'

        if not self.bucket_name:
            logger.error("AWS_BUCKET_NAME 환경 변수가 설정되지 않았습니다.")
            raise ValueError("AWS_BUCKET_NAME 환경 변수가 설정되지 않았습니다.")

        self.s3_client = boto3.client(
            "s3",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url
        )

    def upload(
        self, file_path: str, duration: int=0, s3_key: Optional[str] = None
    ) -> str:
        """
        지정된 파일을 S3에 업로드합니다.

        :param file_path: 업로드할 로컬 파일 경로.
        :param duration: 파일의 지속 시간 (초).
        :param s3_key: S3 업로드 시 사용할 object key (경로). None이면 파일명을 사용.
        :return: 업로드된 object key (S3 상의 경로).
        """
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        if s3_key is None:
            ext = Path(file_path).suffix[1:]
            s3_key = self._get_new_media_path(duration, ext=ext)

        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            logger.info(f"파일 업로드 성공: {s3_key}")
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise RuntimeError(f"S3 upload failed: {e}")

        return s3_key

    def gen_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """
        해당 object_name (S3 상의 key)에 대한 presigned URL을 반환.

        :param object_name: S3에 업로드된 파일의 key.
        :param expiration: URL 만료 시간(초), 기본 3600 (1시간).
        :return: presigned URL (str).
        """
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration
            )
            logger.info(f"프리사인드 URL 생성 성공: {object_name}")
        except ClientError as e:
            logger.error(f"Presigned URL generation failed: {e}")
            raise RuntimeError(f"Presigned URL generation failed: {e}")

        return response

    def upload_presigned_url(
        self, file_path: str, duration: float, s3_key: Optional[str] = None, expiration: int = 3600
    ) -> Dict[str, str]:
        """
        파일을 업로드한 뒤, presigned URL을 생성하고 반환합니다.

        :param file_path: 업로드할 로컬 파일 경로.
        :param duration: 파일의 지속 시간 (초).
        :param s3_key: S3 상에서 사용할 key (경로). 미지정 시 로컬 파일명 사용.
        :param expiration: presigned URL 만료 시간(초).
        :return: {"object_key": s3_key, "presigned_url": url}.
        """
        key = self.upload(file_path, duration, s3_key=s3_key)
        url = self.gen_presigned_url(key, expiration=expiration)
        return {"object_key": key, "presigned_url": url}

    def upload_av(
        self, audio_path: str, video_path: str, presigned_duration: int = 600, s3_key: Optional[str] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        오디오와 비디오 파일을 S3에 업로드하고, presigned URL을 생성하여 반환합니다.

        :param audio_path: 업로드할 오디오 파일 경로.
        :param video_path: 업로드할 비디오 파일 경로.
        :param presigned_duration: 파일의 지속 시간 (초).
        :param s3_key: S3 업로드 시 사용할 object key (경로). None이면 파일명을 사용.
        :return: {
            "audio": {"object_key": s3_key, "presigned_url": url},
            "video": {"object_key": s3_key, "presigned_url": url}
        }.
        """
        audio_info = self.upload_presigned_url(audio_path, presigned_duration, s3_key=s3_key)
        video_info = self.upload_presigned_url(video_path, presigned_duration, s3_key=s3_key)
        return {"audio": audio_info, "video": video_info}
    
    def remove(self, object_name: str) -> None:
        """
        S3에서 object_name을 삭제합니다.

        :param object_name: S3 상의 파일 key.
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"S3 파일 삭제 성공: {object_name}")
        except ClientError as e:
            logger.error(f"S3 file deletion failed: {e}")
            raise RuntimeError(f"S3 file deletion failed: {e}")

    def download(self, object_name: str, download_path: str=None) -> None:
        """
        S3에 있는 object_name을 로컬로 다운로드합니다.

        :param object_name: S3 상의 파일 key.
        :param download_path: 다운로드할 로컬 파일 경로.
        """
        try:
            if download_path is None:
                logger.error("다운로드 경로가 지정되지 않았습니다.")
            self.s3_client.download_file(self.bucket_name, object_name, download_path)
            download_path = os.path.join(os.getcwd(), download_path)
            logger.info(f"S3에서 파일 다운로드 성공: {object_name} -> {download_path}")
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            raise RuntimeError(f"S3 download failed: {e}")
        return download_path

    def _get_new_media_path(self, duration: int=0, ext: str = 'mp3') -> str:
        """
        새로운 파일 경로를 생성합니다.

        :param duration: 파일의 지속 시간 (초).
        :param ext: 파일 확장자.
        :return: 새로운 S3 파일 경로.
        """
        now = datetime.now()
        date_str = now.strftime("%Y/%m")
        datetime_str = now.strftime("%Y%m%d_%H%M%S")
        new_file_name = f"{self.base_dir}/{date_str}/{datetime_str}_{duration}Sec.{ext}"
        return new_file_name