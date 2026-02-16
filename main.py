import requests
import os
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")
CITY_CODE = os.environ.get("USER_CITY_CODE")

# --- ゴミの日の設定（お住まいの地域に合わせて書き換えてください） ---
GOMI_SCHEDULE = {
    "Monday": "【可燃ごみ】の日です🔥",
    "Tuesday": "（ごみ収集はありません）",
    "Wednesday": "【資源ごみ・ペットボトル】の日です♻️",
    "Thursday": "【可燃ごみ】の日です🔥",
    "Friday": "【不燃ごみ】の日です🚫",
    "Saturday": "（ごみ収集はありません）",
    "Sunday": "（ごみ収集はありません）",
}


def get_tomorrow_weather_and_gomi():
    """明日の天気・降水確率・ゴミの日情報をまとめて取得"""
    url = f"https://weather.tsukumijima.net/api/forecast/city/{CITY_CODE}"

    # バグ特定用コード　開始
    print(f"DEBUG_URL: {url}")
    response = requests.get(url)
    print(f"DEBUG_STATUS: {response.status_code}")
    # バグ特定用コード　終了
    """
    response = requests.get(url)
    if response.status_code != 200:
        return f"天気APIとの通信に失敗しました"
    """

    data = response.json()

    # --- 1. 明日のデータ（index:1）を取り出す ---
    tomorrow = data["forecasts"][1]

    # ここで telop を定義します
    telop = tomorrow.get("telop", "不明")
    date_label = tomorrow.get("dateLabel", "明日")

    # --- 2. 気温の取得（キーは小文字の 'celsius'） ---
    temp_data = tomorrow.get("temperature", {})

    max_val = temp_data.get("max", {}).get("celsius")
    t_max = max_val if max_val is not None else "--"

    min_val = temp_data.get("min", {}).get("celsius")
    t_min = min_val if min_val is not None else "--"

    # --- 3. 降水確率の取得 ---
    rain_probs = tomorrow.get("chanceOfRain", {})
    rain_text = f"午前:{rain_probs.get('T06_12', '--')} / 午後:{rain_probs.get('T12_18', '--')} / 夜:{rain_probs.get('T18_24', '--')}"

    # --- 4. ゴミの日の判定 ---
    tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)
    tomorrow_day_en = tomorrow_date.strftime("%A")
    gomi_info = GOMI_SCHEDULE.get(tomorrow_day_en, "スケジュールなし")

    # --- 5. メッセージ組み立て ---
    msg = (
        f"【{date_label}の準備】\n"
        f"☁️ 天気：{telop}\n"
        f"🌡 気温：{t_max}℃ / {t_min}℃\n"
        f"☔ 降水確率：{rain_text}\n\n"
        f"🗑 明日のゴミ：\n{gomi_info}\n\n"
        f"💡アドバイス：\n"
    )

    # 傘アドバイス
    try:
        # 午後の降水確率を数値化して判定
        p_str = rain_probs.get("T12_18", "0%").replace("%", "")
        p_val = int(p_str) if p_str.isdigit() else 0

        if "雨" in telop or p_val > 30:
            msg += "雨の可能性が高いです。傘を忘れずに！☔"
        else:
            msg += "明日は傘なしでも大丈夫そうです。✨"
    except:
        msg += "天気の変化に気をつけてくださいね。"

    return msg


def send_line_message(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}",
    }
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": text}]}
    requests.post(url, headers=headers, data=json.dumps(payload))


def main():
    try:
        final_msg = get_tomorrow_weather_and_gomi()
        send_line_message(final_msg)
        print("明日の総合通知を送信しました。")
    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    main()
