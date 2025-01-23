import os
from datetime import datetime
from typing import Optional, Dict, Tuple, Union

from moviepy import VideoFileClip, AudioFileClip

from common.Logger import logger


class MediaEditor:
    """
    MediaEditor 클래스:
    
    1) Media 로드:
       - 지정된 경로의 미디어 파일을 로드합니다.
    2) 정보 조회:
       - 미디어 파일의 정보(재생 시간, FPS, 해상도 등)를 반환합니다.
    3) 미디어 자르기:
       - 지정된 시간까지만 미디어 파일을 잘라냅니다.
    4) 오디오 추출:
       - 비디오 파일에서 오디오를 추출하여 저장합니다.
    5) 오디오 형식 변환:
       - 오디오 파일의 형식을 변환하여 저장합니다.
    """

    SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
    SUPPORTED_AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav"}

    def __init__(self, media_path: str):
        """
        MediaEditor 초기화 메서드.

        :param media_path: 편집할 미디어(오디오/비디오) 파일의 경로
        """
        self.path = media_path
        self.clip: Optional[Union[VideoFileClip, AudioFileClip]] = None
        self.is_video: bool = False

        self._load_media()

    def __del__(self):
        if self.clip:
            self.clip.close()
            # logger.info("미디어 클립이 닫혔습니다.")

    def _load_media(self):
        """
        내부 메서드: 파일 확장자를 체크하고,
        VideoFileClip 또는 AudioFileClip으로 로드합니다.
        """
        if not os.path.exists(self.path):
            logger.error(f"파일을 찾을 수 없습니다: {self.path}")
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.path}")

        ext = os.path.splitext(self.path.lower())[1]

        try:
            if ext in self.SUPPORTED_VIDEO_EXTENSIONS:
                self.clip = VideoFileClip(self.path)
                self.is_video = True
                # logger.info(f"비디오 파일 로드 완료: {self.path}")
            elif ext in self.SUPPORTED_AUDIO_EXTENSIONS:
                self.clip = AudioFileClip(self.path)
                # logger.info(f"오디오 파일 로드 완료: {self.path}")
            else:
                logger.error(f"지원하지 않는 파일 형식입니다: {ext}")
                raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")
        except Exception as e:
            logger.error(f"미디어 파일 로드 중 오류 발생: {e}")
            raise

    def get_info(self) -> Dict[str, Union[float, Tuple[int, int], str]]:
        """
        미디어 정보 읽기:
         - 총 재생 시간(초)
         - 비디오의 경우 프레임 수, FPS, 해상도 등 추가 정보

        :return: 미디어 정보 딕셔너리
        """
        if self.clip is None:
            logger.error("미디어 클립이 로드되지 않았습니다.")
            raise RuntimeError("미디어 클립이 로드되지 않았습니다.")

        info = {
            "duration": self.clip.duration  # 초 단위 float
        }

        if self.is_video:
            info.update({
                "fps": self.clip.fps,
                "resolution": (self.clip.w, self.clip.h)  # (width, height)
            })
            # logger.info(f"비디오 정보: {info}")
        else:
            # 오디오 파일에 대한 추가 정보가 필요할 경우 여기에 추가
            # logger.info(f"오디오 정보: {info}")
            pass

        return info

    def get_new_media_path(self, ext: str = 'mp3', dirpath: Optional[str] = None) -> str:
        """
        새로운 파일 경로를 생성합니다.

        :param ext: 파일 확장자 (기본값 'mp3')
        :param dirpath: 저장할 디렉토리 경로. 지정하지 않으면 현재 작업 디렉토리를 사용
        :return: 생성된 파일 경로
        """
        if not dirpath:
            dirpath = os.getcwd()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"converted_{timestamp}.{ext}"
        file_path = os.path.join(dirpath, filename)

        # logger.info(f"새로운 미디어 경로 생성: {file_path}")
        return file_path

    def cut_duration(self, cutoff_seconds: float, output_path: Optional[str] = None) -> str:
        """
        미디어 파일을 'cutoff_seconds'초까지만 남기고 잘라낸 뒤 저장합니다.

        :param cutoff_seconds: 잘라낼 기준 초 (예: 30.0)
        :param output_path: 결과물을 저장할 파일 경로. 지정하지 않으면 자동 생성
        :return: 잘라낸 파일의 저장 경로
        """
        if self.clip is None:
            logger.error("미디어 클립이 로드되지 않았습니다.")
            raise RuntimeError("미디어 클립이 로드되지 않았습니다.")

        if cutoff_seconds <= 0:
            logger.error("잘라낼 초(cutoff_seconds)는 0보다 커야 합니다.")
            raise ValueError("잘라낼 초(cutoff_seconds)는 0보다 커야 합니다.")

        original_duration = self.clip.duration
        if cutoff_seconds >= original_duration:
            logger.info("원본 길이보다 짧거나 같으므로, 전체 미디어를 그대로 저장합니다.")
            cutoff_seconds = original_duration

        try:
            sub_clip = self.clip.subclipped(0, cutoff_seconds)
            # logger.info(f"미디어를 {cutoff_seconds}초까지 자름.")
        except Exception as e:
            logger.error(f"미디어 자르기 중 오류 발생: {e}")
            raise

        if not output_path:
            ext = 'mp4' if self.is_video else 'mp3'
            output_path = self.get_new_media_path(ext=ext)

        try:
            if self.is_video:
                sub_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
                logger.info(f"잘라낸 비디오 저장 완료: {output_path}")
            else:
                sub_clip.write_audiofile(output_path)
                logger.info(f"잘라낸 오디오 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"잘라낸 미디어 저장 중 오류 발생: {e}")
            raise
        finally:
            sub_clip.close()

        return output_path

    def extract_audio(self, output_path: str) -> str:
        """
        비디오인 경우, 오디오만 추출하여 mp3 파일로 저장합니다.

        :param output_path: 저장할 오디오 파일 경로. 지정하지 않으면 자동 생성
        :return: 저장된 오디오 파일의 경로
        """
        if not self.is_video:
            logger.error("비디오 파일이 아니므로 오디오 추출을 진행할 수 없습니다.")
            raise RuntimeError("비디오 파일이 아니므로 오디오 추출을 진행할 수 없습니다.")

        if self.clip is None:
            logger.error("미디어 클립이 로드되지 않았습니다.")
            raise RuntimeError("미디어 클립이 로드되지 않았습니다.")

        audio_clip = self.clip.audio
        if not audio_clip:
            logger.error("비디오에 오디오 트랙이 존재하지 않습니다.")
            raise RuntimeError("비디오에 오디오 트랙이 존재하지 않습니다.")

        try:
            audio_clip.write_audiofile(output_path)
            # logger.info(f"오디오 추출 및 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"오디오 추출 중 오류 발생: {e}")
            raise
        finally:
            audio_clip.close()

        return output_path

    def convert_audio_format(self, output_ext: str = 'mp3', output_path: Optional[str] = None) -> str:
        """
        오디오 클립을 다른 확장자(예: m4a -> mp3)로 변환해서 저장합니다.

        :param output_ext: 변환 후 확장자 (기본값 'mp3')
        :param output_path: 변환 후 파일 경로. 지정하지 않으면 자동 생성
        :return: 최종 저장된 파일 경로
        """
        if self.is_video:
            logger.error("비디오 파일이므로 이 함수로 변환할 수 없습니다. extract_audio를 사용하세요.")
            raise RuntimeError("비디오 파일이므로 이 함수로 변환할 수 없습니다. extract_audio를 사용하세요.")

        if self.clip is None:
            logger.error("오디오 클립이 로드되지 않았습니다.")
            raise RuntimeError("오디오 클립이 로드되지 않았습니다.")

        if not output_path:
            output_path = self.get_new_media_path(ext=output_ext)

        try:
            self.clip.write_audiofile(output_path)
            # logger.info(f"오디오 형식 변환 및 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"오디오 형식 변환 중 오류 발생: {e}")
            raise

        return output_path