# fetch_chevon.py
import urllib.request
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re

BASE_URL = "https://chevon.biz"

def fetch_chevon():
    url = f"{BASE_URL}/live/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print("Chevon公式サイトの通信エラー:", e)
        return []

    soup = BeautifulSoup(html, "html.parser")
    events = []

    # 1. まずはページ全体のテキストを1行ずつに分解
    raw_text = soup.get_text("\n", strip=True)
    lines = raw_text.split("\n")

    current_date = None
    current_title_lines = []

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # 2026/12/20 や 2026.12.20 などの日付パターンを検知
        date_match = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", line_str)
        
        if date_match:
            # 前の予定がたまっていれば、ここで組み立てて保存
            if current_date and current_title_lines:
                # 全ての行を「空白」で繋ぎ、前後の不要な空白や記号を掃除
                full_title = " ".join(current_title_lines).strip()
                full_title = re.sub(r"\s+", " ", full_title)
                
                if len(full_title) > 3 and "LIVE" != full_title.upper():
                    events.append({
                        "artist": "Chevon",
                        "title": full_title,
                        "date": current_date,
                        "place": "公式サイト参照",
                        "url": url
                    })
            
            # 新しい予定のスタート
            try:
                year = int(date_match.group(1))
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                current_date = datetime(year, month, day)
                
                # 日付と同じ行にある文字もタイトル候補として残す（ただし日付自体は消す）
                rem = line_str.replace(date_match.group(0), "").strip()
                current_title_lines = [rem] if rem else []
            except:
                current_date = None
                current_title_lines = []
        else:
            # 日付がない行は、現在追跡中のスケジュールの「詳細情報（タイトルや会場）」としてひたすら蓄積
            if current_date:
                # フッターや無関係なメニューの文字は除外する防波堤
                if "©" in line_str or "SHOP" in line_str or "倶楽部" in line_str or "BIOGRAPHY" in line_str:
                    continue
                current_title_lines.append(line_str)

    # ループが終わったあとの最後の1件を滑り込みで保存
    if current_date and current_title_lines:
        full_title = " ".join(current_title_lines).strip()
        full_title = re.sub(r"\s+", " ", full_title)
        if len(full_title) > 3:
            events.append({
                "artist": "Chevon",
                "title": full_title,
                "date": current_date,
                "place": "公式サイト参照",
                "url": url
            })

    # 2. 【超強力バックアップ】aタグの個別リンクからも直接予定を回収する
    # これにより、上記テキスト分解で変に文字が切れた場合でも、確実に正しいタイトルで上書きできます
    for a_tag in soup.find_all("a"):
        text = a_tag.get_text(" ", strip=True)
        href = a_tag.get("href", "")
        
        # リンクのテキスト内に日付が含まれているかチェック
        dm = re.search(r"(\d{4})[/\.](\d{1,2})[/\.](\d{1,2})", text)
        if dm and href and any(k in href for k in ["/live/", "ticket", "http"]):
            try:
                ev_date = datetime(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                t_text = text.replace(dm.group(0), "").strip()
                # 連続するスペースを1つに統合
                t_text = re.sub(r"\s+", " ", t_text)
                
                if len(t_text) > 5 and "LIVE" != t_text.upper():
                    link = href if href.startswith("http") else BASE_URL + href
                    events.append({
                        "artist": "Chevon",
                        "title": t_text,
                        "date": ev_date,
                        "place": "公式サイト参照",
                        "url": link
                    })
            except:
                pass

    # 3. 重複チェックと、タイトルが長く綺麗に残っている方を優先するロジック
    unique_events = []
    seen = {} # 日付をキーにして、一番長いタイトルを保持する
    
    for ev in events:
        date_str = ev["date"].strftime("%Y-%m-%d")
        
        # 同じ日に複数のデータが見つかった場合、文字数が多い（詳細が削れていない）方を採用する
        if date_str not in seen:
            seen[date_str] = ev
        else:
            if len(ev["title"]) > len(seen[date_str]["title"]):
                seen[date_str] = ev

    # 辞書からリストに戻す
    unique_events = list(seen.values())

    return unique_events
