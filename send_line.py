# send_line.py

import requests
from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID
# send_line.py のデバッグ用書き換え例

def send_line_message(message: str):
    """
    LINE Messaging API を使って自分にメッセージを送信する関数
    """
    # どの変数が空っぽ（None）になっているかをログに出す
    print("【デプロイ確認】TOKENの有無:", LINE_CHANNEL_ACCESS_TOKEN is not None)
    print("【デプロイ確認】USER_IDの有無:", LINE_USER_ID is not None)

    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("エラー: LINE の設定（トークンまたはユーザーID）が足りません")
        return


    # Messaging API のプッシュメッセージ用エンドポイント
    url = "https://line.me"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    # Messaging API 専用の JSON 構造
    data = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": str(message)  # 確実に文字列にする
            }
        ]
    }

    try:
        # data= ではなく json= で送る点に注意してください
        response = requests.post(url, headers=headers, json=data)
        
        # デバッグ用（Render のログに出る）
        print("LINE Bot response status:", response.status_code)
        print("LINE Bot response text:", response.text)
        
    except requests.exceptions.RequestException as e:
        print(f"LINE送信中に通信エラーが発生しました: {e}")
