import os
from datetime import datetime

from moviepy import VideoFileClip, AudioFileClip

class MediaEditor:
    def __init__(self, media_path: str):
        """
        :param media_path: 편집할 미디어(오디오/비디오) 파일의 경로
        """
        self.path = media_path
        self.clip = None     # 이후 로딩된 MoviePy clip 객체 (VideoFileClip 또는 AudioFileClip)
        self.is_video = False
        
        # 미디어 파일 로드
        self._load_media()

    def __del__(self):
        if self.clip:
            self.clip.close()

    def _load_media(self):
        """
        내부 메서드: 파일 확장자를 체크하고,
        VideoFileClip 또는 AudioFileClip으로 로드
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.path}")

        ext = os.path.splitext(self.path.lower())[1]
        # 단순 분류 (mp4 -> video, m4a/mp3 -> audio)
        # 필요 시 더 많은 확장자 대응 가능
        if ext == ".mp4":
            self.clip = VideoFileClip(self.path)
            self.is_video = True
        elif ext in (".m4a", ".mp3"):
            self.clip = AudioFileClip(self.path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")

    def get_info(self):
        """
        미디어 정보 읽기:
         - 총 재생 시간(초)
         - 비디오의 경우 프레임 수, FPS 등 추가 정보
        """
        info = {}

        if self.clip is None:
            raise RuntimeError("미디어 클립이 로드되지 않았습니다.")

        # 공통: 총 재생 시간
        duration = self.clip.duration  # 초 단위 float
        info["duration"] = duration

        if self.is_video:
            # VideoFileClip이라면, fps, size 등 확인 가능
            info["fps"] = self.clip.fps
            info["resolution"] = (self.clip.w, self.clip.h)  # (width, height)
        else:
            # 오디오 파일이라면, 필요한 경우 샘플레이트 등 추가
            pass

        return info
    
    def getNewMediaPath(self, ext: str = 'mp3', dirpath: str = '') -> str:
        # 만약 dirpath가 제공되지 않았다면, 현재 디렉토리를 사용
        if not dirpath:
            dirpath = os.getcwd()

        # 현재 시각을 'YYYYMMDD_HHMMSS' 형식으로 포맷
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 파일 이름 예시: "converted_20250109_130045.mp3"
        filename = f"converted_{timestamp}.{ext}"

        # 디렉토리와 파일 이름을 합쳐 최종 경로 생성
        file_path = os.path.join(dirpath, filename)
        return file_path

    def cut_duration(self, cutoff_seconds: float, output_path: str = ''):
        """
        미디어 파일을 'cutoff_seconds'초까지만 남기고 잘라낸 뒤 저장.
        :param cutoff_seconds: 잘라낼 기준 초(예: 30.0)
        :param output_path: 결과물을 저장할 파일 경로
        """
        if self.clip is None:
            raise RuntimeError("미디어 클립이 로드되지 않았습니다.")

        if cutoff_seconds <= 0:
            raise ValueError("잘라낼 초(cutoff_seconds)는 0보다 커야 합니다.")

        # 원본 길이와 비교
        original_duration = self.clip.duration
        if cutoff_seconds >= original_duration:
            # cutoff_seconds가 원본 길이 이상이면, 편집할 필요가 없음
            print("원본 길이보다 짧거나 같으므로, 전체 미디어를 그대로 저장합니다.")
            cutoff_seconds = original_duration

        # subclip(0, cutoff_seconds)를 이용해 앞부분만 남기기
        sub = self.clip.subclipped(0, cutoff_seconds)

        if output_path == '':
            output_path = self.getNewMediaPath(ext='mp4' if self.is_video else 'mp3')

        # 비디오일 경우
        if self.is_video:
            sub.write_videofile(output_path, codec="libx264", audio_codec="aac")
        else:
            # 오디오일 경우
            sub.write_audiofile(output_path)
        
        sub.close()
        return output_path

    def extract_audio(self, output_path: str):
        """
        비디오인 경우, 오디오만 추출하여 mp3 파일로 저장
        """
        if not self.is_video:
            raise RuntimeError("비디오 파일이 아니므로 오디오 추출을 진행할 수 없습니다.")

        if self.clip is None:
            raise RuntimeError("미디어 클립이 로드되지 않았습니다.")

        # VideoFileClip.audio 로 AudioFileClip 가져오기
        audio_clip = self.clip.audio
        if not audio_clip:
            raise RuntimeError("비디오에 오디오 트랙이 존재하지 않습니다.")

        # mp3 등 원하는 포맷으로 저장
        audio_clip.write_audiofile(output_path)
        audio_clip.close()

    def convert_audio_format(self, output_ext='mp3', output_path: str = '') -> str:
        """
        오디오 클립을 다른 확장자(예: m4a -> mp3)로 변환해서 저장.
        
        :param output_ext: 변환 후 확장자 (기본값 'mp3')
        :param output_path: 변환 후 파일 경로. 지정하지 않으면 자동 생성
        :return: 최종 저장된 파일 경로
        """
        # 비디오는 제외(이미 VideoFileClip이면, extract_audio 등 별도 처리)
        if self.is_video:
            raise RuntimeError("비디오 파일이므로 이 함수로 변환할 수 없습니다. extract_audio를 사용하세요.")

        if self.clip is None:
            raise RuntimeError("오디오 클립이 로드되지 않았습니다.")

        if not output_path:
            output_path = self.getNewMediaPath(ext=output_ext)

        # AudioFileClip → mp3 등 원하는 포맷으로 저장
        self.clip.write_audiofile(output_path)

        return output_path

