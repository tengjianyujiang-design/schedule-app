# app.py
import os
import json
import urllib.request
import urllib.error
from fastapi import FastAPI, Request, Form  # 💡【修正】Formを新しくインポートします
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from send_line import send_line_message

app = FastAPI()

# URLの末尾のスラッシュの有無を自動で合わせてくれる設定
app.router.redirect_slashes = True 

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """トップページを表示し、アーティストごとのリストを個別にHTMLへ渡します。"""
    all_events = fetch_schedule_list()
    
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

@app.post("/notify")
@app.post("/notify/")
def notify(target: str = Form("all")):  # 💡【重要】FastAPI標準の Form() を使うことで、どのボタンが押されたか100%確実に判別します
    """
    毎日18:00に自動実行、または画面から手動実行される通知エンドポイント。
    """
    # 1. 最新のスケジュールをリスト形式で取得
    all_events = fetch_schedule_list() 
    if not all_events:
        print("サイトからスケジュールを取得できませんでした（または0件）")
        return {"status": "ok", "message": "スケジュールなし"}

    # 💡【重要】ボタンの選択（target）に応じて、チェック対象のアーティストを厳密に絞り込みます
    if target == "frederic":
        events = [ev for ev in all_events if ev["artist"] == "フレデリック"]
        title_tag = "【🔥フレデリック 新着情報！】\n\n"
    elif target == "chevon":
        events = [ev for ev in all_events if ev["artist"] == "Chevon"]
        title_tag = "【🔥Chevon 新着情報！】\n\n"
    else:
        events = all_events
        title_tag = "【🔥W新着ライブ・メディア情報！】\n\n"

    if not events:
        return {"status": "ok", "message": f"{target} のスケジュールがありません"}

    # 2. Supabase から過去に通知済みの URL 一覧を取得
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    api_url = f"{supabase_url}/rest/v1/notified_events?select=url"
    
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
        print("データベースの読み込みに失敗しました:", e)
        return {"status": "error", "message": "DBエラー"}

    # 3. まだLINEに送っていない「新着イベント」だけを抽出
    new_events = [ev for ev in events if ev["url"] not in notified_urls]

    if not new_events:
        print(f"{target} の新着スケジュールはありませんでした。")
        return {"status": "ok", "message": "新着なし"}

    # 4. 新着分だけのLINEメッセージを作成（現在に近い順）
    text = title_tag
    for ev in new_events:
        date_str = ev["date"].strftime("%Y-%m-%d") if ev["date"] else "日付未定"
        text += f"📅 {date_str}\n🎵 {ev['artist']}\n📝 {ev['title']}\n🔗 詳細リンク:\n{ev['url']}\n"
        text += "---------------------\n\n"

    # 5. LINEに送信
    send_line_message(text)

    # 6. 送信が成功したURLを Supabase に保存（次回から重複通知しないようにする）
    rows = [{"url": ev["url"]} for ev in new_events]
   # 末尾に ?on_conflict=url を付けることで、重複した時はエラーにせず「上書き（無視）」してくれます
post_url = f"{supabase_url}/rest/v1/notified_events?on_conflict=url"

    
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

    return {"status": "ok", "message": "通知を送信しました"}


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
    
    # 日付が古い順（＝現在に近い順）に並び替えます
    events.sort(key=lambda x: (x["date"] is None, x["date"]), reverse=False)
    
    return events

