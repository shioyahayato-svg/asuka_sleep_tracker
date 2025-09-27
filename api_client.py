# -*- coding: utf-8 -*-
import os
import requests
import time
import json
import logging
import random

# --- ログ設定 ---
logger = logging.getLogger(__name__)

# --- APIクライアントクラス ---
class ApiClient:
    """外部APIとの通信を管理するクラス (Gemini, OpenWeatherMap)"""

    # APIキーは.envファイルからロードされる
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
    
    # Gemini APIのエンドポイントとモデル
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
    # OpenWeatherMap API
    OPENWEATHERMAP_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self):
        if not self.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEYが設定されていません。AIアドバイス機能は動作しません。")
        if not self.OPENWEATHERMAP_API_KEY:
            logger.warning("OPENWEATHERMAP_API_KEYが設定されていません。ダミーデータを使用します。")

    # --- ヘルパーメソッド: リトライ付きAPI呼び出し ---
    def _call_api_with_retry(self, url, method="POST", data=None, headers=None, max_retries=3):
        """API呼び出しをリトライと指数関数的バックオフで実行する"""
        
        # ★★★ 修正箇所: タイムアウトを10秒から30秒に延長 ★★★
        TIMEOUT = 30 
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Gemini API呼び出し試行: {attempt + 1}")
                if method == "POST":
                    response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT)
                else: # GET
                    response = requests.get(url, headers=headers, params=data, timeout=TIMEOUT)
                    
                response.raise_for_status() # HTTPエラーレスポンスを検出
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"APIリクエストエラー (試行 {attempt + 1}/{max_retries}): Read timed out. (read timeout={TIMEOUT})")
                if attempt + 1 < max_retries:
                    # 指数関数的バックオフ (1s, 2s, 4s...)
                    sleep_time = 2 ** attempt
                    time.sleep(sleep_time)
                else:
                    raise

            except requests.exceptions.RequestException as e:
                logger.warning(f"APIリクエストエラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt + 1 < max_retries:
                    sleep_time = 2 ** attempt
                    time.sleep(sleep_time)
                else:
                    raise

            except Exception as e:
                logger.error(f"予期せぬエラー: {e}")
                raise

        return None

    # --- 1. Gemini AI API ---
    def get_gemini_advice(self, system_prompt, user_query):
        """Gemini APIを呼び出して睡眠アドバイスを取得する"""
        if not self.GEMINI_API_KEY:
            return "アスカ: ごめんなさい、APIキーが設定されていないためAIアドバイス機能は利用できません。"

        url_with_key = f"{self.GEMINI_API_URL}?key={self.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{ "parts": [{ "text": user_query }] }],
            "systemInstruction": {
                "parts": [{ "text": system_prompt }]
            },
            # Google Search Groundingは利用しないためツールは省略
        }

        try:
            result = self._call_api_with_retry(
                url=url_with_key, 
                method="POST", 
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if result and result.get('candidates'):
                text = result['candidates'][0]['content']['parts'][0]['text']
                # ソース情報はここでは利用しない
                return text
            else:
                return "アスカ: AIからの応答が得られませんでした。サーバー側の問題かもしれません。"

        except Exception as e:
            logger.error(f"Gemini API呼び出しに失敗: {e}")
            return "アスカ: ネットワークエラーまたはサーバー応答エラーにより、アドバイスを取得できませんでした。時間を置いて試してね。"


    # --- 2. OpenWeatherMap API (天気) ---
    def get_weather_data(self, city="Tokyo", country="JP"):
        """OpenWeatherMapから天気と気温を取得する (キーがない場合はダミーデータを返す)"""
        
        # APIキーがない場合はダミーデータを返す
        if not self.OPENWEATHERMAP_API_KEY:
            # ダミーデータ生成
            conditions = ["Clear", "Clouds", "Rain"]
            dummy_condition = random.choice(conditions)
            dummy_temp = random.uniform(15.0, 30.0)
            return dummy_condition, round(dummy_temp, 1)

        params = {
            "q": f"{city},{country}",
            "appid": self.OPENWEATHERMAP_API_KEY,
            "units": "metric", # 摂氏で取得
            "lang": "ja" # 日本語の天気説明を取得
        }

        try:
            # GETリクエスト
            result = self._call_api_with_retry(
                url=self.OPENWEATHERMAP_URL, 
                method="GET", 
                data=params
            )
            
            if result and result.get('main') and result.get('weather'):
                temp = result['main']['temp']
                condition = result['weather'][0]['description']
                return condition, round(temp, 1)
            else:
                logger.warning("OpenWeatherMapからの応答形式が不正です。")
                return None, None
            
        except Exception as e:
            logger.error(f"OpenWeatherMap API呼び出しに失敗: {e}")
            return None, None
