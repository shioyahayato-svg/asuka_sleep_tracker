# -*- coding: utf-8 -*-
# api_client.py
import os
import requests
import time
import json
import logging
import random
import datetime # datetimeモジュールを追加
from typing import Optional, Any, Dict, Union 

# --- ログ設定 ---
logger = logging.getLogger(__name__)

# --- APIクライアントクラス ---
class ApiClient:
    """外部APIとの通信を管理するクラス (Gemini, OpenWeatherMap)"""

    # --- クラス定数 ---
    # モデル名は generateContent エンドポイントで使用するモデルに合わせます
    GEMINI_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    OPENWEATHERMAP_URL: str = "https://api.openweathermap.org/data/2.5/weather"
    MAX_API_RETRIES: int = 3        # 最大リトライ回数
    REQUEST_TIMEOUT: int = 30       # リクエストタイムアウト秒数

    def __init__(self):
        """環境変数からAPIキーを取得し、未設定の場合は警告をログに記録する"""
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.OPENWEATHERMAP_API_KEY: str = os.getenv("OPENWEATHERMAP_API_KEY", "")

        if not self.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEYが設定されていません。AIアドバイス機能は動作しません。")
        if not self.OPENWEATHERMAP_API_KEY:
            logger.warning("OPENWEATHERMAP_API_KEYが設定されていません。天気データにダミーデータを使用します。")

    # --- ヘルパーメソッド: リトライ付きAPI呼び出し ---
    def _call_api_with_retry(self, url: str, method: str = "POST", 
                             data: Optional[Dict[str, Any]] = None, 
                             headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        API呼び出しをリトライと指数関数的バックオフ（+ジッター）で実行する
        """
        
        for attempt in range(self.MAX_API_RETRIES):
            try:
                logger.info(f"API呼び出し試行: {attempt + 1}/{self.MAX_API_RETRIES}")
                
                # HTTPメソッドに応じてリクエストを実行
                if method == "POST":
                    response = requests.post(
                        url, 
                        headers=headers, 
                        json=data, 
                        timeout=self.REQUEST_TIMEOUT
                    )
                elif method == "GET":
                    response = requests.get(
                        url, 
                        headers=headers, 
                        params=data, # GETリクエストでは 'params' を使用
                        timeout=self.REQUEST_TIMEOUT
                    )
                else:
                    logger.error(f"未サポートのHTTPメソッド: {method}")
                    return None

                # 4xx/5xxエラーが発生した場合に例外を発生させる
                response.raise_for_status() 
                return response.json()

            # リクエスト関連のエラーを処理 (接続、読み取り、タイムアウト、HTTPエラー)
            except requests.exceptions.RequestException as e:
                # 400エラーの場合、レスポンス本文があればログに出力してデバッグを容易にする
                response_text = ""
                if hasattr(e, 'response') and e.response is not None:
                     try:
                         # レスポンス本文を読み取ってログに出力
                         response_text = f" Response Body: {e.response.text}"
                     except Exception:
                         pass
                
                logger.warning(f"APIリクエストエラー (試行 {attempt + 1}/{self.MAX_API_RETRIES}): {e}{response_text}")
            
            # リトライが必要な場合、待機する
            if attempt + 1 < self.MAX_API_RETRIES:
                # 指数関数的バックオフ (1s, 2s, 4s, ...) にランダムなジッターを加える
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"リトライのため {sleep_time:.2f} 秒待機します...")
                time.sleep(sleep_time)
            else:
                logger.error("API呼び出しが最大リトライ回数に達し、失敗しました。")
                return None
        
        return None

    # --- 1. Gemini AI API ---
    def generate_advice_sync(self, user_query: str) -> str:
        """Gemini APIを呼び出して睡眠アドバイスを取得する"""
        
        if not self.GEMINI_API_KEY:
            return "アスカ: ごめんなさい、APIキーが設定されていないためAIアドバイス機能は利用できません。"

        # APIキーをURLに付加
        url_with_key = f"{self.GEMINI_API_URL}?key={self.GEMINI_API_KEY}"
        
        # システムプロンプトをここで定義
        system_prompt = (
            "あなたは睡眠トラッカーアプリのアドバイザー「アスカ」です。ユーザーから提供された睡眠データと目標に基づき、"
            "健康的で親しみやすいトーンで、具体的かつ実行可能なアドバイスを3つ提供してください。"
            "応答は日本語で、箇条書きを使って分かりやすく構成してください。"
        )
        
        # ★ 400 Bad Request を解消するための修正済み JSON ペイロード構造 ★
        payload = {
            # 1. systemInstruction フィールドをトップレベルに追加
            "systemInstruction": {
                "parts": [{ "text": system_prompt }]
            },
            # 2. contents には 'user' ロールのプロンプトのみを含める
            "contents": [
                { "role": "user", "parts": [{ "text": user_query }] }
            ],
            # 3. config を generationConfig にリネーム
            "generationConfig": {
                "temperature": 0.7 # 創造性を少し上げる
            }
        }

        # API呼び出し
        result = self._call_api_with_retry(
            url=url_with_key, 
            method="POST", 
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if result and result.get('candidates'):
            try:
                # 応答からテキストを安全に抽出
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text
            except (KeyError, IndexError):
                logger.error("Gemini API応答の形式が不正です。")
                return "アスカ: AIからの応答が得られませんでした。応答構造に問題があります。"
        else:
            return "アスカ: ネットワークエラーまたはサーバー応答エラーにより、アドバイスを取得できませんでした。時間を置いて試してね。"


    # --- 2. OpenWeatherMap API (天気) ---
    def get_weather_sync(self, city: str = "Tokyo", wake_time_dt: datetime.datetime = None, country: str = "JP") -> Dict[str, Union[str, float, None]]:
        """
        OpenWeatherMapから天気と気温を取得する。
        戻り値は {'description': str | None, 'temp_celsius': float | None}
        """
        
        if not self.OPENWEATHERMAP_API_KEY:
            # ダミーデータ生成
            conditions = ["晴れ", "曇り", "雨"]
            dummy_condition = random.choice(conditions)
            dummy_temp = random.uniform(15.0, 30.0)
            logger.info(f"OpenWeatherMapキーがないためダミーデータを返します: {dummy_condition}, {round(dummy_temp, 1)}℃")
            return {
                'description': dummy_condition, 
                'temp_celsius': round(dummy_temp, 1)
            }
        
        params = {
            "q": f"{city},{country}",
            "appid": self.OPENWEATHERMAP_API_KEY, 
            "units": "metric", # 摂氏
            "lang": "ja" 
        }

        # GETリクエスト
        result = self._call_api_with_retry(
            url=self.OPENWEATHERMAP_URL, 
            method="GET", 
            data=params
        )
        
        if result and result.get('main') and result.get('weather'):
            try:
                temp = result['main']['temp']
                condition = result['weather'][0]['description']
                return {
                    'description': condition, 
                    'temp_celsius': round(temp, 1)
                }
            except (KeyError, IndexError):
                logger.warning("OpenWeatherMapからの応答形式が不正です。")
                return {'description': None, 'temp_celsius': None}
        else:
            logger.warning("OpenWeatherMapから天気データを取得できませんでした。")
            return {'description': None, 'temp_celsius': None}
