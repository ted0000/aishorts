import os
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

class S3Uploader:
    """
    S3Uploader 클래스:
    
    1) upload:
       - 특정 디렉토리(또는 경로)에 있는 파일을 S3에 업로드합니다.
       - 업로드 후 S3 object key(또는 경로)를 반환.
    2) gen_presigned_url:
       - 업로드된 object_name을 기반으로 프리사인드 URL을 생성해 반환 (기본 1시간 만료)
    3) upload_presigned_url:
       - 파일을 업로드한 뒤, 그 object_name으로 곧바로 presigned URL을 생성하고 return
    4) download:
       - S3에서 특정 object를 지정된 로컬 경로에 다운로드
    """
    def __init__(self):
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')  # 고정 버킷 이름
        self.base_dir = os.getenv('AWS_BASE_MEDIA_DIR')
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region_name="ap-northeast-2"  # 필요 시 변경

        self.s3_client = boto3.client(
            "s3",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url='https://s3.ap-northeast-2.amazonaws.com'
        )

    def upload_av(self, audio_path: str, video_path: str, duration:float=0, s3_key: str = None) -> dict:
        """
        오디오와 비디오 파일을 S3에 업로드하고, presigned URL을 생성하여 반환
        
        :param audio_path: 업로드할 오디오 파일 경로
        :param video_path: 업로드할 비디오 파일 경로
        :param s3_key: S3 업로드 시 사용할 object key (경로). None이면 파일명으로 사용
        :return: {"audio": {"object_key": s3_key, "presigned_url": url},
                  "video": {"object_key": s3_key, "presigned_url": url}}
        """
        audio_info = self.upload_presigned_url(audio_path, duration, s3_key=s3_key)
        video_info = self.upload_presigned_url(video_path, duration, s3_key=s3_key)
        
        return {"audio": audio_info, "video": video_info}
    
    def _get_new_media_path(self, duration=0, ext='mp3'):
        # 현재 날짜와 시간 가져오기
        now = datetime.now()
        date_str = now.strftime("%Y/%m")
        datetime_str = now.strftime("%Y%m%d_%H%M")
        
        # 새로운 파일 경로 생성
        new_file_name = f"{date_str}/{datetime_str}_{int(duration)}Sec.{ext}"
        return new_file_name

    def upload(self, file_path: str, duration, s3_key: str = None) -> str:
        """
        지정된 파일을 S3에 업로드합니다.
        
        :param file_path: 업로드할 로컬 파일 경로
        :param s3_key: S3 업로드 시 사용할 object key (경로). None이면 파일명으로 사용
        :return: 업로드된 object key (S3 상의 경로)
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if s3_key is None:
            # s3_key = 'media/' + os.path.basename(file_path)
            ext = Path(file_path).suffix[1:]
            s3_key = self._get_new_media_path(duration=duration, ext=ext)

        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
        except ClientError as e:
            raise RuntimeError(f"S3 upload failed: {e}")

        return s3_key

    def gen_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """
        해당 object_name (S3 상의 key)에 대한 presigned URL을 반환
        presined url은 완전 public한 url을 expiration 시간만큼 제한하여 사용 가능하게 합니다.

        :param object_name: S3에 업로드된 파일의 key
        :param expiration: URL 만료 시간(초), 기본 3600(1시간)
        :return: presigned URL (str)
        """
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration
            )
        except ClientError as e:
            raise RuntimeError(f"Presigned URL generation failed: {e}")

        return response

    def upload_presigned_url(self, file_path: str, duration: float, s3_key: str = None, expiration: int = 3600) -> dict:
        """
        1) 파일을 S3에 업로드
        2) 업로드된 object key로 presigned URL을 생성
        3) object key, presigned URL을 리턴
        
        :param file_path: 업로드할 로컬 파일 경로
        :param s3_key: S3 상에서 사용할 key (경로). 미지정 시 로컬 파일명 사용
        :param expiration: presigned URL 만료 시간(초)
        :return: {"object_key": s3_key, "presigned_url": url}
        """
        # 1) upload
        key = self.upload(file_path, duration, s3_key=s3_key)
        
        # 2) generate presigned URL
        url = self.gen_presigned_url(key, expiration=expiration)
        
        return {"object_key": key, "presigned_url": url}

    def download(self, object_name: str, download_path: str):
        """
        S3에 있는 object_name을 로컬로 다운로드합니다.
        
        :param object_name: S3 상의 파일 key
        :param download_path: 다운로드할 로컬 파일 경로
        """
        try:
            self.s3_client.download_file(self.bucket_name, object_name, download_path)
        except ClientError as e:
            raise RuntimeError(f"S3 download failed: {e}")