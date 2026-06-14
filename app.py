from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# 内部関数が async で定義されていると仮定
from fetch_schedule import fetch_schedule
from send_line_message import send_line_message 

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # 非同期でスケジュールを取得
    schedule = await fetch_schedule()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "schedule": schedule}
    )

@app.post("/notify")
async def notify():
    # 毎回新しく取得するのではなく、本来は画面から受け取るかキャッシュを使うのが理想
    schedule = await fetch_schedule()
    await send_line_message(schedule)
    return {"status": "ok", "message": "通知を送信しました"}

