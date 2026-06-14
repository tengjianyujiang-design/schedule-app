# app.py
import os
import json
import urllib.request
import urllib.error
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from send_line import send_line_message

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
# app.py の該当部分を書き換え

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    トップページを表示します。
    アーティストごとのリストを個別にHTML（Jinja2）へ渡します。
    """
    all_events = fetch_schedule_list()
    
    # アーティストごとに予定を仕分ける（それぞれ新しい順に並びます）
    frederic_events = [ev for ev in all_events if ev["artist"] == "フレデリック"]
    chevon_events = [ev for ev in all_events if ev["artist"] == "Chevon"]
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "frederic_schedule": frederic_events,
            "chevon_schedule": chevon_events
        }
    )

# --- (中略 / notify関数などはそのまま) ---

def fetch_schedule_list():
    """スケジュールを『リスト（生のデータ）』の形で取得し、新しい順に並び替える関数"""
    from fetch_frederic import fetch_frederic
    from fetch_chevon import fetch_chevon
    
    events = []
    try:
        events.extend(fetch_frederic())
    except Exception as e:
        print("フレデリックの取得に失敗:", e)
        
    try:
        events.extend(fetch_chevon())
    except Exception as e:
        print("Chevonの取得に失敗:", e)
    
    # 日付が新しい・近い順（降順）に並び替え
    events.sort(key=lambda x: (x["date"] is not None, x["date"]), reverse=True)
    return events
