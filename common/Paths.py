import os
import tempfile
from pathlib import Path
from typing import Optional

from common.Logger import logger


class Paths:
    """
    Paths 클래스는 프로젝트 내에서 사용되는 파일 및 디렉토리 경로를 관리합니다.
    """

    @staticmethod
    def get_scenemixed_video() -> Optional[str]:
        """
        Scene mixed 비디오 파일을 저장할 경로를 생성합니다.

        :return: 생성된 비디오 파일의 경로 문자열. 실패 시 None.
        """
        try:
            # 현재 작업 디렉토리 가져오기
            root = Path.cwd()
            logger.debug(f"Paths: 현재 작업 디렉토리: {root}")

            # 환경 변수에서 디렉토리 경로 가져오기 또는 기본값 사용
            dir_env = os.getenv("DIR_SCENE_MIXED_RESULT", "result/scene_mixed")
            dir_path = root / dir_env
            logger.debug(f"Paths: 대상 디렉토리 경로: {dir_path}")

            # 디렉토리 생성 (존재하지 않을 경우)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Paths: 디렉토리 생성 또는 존재 확인 완료: {dir_path}")

            # 임시 파일명 생성 (임시 디렉토리 내에서)
            temp_file = tempfile.mktemp(suffix=".mp4", dir=str(dir_path))
            logger.debug(f"Paths: 생성된 임시 비디오 파일 경로: {temp_file}")

            return temp_file
        except Exception as e:
            logger.error(f"Paths: Scene mixed 비디오 경로 생성 중 오류 발생: {e}")
            return None