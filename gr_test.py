import numpy as np
import gradio as gr
from typing import Optional

# AI 메시지 생성 함수
def generate_message(draft: str, draft_time: int) -> str:
    """
    사용자가 입력한 초안과 시간을 바탕으로 AI가 생성한 메시지를 반환합니다.
    
    Args:
        draft (str): 사용자가 입력한 초안 텍스트.
        draft_time (int): 사용자가 원하는 Shorts의 재생 시간 (초).
    
    Returns:
        str: AI가 생성한 메시지.
    """
    return f"AI로 생성된 메시지: {draft} (시간: {draft_time}초)"

# 비디오 생성 함수
def generate_video(shorts_text: str, video_file: Optional[gr.Video] = None) -> str:
    """
    사용자가 입력한 텍스트와 비디오 파일을 바탕으로 AI가 생성한 Shorts 비디오를 반환합니다.
    
    Args:
        shorts_text (str): Shorts 대사 텍스트.
        video_file (Optional[gr.Video]): 원본 비디오 파일.
    
    Returns:
        str: AI가 생성한 Shorts 비디오 정보.
    """
    return f"AI로 생성된 aiShorts: {shorts_text} (video: {video_file})"

# 음성 복제 함수
def voice_cloning(audio_file: Optional[gr.Audio] = None) -> str:
    """
    사용자가 제공한 음성 파일을 바탕으로 AI가 음성을 복제한 결과를 반환합니다.
    
    Args:
        audio_file (Optional[gr.Audio]): 입력 음성 파일.
    
    Returns:
        str: AI가 생성한 복제된 음성 정보.
    """
    # 실제 음성 복제 로직을 여기에 구현
    # 현재는 예시로 경고 메시지를 반환합니다.
    if audio_file is None:
        return "음성 파일이 업로드되지 않았습니다."
    return f"AI로 생성된 복제된 음성: {audio_file.name}"

# Gradio 인터페이스 설정
def create_gradio_interface():
    """
    Gradio 인터페이스를 생성하고 설정합니다.
    
    Returns:
        gr.Blocks: 설정된 Gradio 인터페이스.
    """
    with gr.Blocks() as demo:
        gr.Markdown("# aiShorts Playground")
        
        # 텍스트 생성 탭
        with gr.Tab("Text generation"):
            with gr.Row():
                draft_input = gr.Textbox(
                    lines=4,
                    label="Draft",
                    placeholder="Shorts 대사의 초안을 입력하세요."
                )
                with gr.Column():
                    draft_time_input = gr.Radio(
                        choices=[30, 60],
                        label="Time (Sec)",
                        type="value",
                        value=30  # 기본값 설정
                    )
                    draft_output = gr.Textbox(
                        lines=4,
                        label="Generated Message",
                        interactive=False
                    )
            generate_message_button = gr.Button("AI로 시간에 맞는 메시지 생성")
            generate_message_button.click(
                generate_message,
                inputs=[draft_input, draft_time_input],
                outputs=draft_output
            )
        
        # aiShorts 생성 탭
        with gr.Tab("aiShorts generation"):
            with gr.Row():
                shorts_text_input = gr.Textbox(
                    lines=2,
                    label="Shorts Text",
                    placeholder="Shorts 대사를 입력하세요."
                )
            with gr.Row():
                origin_video = gr.Video(
                    label="Origin Video Template",
                    height=350
                )
                with gr.Column():
                    origin_generated_video = gr.Video(
                        label="Generated Video",
                        height=350
                    )
            generate_video_button = gr.Button("AI로 aiShorts 생성")
            generate_video_button.click(
                generate_video,
                inputs=[shorts_text_input, origin_video],
                outputs=origin_generated_video
            )
        
        # 음성 복제 탭
        with gr.Tab("Voice clone"):
            with gr.Row():
                audio_input = gr.Audio(
                    label="Audio Input",
                    type="filepath"
                )
            clone_button = gr.Button("Voice를 복제합니다.")
            clone_output = gr.Textbox(
                label="Voice Cloning Result",
                interactive=False
            )
            clone_button.click(
                voice_cloning,
                inputs=[audio_input],
                outputs=clone_output
            )
    
    return demo

# 메인 함수
def main():
    """
    Gradio 인터페이스를 실행합니다.
    """
    demo = create_gradio_interface()
    demo.launch()

if __name__ == "__main__":
    main()