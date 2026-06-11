from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fetch_schedule import fetch_schedule
from send_line import send_line

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index(request: Request):
    schedule = fetch_schedule()
    return templates.TemplateResponse("index.html", {"request": request, "schedule": schedule})

@app.post("/notify")
def notify():
    schedule = fetch_schedule()
    send_line(schedule)
    return {"status": "ok", "message": "通知を送信しました"}
