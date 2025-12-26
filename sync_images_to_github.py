import json
import os
import requests
import base64
from datetime import datetime

# --- 初期設定フェーズ ---
print("Mission Start: sync_images_to_github.py 🛰️")

# FirebaseのURL（中継用ノード：temp_upload）
# 末尾の .json は Firebase REST API の決まりだ！
firebase_base_url = "https://chat-1592f-default-rtdb.firebaseio.com/temp_upload"
auth_url = f"{firebase_base_url}.json"
print(f"auth_url:{auth_url}")

# 保存先ディレクトリの作成
upload_dir = "assets/uploads"
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)
    print(f"directory_created:{upload_dir}")

# --- データ取得フェーズ ---
status = "中継基地から未処理の画像を確認中..."
print(f"status:{status}")

try:
    response = requests.get(auth_url)
    print(f"response_code:{response.status_code}")
    
    if response.status_code == 200:
        pending_data = response.json()
    else:
        pending_data = None

except Exception as e:
    print(f"error_fetch:{str(e)}")
    pending_data = None

# --- 画像処理・変換フェーズ ---
if pending_data:
    print(f"found_items:{len(pending_data)}")
    
    for key, item in pending_data.items():
        # Firebaseから届いたBase64データを取得
        img_base64 = item.get('data')
        file_name = item.get('fileName', f"{key}.png")
        
        # 安全なファイル名の生成（タイムスタンプを付与）
        safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
        save_path = os.path.join(upload_dir, safe_name)
        
        print(f"processing_item:{key}")
        print(f"target_file:{safe_name}")

        try:
            # Base64をバイナリに変換して保存
            img_binary = base64.b64decode(img_base64)
            with open(save_path, "wb") as f:
                f.write(img_binary)
            
            print(f"save_success:{save_path}")

            # --- クリーンアップフェーズ ---
            # GitHubへの保存が成功したので、Firebase側を削除して容量を空ける
            delete_url = f"{firebase_base_url}/{key}.json"
            del_res = requests.delete(delete_url)
            
            if del_res.status_code == 200:
                print(f"firebase_cleanup_success:{key}")
            else:
                print(f"firebase_cleanup_failed:{key} (Code:{del_res.status_code})")

        except Exception as e:
            print(f"error_processing_{key}:{str(e)}")

else:
    status = "待機中：新規の画像投稿はありません。"
    print(f"status:{status}")

# --- 完了フェーズ ---
print("Mission Complete: 5分間隔同期処理終了 🫡")
