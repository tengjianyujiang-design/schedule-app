# send_line.py

import requests
from config import LINE_NOTIFY_TOKEN

def send_line_message(message: str):
    """
    LINE Notify にメッセージを送信する関数
    """
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"
    }
    data = {
        "message": message
    }

    response = requests.post(url, headers=headers, data=data)

    # デバッグ用（Render のログに出る）
    print("LINE Notify response:", response.status_code, response.text)
