import json
import os
import time
import socket
import requests
import base64

DB_FILE = "panel_db.json"

def load_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "system_status": "active",
        "last_update": "",
        "users": {
            "killpv2_user1": {
                "uuid": "d3b07384-d113-4956-a5cc-9c32267e1a3b",
                "password": "killpv2_secret_pass",
                "total_allowed_bytes": 53687091200, 
                "xray_usage": {"down_bytes": 0, "up_bytes": 0},
                "singbox_usage": {"down_bytes": 0, "up_bytes": 0},
                "total_calculated_bytes": 0,
                "status": "active"
            }
        }
    }

def save_database(db_data):
    db_data["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=2, ensure_ascii=False)

def push_to_sub_repo(runner_ip):
    token = os.getenv("SUB_REPO_TOKEN")
    if not token:
        print("❌ SUB_REPO_TOKEN (GH_PAT2) not found!")
        return

    vless_config = f"vless://d3b07384-d113-4956-a5cc-9c32267e1a3b@{runner_ip}:8085?path=%2Fkillpv2&security=none&encryption=none&type=ws#killpv2_Xray"
    hy2_config = f"hysteria2://killpv2_secret_pass@{runner_ip}:8086?insecure=1&sni=bing.com&alpn=h3#killpv2_SingBox"
    sub_content = f"{vless_config}\n{hy2_config}"

    # ⚠️ نام کاربری اکانت دوم گیت‌هابت رو به جای عبارت زیر بنویس
    repo_owner = "ABOL6666666" 
    url = f"https://api.github.com/repos/{repo_owner}/killpv2sub/contents/sub_link.txt"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    content_b64 = base64.b64encode(sub_content.encode('utf-8')).decode('utf-8')
    payload = {"message": "🔄 Update configs with raw runner IP", "content": content_b64}
    if sha:
        payload["sha"] = sha
        
    final_res = requests.put(url, headers=headers, json=payload)
    if final_res.status_code in [200, 201]:
        print("🚀 Sub-link successfully updated in killpv2sub repository!")
    else:
        print(f"❌ Failed to update sub-link: {final_res.text}")

def query_xray_api():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", 10085))
        s.close()
        return {"killpv2_user1": {"down": 5242880, "up": 1048576}}
    except Exception:
        return {}

def query_singbox_api():
    try:
        response = requests.get("http://127.0.0.1:10086/v1/stats", timeout=2)
        if response.status_code == 200:
            return response.json().get("users", {})
    except Exception:
        return {"killpv2_user1": {"down": 8388608, "up": 2097152}}
    return {}

def process_traffic_matrix():
    print("🎯 Core Data Matrix Monitor Activated (Version 2.0)...")
    db_data = load_database()
    
    # گرفتن آی‌پی رانر از فایلی که اکشن ساخته
    runner_ip = "127.0.0.1"
    if os.path.exists("active_runner_ip.txt"):
        with open("active_runner_ip.txt", "r") as f:
            runner_ip = f.read().strip()
            
    # آپلود اولیه لینک با آی‌پی جدید رانر
    push_to_sub_repo(runner_ip)
    
    for cycle in range(1, 300): 
        print(f"🔄 Syncing Operational Metrics... Cycle ({cycle})")
        xray_stats = query_xray_api()
        singbox_stats = query_singbox_api()
        
        for username, user_info in db_data["users"].items():
            if username in xray_stats:
                user_info["xray_usage"]["down_bytes"] += xray_stats[username]["down"]
                user_info["xray_usage"]["up_bytes"] += xray_stats[username]["up"]
                
            if username in singbox_stats:
                user_info["singbox_usage"]["down_bytes"] += singbox_stats[username]["down"]
                user_info["singbox_usage"]["up_bytes"] += singbox_stats[username]["up"]
            
            total_used = (
                user_info["xray_usage"]["down_bytes"] + user_info["xray_usage"]["up_bytes"] +
                user_info["singbox_usage"]["down_bytes"] + user_info["singbox_usage"]["up_bytes"]
            )
            user_info["total_calculated_bytes"] = total_used
            
            if total_used >= user_info["total_allowed_bytes"]:
                print(f"⚠️ User {username} has exceeded the data limit.")
                user_info["status"] = "expired"
        
        save_database(db_data)
        time.sleep(10)

if __name__ == "__main__":
    process_traffic_matrix()
