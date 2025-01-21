import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

class VideoText:
    def __init__(self, video_path: str):
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"동영상 파일을 찾을 수 없습니다: {video_path}")

        self.video_clip = VideoFileClip(video_path)
        self.video_duration = self.video_clip.duration

        # 상단 자막용
        self.top_text_clip = None

        # 하단 자막용 : [(start, end, text, fontsize, color), ...]
        self.bottom_subtitle_data = []

    def 상단자막(self, text: str, color='white', fontsize=50):
        """
        상단 자막 (동영상 전체 구간 동안 고정)
        :param text: 자막 내용
        :param color: 글자 색상
        :param fontsize: 글자 크기
        """
        # 전체 영상 길이만큼 고정 표시
        dur = self.video_duration

        txt_clip = (TextClip(txt=text,
                             fontsize=fontsize,
                             color=color,
                             method='caption')  # or 'label'
                    .set_position(("center", "top"))
                    .set_duration(dur)
                    .set_start(0)  # 처음부터 표시
                    )
        self.top_text_clip = txt_clip

    def 하단자막(self, sub_list: list):
        """
        하단 자막 : 시간이 지날수록 자막이 바뀌도록
        :param sub_list: [(start, end, text, fontsize, color), ...]
        """
        # 예: [(0,5,"안녕하세요",40,"white"), (5,10,"다음 자막",40,"yellow"), ...]
        self.bottom_subtitle_data = sub_list

    def make_final(self, output_path: str = "final_with_subtitles.mp4"):
        """
        실제 자막을 합성하여 최종 영상을 저장.
        CompositeVideoClip 사용 -> start=... offset/time을 통해 순차 표출.
        """
        base_clip = self.video_clip

        overlay_clips = []

        # 1) 상단 자막(고정)
        if self.top_text_clip:
            overlay_clips.append(self.top_text_clip)

        # 2) 하단 자막
        #   sub_list 각 항목: (start, end, text, fontsize, color)
        for item in self.bottom_subtitle_data:
            start_sec, end_sec, text, fsize, col = item
            if end_sec <= start_sec:
                continue

            segment_duration = end_sec - start_sec
            if segment_duration <= 0:
                continue

            # TextClip 생성
            sub_txtclip = (TextClip(txt=text,
                                    fontsize=fsize,
                                    color=col,
                                    method='label')
                           # 하단 위치
                           .set_position(("center", "bottom"))
                           # 이 자막이 표시될 시간(길이)
                           .set_duration(segment_duration)
                           # CompositeVideoClip에서 시작 시점
                           .set_start(start_sec)
                           )

            overlay_clips.append(sub_txtclip)

        # 3) CompositeVideoClip
        final_comp = CompositeVideoClip([base_clip, *overlay_clips],
                                        size=base_clip.size)
        # 전체 길이는 원본 비디오 길이
        final_comp = final_comp.set_duration(base_clip.duration)

        # 4) 결과 저장
        final_comp.write_videofile(output_path,
                                   codec="libx264",
                                   audio_codec="aac",
                                   threads=0)

        # 자원 해제
        final_comp.close()
        base_clip.close()
        if self.top_text_clip:
            self.top_text_clip.close()
        for c in overlay_clips:
            if hasattr(c, 'close'):
                c.close()

        print(f"자막 합성 영상 생성 완료: {output_path}")