# fetch_chevon.py
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

BASE_URL = "https://chevon.biz"

def fetch_chevon():
    list_url = f"{BASE_URL}/live/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(list_url, headers=headers, method="GET")
    
    html = None
    # タイムアウト対策（最大3回リトライ）
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                html = response.read().decode("utf-8")
                break
        except Exception as e:
            print(f"Chevon接続試行 {attempt + 1} 回目失敗: {e}")
            if attempt < 2:
                time.sleep(2)
            else:
                return []

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    events = []

    # 【確定ロジック】aタグに依存せず、スケジュールが書かれているすべてのテキスト要素（p, div, li）をスキャン
    elements = soup.find_all(["p", "div", "li", "span", "a"])

    for el in elements:
        # 子要素のタグを一旦無視して、その要素単体のテキストを取得
        text_content = el.get_text(" ", strip=True)
        if not text_content or len(text_content) < 10:
            continue

        # メニューバーなどの無関係なテキストはスキップ
        if "BIOGRAPHY" in text_content or "DISCOGRAPHY" in text_content or "©" in text_content:
            continue

        # 「2026/06/14」や「2026.09.13」などの日付パターンを正確に検知
        date_match = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", text_content)
        if not date_match:
            continue

        # 日付のパース
        try:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            event_date = datetime(year, month, day)
        except:
            continue

        # タイトルのクレンジング（日付の文字を消す）
        display_title = text_content.replace(date_match.group(0), "").strip()
        
        # 過去の「LIVE 2025 2024...」などの年号ナビゲーションが混ざっていたら除去
        display_title = re.sub(r"LIVE\s+\d{4}.*?\d{4}", "", display_title)
        display_title = re.sub(r"\s+", " ", display_title).strip()

        if len(display_title) < 5:
            continue

        # 【個別URLの解決】
        # その要素自体、またはそのすぐ近く（子要素）にあるaタグからチケットや詳細の個別リンクを抽出
        link_tag = el if el.name == "a" else el.find("a")
        final_url = list_url
        
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            if href and href != "/" and "/live" in href or "ticket" in href or "http" in href:
                final_url = href if href.startswith("http") else BASE_URL + href

        events.append({
            "artist": "Chevon",
            "title": display_title,
            "date": event_date,
            "place": "公式サイトをご参照ください",
            "url": final_url
        })

    # 同じ日付の重複を排除（最も文字数（情報量）が多く、タイトルが詳細なものを優先して残す）
    clean_dict = {}
    for ev in events:
        date_str = ev["date"].strftime("%Y-%m-%d")
        if date_str not in clean_dict:
            clean_dict[date_str] = ev
        else:
            # 「・21」のような文字切れゴミデータを完全に上書きし、フルタイトルを残す
            if len(ev["title"]) > len(clean_dict[date_str]["title"]):
                clean_dict[date_str] = ev

    unique_events = list(clean_dict.values())
    
    # 最後に日付の近い順（古い順 ＝ 上から下に未来へ流れる順番）に並び替える
    unique_events.sort(key=lambda x: x["date"])
    return unique_events
