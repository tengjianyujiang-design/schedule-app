
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from fetch_schedule import fetch_schedule
from send_line import send_line_message

app = FastAPI()

from jinja2 import Environment, FileSystemLoader

# キャッシュサイズを 0 にした Jinja2 環境を自前で作成
jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    cache_size=0  # これでバグの発生原因であるキャッシュ機能をオフにします
)

# 作成した環境を FastAPI の Jinja2Templates に渡す
templates = Jinja2Templates(env=jinja_env)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    schedule = fetch_schedule()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "schedule": schedule}
    )

@app.post("/notify")
def notify():
    schedule = fetch_schedule()
    send_line_message(schedule)
    return {"status": "ok", "message": "通知を送信しました"}
