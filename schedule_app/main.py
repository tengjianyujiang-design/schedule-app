from fetch_frederic import fetch_frederic
from db import save_events, load_events

def main():
    print("🔄 スケジュールを更新しています...\n")

    all_events = []
    all_events += fetch_frederic()

    save_events(all_events)

    print("📅 最新スケジュール（日時順）\n")

    events = load_events()

    for e in events:
        date = e["date"]
        print(f"{date} | {e['artist']} | {e['title']} | {e['place']}")

if __name__ == "__main__":
    main()
