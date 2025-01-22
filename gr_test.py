import numpy as np
import gradio as gr

# def flip_text(x):
#     return x[::-1]

# def flip_image(x):
#     return np.fliplr(x)


# open ai api를 이용해서 메세지를 생성합니다.
# draft : 사용자가 입력한 초안
# draft_time : 사용자가 원하는 shorts의 재생시간
# return : ai가 사용자가 입력한 초안을 기초로 설정한 시간분량의 shorts 초안
def generate_message(draft, draft_time):
    return f"AI로 생성된 메시지: {draft} (시간: {draft_time}초)"

def video_file_selected(path):
     print(path)
     return path

def generate_video(shorts_text, video_file):
    return f"AI로 생성된 aiShorts: {shorts_text} (video: {video_file})"

def voice_cloning(audio_file):
    # clone voice

    # message box(음성파일의 복제가 끝나면 mesage box를 출력)
    # gr.Alert(f"AI로 생성된 복제된 음성: {audio_file}", type="info")
    # gr.Markdown(f"AI로 생성된 복제된 음성: {audio_file}")
    gr.Warning(f"AI로 생성된 복제된 음성: {audio_file}")
    gr.
    return f"AI로 생성된 복제된 음성: {audio_file}"

with gr.Blocks() as demo:
    gr.Markdown("aiShorts Playground")
    with gr.Tab("Text generation"):
        with gr.Row():
                draft_input = gr.Textbox(lines=14, label="Draft", placeholder="Shorts 대사의 초안을 입력하세요.")
                with gr.Column():
                    draft_time_input = gr.Radio(
                        choices=[30, 60],
                        label="Time (Sec)",
                        type="value"
                    )
                    draft_output = gr.Textbox(lines=10, label="Msg조정완료")
        generate_message_button = gr.Button("AI로 시간에 맞는 메시지 생성")
        # text_output = gr.Textbox()
        # text_button = gr.Button("Flip")
    with gr.Tab("aiShorts generation"):
        with gr.Row():
            shorts_text_input = gr.Textbox(lines=5, label="Shorts Text", placeholder="Shorts 대사를 입력하세요.")
        with gr.Row():
            origin_video = gr.Video(label="Origin Video Template", height=350, )
            with gr.Column():
                origin_generated_video = gr.Video(label="Generated Video", height=350, )
        generate_video_button = gr.Button("AI로 aiShorts 생성")
    with gr.Tab("Voice clone"):
        with gr.Row():
            audio_input = gr.Audio(label="Audio Input")
        clone_button = gr.Button("Voice를 복제합니다.")

    # generate_message_button 클릭 시 draft_input과 draft_time_input을 전달
    generate_message_button.click(
        generate_message, 
        inputs=[draft_input, draft_time_input],  # 두 개의 입력값을 전달
        outputs=draft_output
    )
    # video_file.change(video_file_selected, inputs=video_file, outputs=origin_video)
    generate_video_button.click(
        generate_video,
        inputs=[shorts_text_input, origin_video],
        outputs=origin_generated_video
    )

    clone_button.click(
        voice_cloning,
        inputs=[audio_input],
        outputs=None
    )
    # text_button.click(flip_text, inputs=draft_input, outputs=text_output)
    # image_button.click(flip_image, inputs=image_input, outputs=image_output)

if __name__ == "__main__":
    demo.launch()