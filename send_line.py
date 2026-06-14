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

    # 【重要】URLを新しく作り直し、末尾に絶対に余計なスラッシュや空白を入れない
    url = "https://api.line.me/v2/bot/message/push"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.strip()}"
    }
    
    send_text = str(message).strip()
    if not send_text:
        send_text = "スケジュールデータが空です。"

    data = {
        "to": user_id.strip(),
        "messages": [
            {
                "type": "text",
                "text": send_text
            }
        ]
    }

    try:
        # 確実にPOSTメソッドで送信
        response = requests.post(url, headers=headers, json=data)
        
        print("LINE Bot response status:", response.status_code)
        print("LINE Bot response text:", response.text)
        
        # もしまた405エラーが出た場合に、実際に送ったメソッドが何かをログで確認する
        print("実際に送信したメソッド:", response.request.method)
        print("実際に送信したURL:", response.request.url)
        
    except requests.exceptions.RequestException as e:
        print(f"LINE送信中に通信エラーが発生しました: {e}")

