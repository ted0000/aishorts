import os
import tempfile

class Paths:
    @staticmethod
    def get_scenemixed_video() -> str:
        root = os.getcwd()
        dir_path = os.path.join(root, os.getenv("DIR_SCENE_MIXED_RESULT", "result/scene_mixed"))
        os.makedirs(dir_path, exist_ok=True)

        # 임시 파일명 생성 (임시 디렉토리 내에서)
        return tempfile.mktemp(suffix=".mp4", dir=dir_path)

