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

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """トップページを表示し、全予定を新しい順に一覧表示します。"""
    schedule_text = fetch_schedule_string()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"schedule": schedule_text}
    )

@app.post("/notify")
def notify():
    """毎日18:00に自動実行。新着スケジュールがある場合のみLINEへ通知します。"""
    # 1. スケジュールをリスト形式で取得
    events = fetch_schedule_list() 
    if not events:
        print("サイトからスケジュールを取得できませんでした（または0件）")
        return {"status": "ok", "message": "スケジュールなし"}

    # 2. Supabase から過去に通知済みの URL 一覧を取得
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    # 接続用のURL
    api_url = f"{supabase_url}/rest/v1/notified_events?select=url"
    
    # 【変更点】httpx の代わりに Python 標準の urllib を使って Supabase からデータを読み込む
    req = urllib.request.Request(
        api_url,
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        },
        method="GET"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            notified_urls = [row["url"] for row in res_data]
    except Exception as e:
        print("データベースの読み込みに失敗しました。安全のため全件通知を回避します:", e)
        return {"status": "error", "message": "DBエラー"}

    # 3. まだLINEに送っていない「新着イベント」だけを抽出
    new_events = [ev for ev in events if ev["url"] not in notified_urls]

    if not new_events:
        print("新着スケジュールはありませんでした。静かに終了します。")
        return {"status": "ok", "message": "新着なし"}

    # 4. 新着分だけのLINEメッセージを作成（新しい順・直近が上）
    text = "【🔥新着ライブ・メディア情報！】\n\n"
    for ev in new_events:
        date_str = ev["date"].strftime("%Y-%m-%d") if ev["date"] else "日付未定"
        text += f"📅 {date_str}\n🎵 {ev['artist']}\n📝 {ev['title']}\n🔗 詳細リンク:\n{ev['url']}\n"
        text += "---------------------\n\n"

    # 5. LINEに送信
    send_line_message(text)

    # 6. 送信が成功したURLを Supabase に保存（次回から重複通知しないようにする）
    rows = [{"url": ev["url"]} for ev in new_events]
    post_url = f"{supabase_url}/rest/v1/notified_events"
    
    # 【変更点】urllib を使って Supabase に書き込む
    post_req = urllib.request.Request(
        post_url,
        data=json.dumps(rows).encode("utf-8"),
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(post_req) as response:
            print(f"新着 {len(new_events)} 件のURLをデータベースに記録しました。")
    except Exception as e:
        print("データベースへの書き込みに失敗しました:", e)

    return {"status": "ok", "message": f"{len(new_events)}件の新着を通知しました"}


# app.py の下部にある fetch_schedule_list を書き換え

def fetch_schedule_list():
    """スケジュールを『リスト（生のデータ）』の形で取得し、新しい順に並び替える関数"""
    from fetch_frederic import fetch_frederic
    from fetch_chevon import fetch_chevon  # 【追加】Chevonの関数をインポート
    
    events = []
    
    # フレデリックの取得
    try:
        events.extend(fetch_frederic())
    except Exception as e:
        print("フレデリックの取得に失敗:", e)
        
    # 【追加】Chevonの取得
    try:
        events.extend(fetch_chevon())
    except Exception as e:
        print("Chevonの取得に失敗:", e)
    
    # 日付があるものを優先し、日付が新しい・近い順（降順）に並び替えます
    events.sort(key=lambda x: (x["date"] is not None, x["date"]), reverse=True)
    return events


def fetch_schedule_string():
    """トップページの表示用に、スケジュールを綺麗な文字列に変換する関数"""
    events = fetch_schedule_list()
    text = ""
    for ev in events:
        date_str = ev["date"].strftime("%Y-%m-%d") if ev["date"] else "日付未定"
        text += f"📅 {date_str}\n🎵 {ev['artist']}\n📝 {ev['title']}\n🔗 詳細URL:\n{ev['url']}\n"
        text += "---------------------\n\n"
    return text

