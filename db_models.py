# -*- coding: utf-8 -*-
import datetime
import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
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

    def __repr__(self):
        return f"<UserProfile(id={self.id}, target_sleep_hours={self.target_sleep_hours})>"

class SleepRecord(Base):
    """睡眠記録データテーブル"""
    __tablename__ = 'sleep_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer) # ユーザーID (UserProfileのIDを参照)
    date = Column(Date, nullable=False) # 記録日 (通常は起床日)
    sleep_time = Column(DateTime, nullable=False) # 就寝時刻
    wake_time = Column(DateTime, nullable=False)  # 起床時刻
    sleep_duration_min = Column(Integer, nullable=False) # 睡眠時間 (分)
    quality_rating = Column(Integer, nullable=False) # 目覚めの良さ (1-5)
    memo = Column(String) # 自由メモ
    
    # 環境データ (OpenWeatherMapから取得)
    weather_condition = Column(String)
    temp = Column(Float) # 気温 (摂氏)

    created_at = Column(DateTime, default=datetime.datetime.now)
    
    def __repr__(self):
        return f"<SleepRecord(date={self.date}, duration={self.sleep_duration_min}min)>"


def create_db_and_tables():
    """データベースファイルとテーブルを初期化/作成する"""
    try:
        # テーブルが存在しない場合のみ作成
        Base.metadata.create_all(ENGINE)
        logger.info("Database and tables created or confirmed.")
    except OperationalError as e:
        logger.error(f"Failed to create tables: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during table creation: {e}")

# --- 補足 ---
# app.py内で 'import db_models' した際、テーブル作成処理が自動的に走るわけではありません。
# app.pyの初期化メソッド内で db_models.create_db_and_tables() が呼び出され、
# 確実にテーブルが作成されるようになっています。
