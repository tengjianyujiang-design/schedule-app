import requests

CHANNEL_ACCESS_TOKEN = "XD8K1pZBHpYxQmOVyrtEVjq3wTJFOTkOx0vH/iWQxJXA/5H+gmX+/bS/PBcIR505yL3w8tp1s+awNTJu/atY6FWcp+2/jaMiEIxw5yUvcGs3UdrWhzWygszNMPtHCX+uhtqjEsVO22gAlNvHHefhJwdB04t89/1O/w1cDnyilFU="
USER_ID = "U3c7003a861e2207ad31e77f3b57d7967"

def send_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": USER_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    requests.post(url, headers=headers, json=data)

# テスト送信
send_line("通知テストだよ！")
