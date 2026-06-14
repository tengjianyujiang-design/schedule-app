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

# app.py

app = FastAPI()

# 💡【追加】URLの末尾のスラッシュの有無を自動で合わせてくれる設定（エラー防止）
app.router.redirect_slashes = True 

templates = Jinja2Templates(directory="templates")


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
# app.py の notify 関数の上にあるデコレーターを2行にします

@app.post("/notify")
@app.post("/notify/")  # 💡【追加】末尾スラッシュ付きのアクセスも100%受け付けるようにします
def notify():
    """
    毎日18:00に自動実行される通知エンドポイント。
    """
    # (これ以降の中身のコードは一切変更せず、そのままで大丈夫です)

# app.py の最下部にある関数を修正

def fetch_schedule_list():
    """スケジュールを『リスト（生のデータ）』の形で取得し、現在に近い順（昇順）に並び替える関数"""
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
    
    # 【順番の修正】
    # reverse=True を外し、日付が古い順（＝現在に近い順）に並び替えます
    # 日付未定(None)のものは一番下に配置します
    events.sort(key=lambda x: (x["date"] is None, x["date"]), reverse=False)
    
    # 💡【おまけの優しさ】もし過去の予定を表示させたくない場合は、
    # 今日以降の予定だけを絞り込むとさらに見やすくなります
    # from datetime import datetime, date
    # today = date.today()
    # events = [ev for ev in events if ev["date"] is None or ev["date"].date() >= today]
    
    return events

