# -*- coding: utf-8 -*-
# sleep_tracker_window.py
import sys
import logging
# PyQt5のウィジェットとレイアウト
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget # ★修正: QHBoxLayoutを追加
)
# QFontとQIconはQtGuiモジュールに移動しています
from PyQt5.QtGui import QFont, QIcon 
# QTimeやQtなど、その他の基本的なクラスはQtCoreに残ります
from PyQt5.QtCore import QTimer, QDateTime, Qt, QTime

# 分割したモジュールとMixinをインポート
from db_models import Session
from chart_canvas import MplCanvas
from api_client import ApiClient 
from ui_creator import UICreatorMixin
from sleep_logic_mixin import SleepLogicMixin

logger = logging.getLogger(__name__)

# --- メインアプリケーションクラス ---
class SleepTrackerApp(QMainWindow, UICreatorMixin, SleepLogicMixin):
    """「眠れる森のアスカ」メインウィンドウ"""
    
    def __init__(self, JAPAN_MAJOR_CITIES: dict):
        super().__init__()
        self.setWindowTitle("眠れる森のアスカ v0.4 (AI機能動作確認中)")
        # アプリケーションのアイコンを設定 (必要に応じてファイルパスを指定)
        # self.setWindowIcon(QIcon('path/to/icon.png')) 
        self.setGeometry(100, 100, 1000, 750)
        
        # 外部定数をインスタンス変数に格納 (Mixinからアクセス可能にするため)
        self.JAPAN_MAJOR_CITIES = JAPAN_MAJOR_CITIES
        
        # --- 依存オブジェクトの初期化 ---
        self.api_client = ApiClient() 
        
        # DB初期化とユーザープロファイルロード
        self.db_session = Session() # Sessionを初期化
        
        # Mixinの初期化メソッドを呼び出し、ユーザーIDと地域設定を取得
        self.user_id, self.weather_city_jp = self._initialize_db_and_data() 
        
        # --- UIの初期化 ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Inter", 10))
        
        # グラフキャンバスもここで初期化（他のMixinから参照されるため）
        self.canvas = MplCanvas(self, width=8, height=5, dpi=100)

        # タブの作成 (UICreatorMixinから呼び出し)
        self._create_record_tab()
        self._create_report_tab()
        self._create_setting_tab(self.JAPAN_MAJOR_CITIES) # 定数を渡す
        
        # --- シグナルとスロットの接続 ---
        self._connect_signals()
        
        # メインレイアウト (★修正箇所: QHBoxLayoutに変更し、キャラクターウィジェットを追加)
        main_layout = QHBoxLayout(self.central_widget)
        
        # 1. キャラクターウィジェットを作成し、左側に追加 (比率1)
        character_widget = self._create_character_widget()
        main_layout.addWidget(character_widget, 1) 
        
        # 2. タブウィジェットを右側に追加 (比率2)
        main_layout.addWidget(self.tab_widget, 2) 
        
        # タイマー設定 (SleepLogicMixinから呼び出し)
        self._setup_rpa_timer()
        
        # 起動時にデータをロード (SleepLogicMixinから呼び出し)
        self._load_records()

    def _on_target_slider_changed(self, value: int):
        """
        設定タブのスライダー値が変更されたときに呼び出され、目標睡眠時間を更新する。
        スライダー値 (int, e.g., 75) を時間 (float, e.g., 7.5) に変換する。
        """
        # 値を10で割って時間（float）に変換
        hours = value / 10.0
        
        # UIラベルを即座に更新
        self.setting_target_label.setText(f"目標睡眠時間: {hours:.1f} 時間")
        
        # SleepLogicMixinのメソッドを呼び出し、DBとインスタンス変数を更新
        self._update_target_sleep_hours(hours)
    
    # ---

    def _connect_signals(self):
        """全てのUIシグナルをロジックメソッドに接続する"""
        
        # 記録タブ
        self.save_button.clicked.connect(self.save_sleep_record)

        # レポートタブ
        self.target_wake_time_input.timeChanged.connect(self._update_report_tab)
        self.advice_button.clicked.connect(self.generate_sleep_advice)
        self.tab_widget.currentChanged.connect(self._on_tab_change)

        # 設定タブ
        self.setting_target_slider.valueChanged.connect(self._on_target_slider_changed)
        self.weather_city_combo.currentIndexChanged.connect(self._update_weather_city)
        
    def _on_tab_change(self, index: int):
        """タブが切り替わったときに実行される処理"""
        if index == 1: # レポートタブ
            # 常に最新のデータをロードし、グラフを更新
            self._load_records() 
        
    def _setup_rpa_timer(self):
        """
        モーニングコールチェック用のタイマーをセットアップする。
        1分ごとにチェックを行う。
        """
        self.timer = QTimer(self)
        # check_morning_call は SleepLogicMixin に定義されている
        self.timer.timeout.connect(self.check_morning_call)
        self.timer.start(60000) # 60000ms = 1分
