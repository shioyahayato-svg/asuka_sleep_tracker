# -*- coding: utf-8 -*-
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base # ★ここを修正しました★
from sqlalchemy.exc import OperationalError
import logging

logger = logging.getLogger(__name__)

# DB設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sleep_tracker.db")
ENGINE = create_engine(f'sqlite:///{DB_PATH}', echo=False) # echo=TrueでSQLログを表示
Base = declarative_base()

# セッション作成
Session = sessionmaker(bind=ENGINE)

# --- データベースモデル定義 ---

class UserProfile(Base):
    """ユーザープロファイル (設定) テーブル"""
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    target_sleep_hours = Column(Float, default=7.5) # 目標睡眠時間 (時間)
    created_at = Column(DateTime, default=datetime.datetime.now)
    weather_city_jp = Column(String, default="東京都") # 天気予報の地域 (この設定が保持されます)

    def __repr__(self):
        return f"<UserProfile(id={self.id}, target_sleep_hours={self.target_sleep_hours})>"

class SleepRecord(Base):
    """睡眠記録データテーブル"""
    __tablename__ = 'sleep_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer) # ユーザーID (UserProfileのIDを参照)
    date = Column(Date, nullable=False) # 記録日 (通常は起床日)
    sleep_time = Column(DateTime, nullable=False) # 就寝時刻 (旧 sleep_datetime)
    wake_time = Column(DateTime, nullable=False) # 起床時刻 (旧 wake_datetime)
    sleep_duration_min = Column(Integer, nullable=False) # 睡眠時間 (分) (旧 duration_minutes)
    quality_rating = Column(Integer, nullable=False) # 目覚めの良さ (1-5) (旧 quality)
    memo = Column(String) # 自由メモ
    
    # 環境データ (OpenWeatherMapから取得)
    weather_city_name = Column(String) # ★追加: 天気予報に使用された都市名（日本語）
    weather_condition = Column(String) # (旧 weather_description)
    temp = Column(Float) # 気温 (摂氏) (旧 temperature_celsius)

    created_at = Column(DateTime, default=datetime.datetime.now)
    
    def __repr__(self):
        return f"<SleepRecord(date={self.date}, duration={self.sleep_duration_min}min)>"


def create_db_and_tables():
    """データベースファイルとテーブルを初期化/作成する"""
    try:
        # テーブルが存在しない場合のみ作成
        # 注: SQLiteでは、既存テーブルへのカラム追加（ALTER TABLE）は自動では行われません。
        # アプリケーションの再起動時にDBスキーマを変更する場合は、既存のDBファイルを削除するか、
        # Alembicなどのマイグレーションツールを使用する必要があります。
        Base.metadata.create_all(ENGINE)
        logger.info("Database and tables created or confirmed.")
    except OperationalError as e:
        logger.error(f"Failed to create tables: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during table creation: {e}")
