import logging
import os
import colorlog
from datetime import datetime

class Logger:
    def __init__(
        self,
        root_dir="logs",
        enable_file_logging=False
    ):
        """
        로그 클래스 초기화

        :param root_dir: 로그를 저장할 기본 디렉토리 (예: "logs")
        :param enable_file_logging: 파일로 로그를 저장할지 여부 (기본값: True)
        """
        self.root_dir = root_dir
        self.enable_file_logging = enable_file_logging
        self._setup_logger()

    def _setup_logger(self):
        """
        로거를 설정하는 내부 메서드
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # 콘솔용 색상 핸들러 설정
        log_format = '[%(levelname)s]%(asctime)s - %(message)s'
        color_handler = colorlog.StreamHandler()
        color_handler.setLevel(logging.DEBUG)
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s[%(levelname)s]%(reset)s %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red'
            }
        )
        color_handler.setFormatter(color_formatter)
        self.logger.addHandler(color_handler)

        # 파일 로깅 활성화 여부
        if self.enable_file_logging:
            now = datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%m")
            day = now.strftime("%d")

            # Apache 스타일: access_log-20250109-130045.log
            # (오늘 날짜가 2025년 1월 9일 13:00:45라 가정 시)
            log_filename = f'aishorts-{now.strftime("%Y%m%d-%H%M%S")}.log'

            # 최종 로그 파일 경로: root_dir/logs/YYYY/MM/DD/access_log-YYYYmmdd-HHMMSS.log
            log_dir_path = os.path.join(self.root_dir, year, month, day)
            os.makedirs(log_dir_path, exist_ok=True)

            log_file_path = os.path.join(log_dir_path, log_filename)

            # 파일 핸들러 설정
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                log_format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)

            self.logger.addHandler(file_handler)

    def debug(self, message):
        """디버그 메시지 로그"""
        self.logger.debug(message)

    def info(self, message):
        """정보 메시지 로그"""
        self.logger.info(message)

    def warning(self, message):
        """경고 메시지 로그"""
        self.logger.warning(message)

    def error(self, message):
        """에러 메시지 로그"""
        self.logger.error(message)

    def critical(self, message):
        """치명적인 에러 메시지 로그"""
        self.logger.critical(message)


logger = Logger()
