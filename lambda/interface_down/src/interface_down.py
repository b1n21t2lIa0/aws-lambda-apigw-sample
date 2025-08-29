import json
import os
import urllib.request
import ast
from typing import Any, Dict, List

# === ENV ===
TELEGRAM_BOT_TOKEN_1 = os.environ.get("TG_TOKEN_1")
TELEGRAM_CHAT_ID_1   = os.environ.get("TG_CHAT_ID_1")
TELEGRAM_BOT_TOKEN_2 = os.environ.get("TG_TOKEN_2")
TELEGRAM_CHAT_ID_2   = os.environ.get("TG_CHAT_ID_2")

# 哪些 extractedFields 的 name 要抓；可自行擴充
FIELD_MAP = {
    "hostname": ["source"],
    "count": ["count", "Count"],
    "interface_down": ["Interface_Down_TG"],
}

def send_telegram_message(bot_token: str, chat_id: str, message: str) -> None:
    if not bot_token or not chat_id:
        print("[WARN] skip send_telegram_message: missing bot_token or chat_id")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        result = res.read().decode()
        print(f"[DEBUG] Telegram response for {chat_id}:", result)

def parse_messages_value(value: Any) -> List[Dict[str, Any]]:
    """
    將 'messages' 欄位轉成 list[dict] 格式：
    - 如果是字串，先 json.loads；失敗再 ast.literal_eval
    - 如果本來就是 list 就直接回傳
    - 其餘回空陣列
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as je:
            print("[WARN] json.loads failed:", str(je))
            try:
                return ast.literal_eval(value)
            except Exception as ae:
                print("[ERROR] ast.literal_eval failed:", str(ae))
                return []
    return []

def pick_field(extracted: List[Dict[str, str]], keys: List[str]) -> str:
    """從 extractedFields 中依 keys 找第一個匹配到的 content"""
    for item in extracted:
        name = item.get("name")
        if not name:
            continue
        for k in keys:
            if name == k:
                return str(item.get("content", "")).strip()
    return "N/A"

def build_events_block(parsed_messages: List[Dict[str, Any]]) -> str:
    """
    將多筆 messages 組成可讀清單
    例如：
    • Events (2):
      1) Host `10.250.253.1`  Count `2`  Interface `interface_down 1.2.3.4 on bundle-ether...`
      2) Host `10.250.253.2`  Count `2`  Interface `...`
    """
    if not parsed_messages:
        return "• Events (0):\n  (no details)"

    lines = []
    for idx, msg in enumerate(parsed_messages, start=1):
        extracted = msg.get("extractedFields", [])
        host = pick_field(extracted, FIELD_MAP["hostname"])
        cnt  = pick_field(extracted, FIELD_MAP["count"])
        interface_down  = pick_field(extracted, FIELD_MAP["interface_down"])

        piece = f"{idx}) Host `{host}`  Count `{cnt}`  Interface `{interface_down}`"
        lines.append(piece)

    # 避免訊息過長，最多顯示 20 筆
    max_lines = 20
    more = ""
    if len(lines) > max_lines:
        more = f"\n  ...and {len(lines)-max_lines} more"
        lines = lines[:max_lines]

    return "• Events (" + str(len(parsed_messages)) + "):\n  " + "\n  ".join(lines) + more

def lambda_handler(event, context):
    print("[DEBUG] Raw event:")
    print(json.dumps(event, indent=2))

    body_raw = event.get("body", "{}")

    try:
        body = json.loads(body_raw)
    except json.JSONDecodeError as e:
        print("[ERROR] Invalid JSON in 'body':", str(e))
        print("[ERROR] Raw body content:", body_raw)
        # 回 500 讓來源知道 payload 不合法（若要避免重試可改 200）
        return {"statusCode": 500, "body": json.dumps({"error": "Invalid JSON in body"})}

    alert_name   = "Unknown"
    alert_url    = "N/A"
    triggered_at = "N/A"

    # 聚合所有 events 的清單字串
    events_block = "• Events (0):\n  (no details)"

    try:
        if "attachments" in body:
            for att in body["attachments"]:
                # 只要第一個 attachment 的標題與連結（通常就一個）
                alert_name = att.get("title", "").replace("Alert Triggered :", "").strip() or alert_name
                alert_url  = att.get("title_link", alert_url)

                messages_value = None

                for field in att.get("fields", []):
                    title = field.get("title")
                    value = field.get("value", "")

                    if title == "At Time":
                        triggered_at = value
                    elif title == "messages":
                        messages_value = value

                # 解析 messages（一次處理所有筆）
                if messages_value is not None:
                    parsed_messages = parse_messages_value(messages_value)
                    events_block = build_events_block(parsed_messages)

        # 組訊息（不顯示 Description/Recommendation）
        message = f"""🚨 *{alert_name}*

• Time: `{triggered_at}`
{events_block}

🔗 [View Alert]({alert_url})
"""
        print("[DEBUG] Final message:\n" + message)

        # 發送到兩個 Bot / 兩個 Chat（若沒有設定就自動略過該路徑）
        send_telegram_message(TELEGRAM_BOT_TOKEN_1, TELEGRAM_CHAT_ID_1, message)
        send_telegram_message(TELEGRAM_BOT_TOKEN_2, TELEGRAM_CHAT_ID_2, message)

        return {"statusCode": 200, "body": json.dumps({"message": "Alert sent"})}

    except Exception as e:
        print("[ERROR] Exception occurred during processing:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
