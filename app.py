import os
import httpx
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
    """
    トップページを開いたときの処理。
    すべての予定を『新しい順（直近が上）』に一覧表示します。
    """
    schedule_text = fetch_schedule_string()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"schedule": schedule_text}
    )

@app.post("/notify")
def notify():
    """
    毎日18:00に自動実行される通知エンドポイント。
    新着のスケジュールがある場合のみ、新しい順にLINEへ通知します。
    """
    # 1. 最新のスケジュールをリスト形式で取得
    events = fetch_schedule_list() 
    if not events:
        print("サイトからスケジュールを取得できませんでした（または0件）")
        return {"status": "ok", "message": "スケジュールなし"}

    # 2. Supabase から過去に通知済みの URL 一覧を取得
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    
    try:
        res = httpx.get(f"{supabase_url}/rest/v1/notified_events?select=url", headers=headers)
        res.raise_for_status()
        notified_urls = [row["url"] for row in res.json()]
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
    try:
        httpx.post(f"{supabase_url}/rest/v1/notified_events", headers=headers, json=rows)
        print(f"新着 {len(new_events)} 件のURLをデータベースに記録しました。")
    except Exception as e:
        print("データベースへの書き込みに失敗しました:", e)

    return {"status": "ok", "message": f"{len(new_events)}件の新着を通知しました"}


def fetch_schedule_list():
    """スケジュールを『リスト（生のデータ）』の形で取得し、新しい順に並び替える関数"""
    from fetch_frederic import fetch_frederic
    events = []
    try:
        events.extend(fetch_frederic())
    except Exception as e:
        print("フレデリックの取得に失敗:", e)
    
    # 【新しい順・直近の予定を一番上に並び替える設定】
    # 日付があるものを優先し、日付が近い順（降順 reverse=True）に並び替えます
    events.sort(key=lambda x: (x["date"] is not None, x["date"]), reverse=True)
    return events

def fetch_schedule_string():
    """トップページの表示用に、スケジュールを『綺麗な文字列』に変換する関数（新しい順になります）"""
    events = fetch_schedule_list()
    text = ""
    for ev in events:
        date_str = ev["date"].strftime("%Y-%m-%d") if ev["date"] else "日付未定"
        text += f"📅 {date_str}\n🎵 {ev['artist']}\n📝 {ev['title']}\n🔗 詳細URL:\n{ev['url']}\n"
        text += "---------------------\n\n"
    return text

