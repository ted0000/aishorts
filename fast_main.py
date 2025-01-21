from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# 1) 정적 파일 서빙
#    예: /static/index.html => static/index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2) 루트 경로 -> index.html 반환
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    # uvicorn 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)