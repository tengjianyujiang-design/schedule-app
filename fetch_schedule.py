# fetch_schedule.py

from fetch_frederic import fetch_frederic
# 今後、他のアーティストを追加するならここに import を増やす
# from fetch_chevon import fetch_chevon
# from fetch_sdm import fetch_sdm
# from fetch_starto import fetch_starto

def fetch_schedule():
    events = []

    # フレデリック
    try:
        events.extend(fetch_frederic())
    except Exception as e:
        print("Frederic fetch error:", e)

    # 他のアーティストを追加する場合はここに書く
    # try:
    #     events.extend(fetch_chevon())
    # except Exception as e:
    #     print("Chevon fetch error:", e)

    # try:
    #     events.extend(fetch_sdm())
    # except Exception as e:
    #     print("SDM fetch error:", e)

    # try:
    #     events.extend(fetch_starto())
    # except Exception as e:
    #     print("STARTO fetch error:", e)

    # 日付順に並べる（date が None のものは最後に）
    events.sort(key=lambda x: (x["date"] is None, x["date"]))

    # 表示用の文字列に変換
    # 表示用の文字列に変換
    text = ""
    for ev in events:
        date_str = ev["date"].strftime("%Y-%m-%d") if ev["date"] else "日付未定"
        
        # URLの前後にしっかり改行(\n)を入れ、文字がくっつかないようにします
        text += f"📅 {date_str}\n"
        text += f"🎵 {ev['artist']}\n"
        text += f"📝 {ev['title']}\n"
        text += f"🔗 詳細URL:\n{ev['url']}\n"  # URLの直前で改行
        text += "---------------------\n\n"    # 区切り線を入れて見やすく

    return text

