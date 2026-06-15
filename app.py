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

# URLの末尾のスラッシュの有無を自動で合わせてくれる設定（エラー防止）
app.router.redirect_slashes = True 

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    トップページを表示します。
    アーティストごとのリストを個別にHTML（Jinja2）へ渡します。
    """
    all_events = fetch_schedule_list()
    
    # アーティストごとに予定を仕分ける（現在に近い順に並びます）
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

# app.py の notify 関数部分を以下に置き換えます

@app.post("/notify")
@app.post("/notify/")
async def notify(request: Request):
    """
    通知エンドポイント（手動・自動共通）。
    どのアーティストを通知するかをフォームデータから判別します。
    """
    # フォームデータから「target（どのアーティストか）」を取得（初期値は all）
    form_data = await request.form()
    target = form_data.get("target", "all")

    # 1. スケジュールをリスト形式で取得
    all_events = fetch_schedule_list() 
    if not all_events:
        print("サイトからスケジュールを取得できませんでした（または0件）")
        return {"status": "ok", "message": "スケジュールなし"}

    # ボタンの選択に応じて、チェック対象のアーティストを絞り込む
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

    # 3. 未通知の「新着イベント」だけを抽出
    new_events = [ev for ev in events if ev["url"] not in notified_urls]

    if not new_events:
        print(f"{target} の新着スケジュールはありませんでした。")
        return {"status": "ok", "message": "新着なし"}

    # 4. 新着分だけのLINEメッセージを作成
    text = title_tag
    for ev in new_events:
        date_str = ev["date"].strftime("%Y-%m-%d") if ev["date"] else "日付未定"
        text += f"📅 {date_str}\n🎵 {ev['artist']}\n📝 {ev['title']}\n🔗 詳細リンク:\n{ev['url']}\n"
        text += "---------------------\n\n"

    # 5. LINEに送信
    send_line_message(text)

    # 6. 送信が成功したURLを Supabase に保存
    rows = [{"url": ev["url"]} for ev in new_events]
    post_url = f"{supabase_url}/rest/v1/notified_events"
    
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
