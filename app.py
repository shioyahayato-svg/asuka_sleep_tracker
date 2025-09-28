# -*- coding: utf-8 -*-
# app.py
import sys
import logging
import random
import datetime
import os 
from dotenv import load_dotenv 

# 外部モジュールと分割したモジュールをインポート
from db_models import create_db_and_tables 
from sleep_tracker_window import SleepTrackerApp

# --- ログ設定 ---
# ログレベルをINFOに設定し、日時、レベル、メッセージを出力
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 環境変数ロード (APIキーなどの読み込み) ---
load_dotenv() 

# --- 💡 DEBUG用コード 💡 ---
# 環境変数ロードの直後に、キーが読み込まれたかを確認
owm_key_prefix = os.getenv('OPENWEATHERMAP_API_KEY', 'NONE')[:8]
gemini_key_prefix = os.getenv('GEMINI_API_KEY', 'NONE')[:8]

logger.info(f"DEBUG: OWM Key Loaded? Prefix: {owm_key_prefix}...")
logger.info(f"DEBUG: Gemini Key Loaded? Prefix: {gemini_key_prefix}...")
# -----------------------------

# --- 47都道府県の主要都市リスト ---
# OpenWeatherMap API向けに、日本語の都道府県名と対応する英語の都市名をマッピング
JAPAN_MAJOR_CITIES = {
    "北海道": "Sapporo", "青森県": "Aomori", "岩手県": "Morioka", "宮城県": "Sendai", 
    "秋田県": "Akita", "山形県": "Yamagata", "福島県": "Fukushima", "茨城県": "Mito", 
    "栃木県": "Utsunomiya", "群馬県": "Maebashi", "埼玉県": "Saitama", "千葉県": "Chiba", 
    "東京都": "Tokyo", "神奈川県": "Yokohama", "新潟県": "Niigata", "富山県": "Toyama", 
    "石川県": "Kanazawa", "福井県": "Fukui", "山梨県": "Kofu", "長野県": "Nagano", 
    "岐阜県": "Gifu", "静岡県": "Shizuoka", "愛知県": "Nagoya", "三重県": "Tsu", 
    "滋賀県": "Otsu", "京都府": "Kyoto", "大阪府": "Osaka", "兵庫県": "Kobe", 
    "奈良県": "Nara", "和歌山県": "Wakayama", "鳥取県": "Tottori", "島根県": "Matsue", 
    "岡山県": "Okayama", "広島県": "Hiroshima", "山口県": "Yamaguchi", "徳島県": "Tokushima", 
    "香川県": "Takamatsu", "愛媛県": "Matsuyama", "高知県": "Kochi", "福岡県": "Fukuoka", 
    "佐賀県": "Saga", "長崎県": "Nagasaki", "熊本県": "Kumamoto", "大分県": "Oita", 
    "宮崎県": "Miyazaki", "鹿児島県": "Kagoshima", "沖縄県": "Naha"
}

# --- 実行 ---
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    # データベースの初期化
    create_db_and_tables() 
    
    app = QApplication(sys.argv)
    
    # メインウィンドウのインスタンス化
    window = SleepTrackerApp(JAPAN_MAJOR_CITIES)
    window.show()
    
    sys.exit(app.exec_())