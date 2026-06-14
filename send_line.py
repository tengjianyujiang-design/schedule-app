# send_line.py
import os
import requests

def send_line_message(message: str):
    """
    LINE Messaging API を使って自分にメッセージを送信する関数
    """
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if not token or not user_id:
        print("エラー: LINE の設定（トークンまたはユーザーID）が足りません")
        return

    # 正確なエンドポイントURL（末尾に不要な文字がないことを確認）
    url = "https://line.me"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.strip()}"  # 前後の空白を完全に排除
    }
    
    # もしスケジュールが空だった場合の対策
    send_text = str(message).strip()
    if not send_text:
        send_text = "本日のスケジュールはありません、または取得に失敗しました。"

    data = {
        "to": user_id.strip(),  # 前後の空白を完全に排除
        "messages": [
            {
                "type": "text",
                "text": send_text
            }
        ]
    }

    try:
        # 必ず json= で送信する
        response = requests.post(url, headers=headers, json=data)
        
        print("LINE Bot response status:", response.status_code)
        print("LINE Bot response text:", response.text)
        
    except requests.exceptions.RequestException as e:
        print(f"LINE送信中に通信エラーが発生しました: {e}")

