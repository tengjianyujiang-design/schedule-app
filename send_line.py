# send_line.py
import os
import requests

def send_line_message(message: str):
    """
    LINE Messaging API を使って自分にメッセージを送信する関数
    """
    # 【超重要】configからではなく、ここで直接Renderの環境変数を読み込みます
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    # デバッグログを出力
    print("【ダイレクト確認】TOKENの有無:", token is not None)
    print("【ダイレクト確認】USER_IDの有無:", user_id is not None)

    if not token or not user_id:
        print("エラー: LINE の設定（トークンまたはユーザーID）が足りません")
        return

    url = "https://line.me"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": str(message)
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        print("LINE Bot response status:", response.status_code)
        print("LINE Bot response text:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"LINE送信中に通信エラーが発生しました: {e}")

        
    except requests.exceptions.RequestException as e:
        print(f"LINE送信中に通信エラーが発生しました: {e}")
