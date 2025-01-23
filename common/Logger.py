import logging
import os
import colorlog
from datetime import datetime


class Logger:
    """
    로그 클래스 초기화 및 설정.
    
    :param root_dir: 로그를 저장할 기본 디렉토리 (기본값: "logs").
    :param enable_file_logging: 파일로 로그를 저장할지 여부 (기본값: False).
    """
    _is_initialized = False

    def __init__(self, root_dir: str = "logs", enable_file_logging: bool = False):
        self.root_dir = root_dir
        self.enable_file_logging = enable_file_logging
        self.logger = logging.getLogger()
        
        if not Logger._is_initialized:
            self._setup_logger()
            Logger._is_initialized = True

    def _setup_logger(self):
        """
        로거에 콘솔 및 파일 핸들러를 설정하는 내부 메서드.
        """
        self.logger.setLevel(logging.DEBUG)

        # 콘솔용 색상 핸들러 설정
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s[%(levelname)s] %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red'
            }
        )
        color_handler = colorlog.StreamHandler()
        color_handler.setLevel(logging.DEBUG)
        color_handler.setFormatter(color_formatter)
        self.logger.addHandler(color_handler)

        # 파일 로깅 활성화 여부
        if self.enable_file_logging:
            try:
                now = datetime.now()
                log_filename = f'aishorts-{now.strftime("%Y%m%d-%H%M%S")}.log'
                log_dir_path = os.path.join(self.root_dir, now.strftime("%Y/%m/%d"))
                os.makedirs(log_dir_path, exist_ok=True)

                log_file_path = os.path.join(log_dir_path, log_filename)

                file_formatter = logging.Formatter(
                    '[%(levelname)s] %(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler = logging.FileHandler(log_file_path)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.error(f"Logger: 파일 핸들러 설정 중 오류 발생: {e}")

    def debug(self, message: str):
        """디버그 메시지 로그"""
        self.logger.debug(message)

    def info(self, message: str):
        """정보 메시지 로그"""
        self.logger.info(message)

    def warning(self, message: str):
        """경고 메시지 로그"""
        self.logger.warning(message)

    def error(self, message: str):
        """에러 메시지 로그"""
        self.logger.error(message)

    def critical(self, message: str):
        """치명적인 에러 메시지 로그"""
        self.logger.critical(message)


# 전역 logger 인스턴스 생성
# 파일 로깅을 활성화하려면 enable_file_logging=True로 설정하세요.
logger = Logger(enable_file_logging=False).logger