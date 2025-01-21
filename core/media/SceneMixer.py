import os

from moviepy import (
    VideoFileClip,
    ImageClip,
    AudioFileClip,
    CompositeVideoClip
)

from common.Logger import logger
from common.Paths import Paths

class SceneMixer:
    def __init__(self, video, audio, images):
        # video : video path
        # audio : audio path
        # images : list of image paths
        if not os.path.isfile(video):
            raise FileNotFoundError(f"비디오 파일을 찾을 수 없습니다: {video}")
        if not os.path.isfile(audio):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio}")
        for img in images:
            if not os.path.isfile(img):
                raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {img}")
            
        # 로드
        self.video_clip = VideoFileClip(video)
        self.audio_clip = AudioFileClip(audio)
        self.image_paths = images

        # 비디오 총 길이(초)
        self.video_duration = self.video_clip.duration
        # 오디오 총 길이(초)
        self.audio_duration = self.audio_clip.duration

    def create_edited_video(self, output_path: str = ''):
        """
        - 최종 영상 길이 = 오디오 길이 (audio_duration)
        - 이미지가 0개면 비디오+오디오 (영상은 audio_duration까지, 부족하면 반복(loop))
        - 이미지가 N개면:
          total_segments = 2*N + 1
          segment_len = audio_duration / total_segments
          => 비디오 segment_len씩 N+1개 (loop로 부족분 채움),
             이미지 segment_len씩 N개
          => 번갈아(concat) => 최종 영상
        """
        if not output_path:
            # output_path = self.getNewMediaPath(ext='mp4')
            output_path = Paths.get_scenemixed_video()

        final_duration = self.audio_duration  # 오디오 길이에 맞춤
        N = len(self.image_paths)

        # =========== 이미지가 없을 경우 ===========
        if N == 0:
            logger.info(f"이미지가 없으므로 비디오+오디오만 사용합니다.")
            sub_video = self._get_subclip_with_loop(0, final_duration)
            
            if self.audio_duration >= final_duration:
                sub_audio = self.audio_clip.subclip(0, final_duration)
            else:
                sub_audio = self.audio_clip  # 여기서는 거의 없을 시나리오

            merged = sub_video.set_audio(sub_audio)
            merged.write_videofile(output_path, codec="libx264", audio_codec="aac")

            sub_video.close()
            merged.close()
            return output_path

        # =========== 이미지가 1개 이상인 경우 ===========
        segment_count = 2*N + 1
        segment_len = final_duration / segment_count
        segments = []
        final_sequence = []
        images = self.image_paths.copy()
        for i in range(N):
            segments.append('video')
            segments.append('image')
        segments.append('video')

        for i, seg in enumerate(segments):
            if seg == 'video':
                start_t = i * segment_len
                end_t = (i+1) * segment_len
                if end_t > final_duration:
                    end_t = final_duration

                clip = self._get_subclip_with_loop(start_t, end_t)
                final_sequence.append(clip)
            else:
                iclip = ImageClip(images.pop(0))
                iclip.duration = segment_len
                final_sequence.append(iclip)

        # merged_clips = concatenate_videoclips(final_sequence, method="compose")
        merged_clips = CompositeVideoClip(final_sequence)
        # merged_clips = merged_clips.set_audio(self.audio_clip)
        merged_clips.audio = self.audio_clip
        merged_clips.duration = final_duration

        merged_clips.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=0)

        # 자원 해제
        merged_clips.close()
        for c in final_sequence:
            c.close()

        logger.info(f"최종 Scene Mix 영상 생성 완료: {output_path}")

        return output_path

    def _get_subclip_with_loop(self, start_t: float, end_t: float):
        """
        비디오를 (end_t - start_t) 길이만큼 잘라서 사용.
        만약 원본 비디오가 부족하면 (반복)으로 이어붙인다.
        
        ex) 원본 10초, 필요한 길이 13초 => 
          1) 10초(0~10) + 3초(0~3) => concat
        """
        needed_duration = end_t - start_t
        if needed_duration <= 0:
            # 0초 클립 리턴
            return self.video_clip[0, 0]

        # 목표: needed_duration 만큼을 비디오(루프)로 구성
        clips = []
        leftover = needed_duration
        video_len = self.video_duration

        # 루프를 시작할 때, 원본 비디오에서 start_t 지점~끝까지 우선 사용
        current_start = start_t % video_len  # 만약 start_t가 video_len보다 클 수도 있으니
        while leftover > 0:
            # 이번에 쓸 subclip 끝 위치
            current_end = min(video_len, current_start + leftover)
            # sub = self.video_clip.subclip(current_start, current_end)
            sub = self.video_clip[current_start:current_end]
            sub_duration = sub.duration
            clips.append(sub)

            leftover -= sub_duration
            sub.close()

            if leftover <= 0:
                break

            # 한 바퀴 loop -> 다시 비디오 처음(0초)부터 사용
            current_start = 0.0

        # 모든 clips를 합쳐 하나의 클립으로
        final_clip = CompositeVideoClip(clips)
        # final_clip = final_clip.set_duration(needed_duration)
        final_clip = final_clip.with_duration(needed_duration)
        # 혹시 float 오차가 있으면 정확히 needed_duration로 set
        final_clip = final_clip.with_duration(needed_duration)
        return final_clip