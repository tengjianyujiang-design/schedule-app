# fetch_frederic.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 末尾のスラッシュが重複しないように修正
BASE_URL = "https://frederic-official.com"

def fetch_frederic():
    # 正しいLIVEページのURL
    url = f"{BASE_URL}/live"
    
    # 相手のサイトに拒否されないよう、一般的なブラウザ（User-Agent）を装う
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status() # 通信エラーがあればここで例外を発生させる
    except Exception as e:
        print("フレデリック公式サイトの通信エラー:", e)
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    events = []

    # 実際の公式サイトの構造に合わせたセレクターに修正
    # 各スケジュールは <li> タグのなかの「aタグ」または特定の要素で構成されています
    # 確実を期すため、liveページ内のリンクやテキスト構造から抽出します
    items = soup.select("ul li")  # サイトの最新構造に合わせて調整

    # もし上記で取れない場合のための代替手段：
    # サイトの「LIVE」セクション配下の要素を解析
    if not items:
        # トップページや簡易表示の場合
        items = soup.find_all("li")

    for item in items:
        # テキストに日付や会場が含まれているかチェック
        text_content = item.get_text(strip=True)
        
        # 簡易的にテキストを解析するか、特定のタグ（例: .date, .title）を探す
        date_tag = item.select_one(".date") or item.select_one("span")
        title_tag = item.select_one(".title") or item.select_one("p")
        link_tag = item.select_one("a")

        if not link_tag or not text_content:
            continue

        # 日付の抽出
        date_text = date_tag.get_text(strip=True) if date_tag else ""
        event_date = None
        
        # "06.18" のような形式をパース
        try:
            # 文字列から日付っぽい部分（例: 06.18）を探す
            import re
            match = re.search(r"(\d{2})\.(\d{2})", text_content)
            if match:
                month, day = match.groups()
                event_date = datetime(datetime.now().year, int(month), int(day))
        except:
            event_date = None

        # タイトルと会場の抽出
        title = title_tag.get_text(strip=True) if title_tag else text_content
        place = ""
        
        # 「東京」や「大阪」といった地名が含まれていることが多いため抽出
        if "「" in title and "」" in title:
            # タイトルから会場や地名を大まかに分離
            parts = title.split("」")
            if len(parts) > 1:
                place = parts[0].replace("「", "")
                title = parts[1]

        # 詳細URL
        href = link_tag["href"]
        link = href if href.startswith("http") else BASE_URL + href

        # アーティストのLIVEに関係ありそうなデータのみに絞り込む
        if event_date or "Tour" in title or "LIVE" in text_content or "公演" in text_content:
            events.append({
                "artist": "フレデリック",
                "title": title,
                "date": event_date,
                "place": place if place else "公式サイトをご確認ください",
                "url": link,
                "source": "frederic-official"
            })

    # 重複する予定を削除（URLが同じものはまとめる）
    seen_urls = set()
    unique_events = []
    for ev in events:
        if ev["url"] not in seen_urls:
            seen_urls.add(ev["url"])
            unique_events.append(ev)

    return unique_events

