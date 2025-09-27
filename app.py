# -*- coding: utf-8 -*-
import sys
import datetime
import random
import logging
import time

# --- 外部設定ファイル (.env) ロード ---
from dotenv import load_dotenv 

# 分割したモジュールをインポート
from db_models import Session, UserProfile, SleepRecord
from chart_canvas import MplCanvas
from api_client import ApiClient 

# 外部ライブラリのインポート (PyQt5)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QDateTimeEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QSlider, QScrollArea, QSizePolicy, QTimeEdit
)
from PyQt5.QtCore import QDateTime, Qt, QTimer, QTime
from PyQt5.QtGui import QFont, QColor

# --- ログ設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 環境変数ロード (APIキーなどの読み込み) ---
load_dotenv() 

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

# --- メインアプリケーションクラス ---
class SleepTrackerApp(QMainWindow):
    """「眠れる森のアスカ」メインウィンドウ"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("眠れる森のアスカ v0.4 (AI機能動作確認中)")
        self.setGeometry(100, 100, 1000, 750)
        
        # APIクライアントの初期化 (この時点でAPIキーがロードされているはず)
        self.api_client = ApiClient() 
        self.db_session = Session()
        self.user_id = self._initialize_db()
        self.target_sleep_hours = self._get_target_sleep_hours()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Inter", 10))

        # タブの作成
        self._create_record_tab()
        self._create_report_tab()
        self._create_setting_tab() # ★★★ ここで設定タブが呼ばれる ★★★

        # タブ切り替え時のレポート更新を設定
        self.tab_widget.currentChanged.connect(self._on_tab_change)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addWidget(self.tab_widget)
        
        # タイマー設定 (RPA/自動化機能)
        self._setup_rpa_timer()
        
        # 起動時にデータをロード
        self._load_records() # 起動時データロード

    def _on_tab_change(self, index):
        """タブが切り替わったときに実行される処理"""
        if index == 1: # レポートタブ
            self._load_records() # レポートタブに切り替わったらデータを再ロード（グラフ更新）

    # --- DB初期化・ユーザープロファイル管理 ---
    def _initialize_db(self):
        """データベースを初期化し、ユーザープロファイルをロードまたは作成する"""
        try:
            profile = self.db_session.query(UserProfile).first()
            if not profile:
                profile = UserProfile()
                self.db_session.add(profile)
                self.db_session.commit()
                logger.info("New user profile created.")
            return profile.id
        except Exception as e:
            logger.error(f"DB initialization error: {e}")
            return None

    def _get_target_sleep_hours(self):
        """データベースから目標睡眠時間を取得する"""
        try:
            profile = self.db_session.query(UserProfile).filter(UserProfile.id == self.user_id).first()
            return profile.target_sleep_hours if profile else 7.5
        except Exception as e:
            logger.error(f"Failed to get target sleep hours: {e}")
            return 7.5

    def _update_target_sleep_hours(self, hours):
        """目標睡眠時間を更新し、インスタンス変数にも反映する"""
        try:
            profile = self.db_session.query(UserProfile).filter(UserProfile.id == self.user_id).first()
            if profile:
                profile.target_sleep_hours = hours
                self.db_session.commit()
                self.target_sleep_hours = hours
                self.setting_target_label.setText(f"目標睡眠時間: {hours:.1f} 時間")
                self.setting_target_slider.setValue(int(hours * 10))
                logger.info(f"Target sleep hours updated to {hours}")
                self._update_report_tab() # レポートの推奨時刻を更新
        except Exception as e:
            logger.error(f"Failed to update target sleep hours: {e}")


    # --- GUIタブ作成メソッド ---
    def _create_record_tab(self):
        """記録タブを作成する"""
        self.record_tab = QWidget()
        layout = QVBoxLayout(self.record_tab)
        
        # 入力フォーム
        form_layout = QHBoxLayout()
        
        # 睡眠時刻
        sleep_label = QLabel("💤 入眠時刻:")
        self.sleep_time_input = QDateTimeEdit(QDateTime.currentDateTime().addSecs(-8 * 3600))
        self.sleep_time_input.setCalendarPopup(True)
        self.sleep_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        form_layout.addWidget(sleep_label)
        form_layout.addWidget(self.sleep_time_input)

        # 起床時刻
        wake_label = QLabel("⏰ 起床時刻:")
        self.wake_time_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.wake_time_input.setCalendarPopup(True)
        self.wake_time_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        form_layout.addWidget(wake_label)
        form_layout.addWidget(self.wake_time_input)
        
        # 目覚めの良さ (1-5)
        quality_label = QLabel("✨ 目覚めの良さ (1-5):")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["5 (最高)", "4 (良い)", "3 (普通)", "2 (悪い)", "1 (最悪)"])
        self.quality_combo.setCurrentIndex(0) # デフォルトは「最高」
        form_layout.addWidget(quality_label)
        form_layout.addWidget(self.quality_combo)
        
        layout.addLayout(form_layout)
        
        # メモ
        memo_layout = QHBoxLayout()
        memo_label = QLabel("✏️ メモ:")
        self.memo_input = QLineEdit()
        self.memo_input.setPlaceholderText("その日の気分や出来事をメモ...")
        memo_layout.addWidget(memo_label)
        memo_layout.addWidget(self.memo_input)
        layout.addLayout(memo_layout)
        
        # 登録ボタン
        self.save_button = QPushButton("💾 記録を登録")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #0077B6;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005A8D;
            }
        """)
        self.save_button.clicked.connect(self.save_sleep_record)
        layout.addWidget(self.save_button)
        
        # 記録済みテーブル
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "日付", "入眠時刻", "起床時刻", "睡眠時間(分)", "目覚め", "天気", "温度(°C)"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch) # 日付をストレッチ
        
        layout.addWidget(QLabel("--- 過去の記録 ---"))
        layout.addWidget(self.table)

        self.tab_widget.addTab(self.record_tab, "記録 (Record)")

    def _create_report_tab(self):
        """レポートタブを作成する"""
        self.report_tab = QWidget()
        layout = QVBoxLayout(self.report_tab)
        
        # ヘッダーと目標表示
        header_layout = QHBoxLayout()
        
        # 理想入眠時刻計算エリア
        ideal_time_group = QHBoxLayout()
        self.target_wake_time_input = QTimeEdit(QTime.currentTime())
        self.target_wake_time_input.setTime(QTime(7, 0)) # デフォルトは朝7時
        self.target_wake_time_input.setDisplayFormat("hh:mm")
        self.target_wake_time_input.timeChanged.connect(self._update_report_tab)
        wake_label = QLabel("明日目覚めたい時刻:")
        ideal_time_group.addWidget(wake_label)
        ideal_time_group.addWidget(self.target_wake_time_input)
        self.ideal_bedtime_label = QLabel("🛌 理想の入眠時刻: --:--")
        self.ideal_bedtime_label.setFont(QFont("Inter", 16, QFont.Bold))
        self.ideal_bedtime_label.setStyleSheet("color: #FF5A5F; padding: 10px; border: 2px solid #FF5A5F; border-radius: 8px;")
        ideal_time_group.addWidget(self.ideal_bedtime_label)
        header_layout.addLayout(ideal_time_group)
        
        # 平均睡眠時間と目標時間の表示
        self.avg_duration_label = QLabel("平均睡眠: -- min (目標: -- 時間)")
        header_layout.addWidget(self.avg_duration_label)

        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # グラフエリア
        self.canvas = MplCanvas(self, width=8, height=5, dpi=100)
        layout.addWidget(self.canvas)
        
        # --- AIアドバイスエリア ---
        advice_group = QVBoxLayout()
        advice_title = QLabel("🤖 アスカの睡眠アドバイス")
        advice_title.setFont(QFont("Inter", 12, QFont.Bold))
        advice_title.setStyleSheet("color: #0077B6;")
        advice_group.addWidget(advice_title)

        self.advice_button = QPushButton("✨ 過去7日間の記録からアドバイスを生成")
        self.advice_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.advice_button.clicked.connect(self.generate_sleep_advice)
        advice_group.addWidget(self.advice_button)

        self.advice_label = QLabel("ここにAIによる分析結果とアドバイスが表示されます。")
        self.advice_label.setWordWrap(True)
        self.advice_label.setStyleSheet("padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px;")
        self.advice_label.setTextInteractionFlags(Qt.TextSelectableByMouse) # テキスト選択を可能にする

        # スクロールエリアを導入して、長いテキストに対応
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(150)
        scroll_area.setWidget(self.advice_label)
        advice_group.addWidget(scroll_area)
        
        layout.addLayout(advice_group)
        
        self.tab_widget.addTab(self.report_tab, "レポート & AIアドバイス")
        
        # 初期ロード時にレポートを更新 (データがないため、初回起動時は何もしない)
        # self._update_report_tab()

    def _create_setting_tab(self):
        """設定タブを作成する"""
        self.setting_tab = QWidget()
        layout = QVBoxLayout(self.setting_tab)
        
        # 目標睡眠時間設定
        target_sleep_layout = QHBoxLayout()
        
        self.setting_target_label = QLabel(f"目標睡眠時間: {self.target_sleep_hours:.1f} 時間")
        self.setting_target_label.setFont(QFont("Inter", 12))
        
        self.setting_target_slider = QSlider(Qt.Horizontal)
        self.setting_target_slider.setMinimum(40) # 4.0時間 (40 * 0.1)
        self.setting_target_slider.setMaximum(120) # 12.0時間 (120 * 0.1)
        self.setting_target_slider.setValue(int(self.target_sleep_hours * 10))
        self.setting_target_slider.setSingleStep(5) # 0.5時間刻み
        self.setting_target_slider.setTickInterval(10)
        self.setting_target_slider.setTickPosition(QSlider.TicksBelow)
        
        self.setting_target_slider.valueChanged.connect(self._on_target_slider_changed)
        
        target_sleep_layout.addWidget(self.setting_target_label)
        target_sleep_layout.addWidget(self.setting_target_slider)
        
        layout.addLayout(target_sleep_layout)

        # ★★★ 追記箇所: 天気予報の都市設定 ★★★
        weather_layout = QHBoxLayout()
        weather_label = QLabel("📍 天気予報の地域設定:")
        self.weather_city_combo = QComboBox()
        
        # 47都道府県のリストをコンボボックスに追加
        self.weather_city_combo.addItems(JAPAN_MAJOR_CITIES.keys())
        # デフォルトで東京都が選択されるように設定
        self.weather_city_combo.setCurrentText("東京都")
        
        weather_layout.addWidget(weather_label)
        weather_layout.addWidget(self.weather_city_combo)
        layout.addLayout(weather_layout)
        # ★★★ 追記ここまで ★★★

        # 設定保存ボタン (スライダー操作で自動保存されるため不要だが一応配置)
        save_settings_button = QPushButton("設定を保存")
        save_settings_button.clicked.connect(lambda: self._update_target_sleep_hours(self.target_sleep_hours))
        layout.addWidget(save_settings_button)
        
        layout.addStretch(1)
        
        self.tab_widget.addTab(self.setting_tab, "設定 (Settings)")

    def _on_target_slider_changed(self, value):
        """スライダー値が変更されたときにラベルと設定を更新する"""
        hours = value / 10.0
        self.setting_target_label.setText(f"目標睡眠時間: {hours:.1f} 時間")
        self._update_target_sleep_hours(hours) # 値が変わるたびにDBを更新

    # --- RPA/自動化 (モーニングコール) 機能 ---
    def _setup_rpa_timer(self):
        """1分ごとにモーニングコールをチェックするタイマーを設定"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_morning_call)
        self.timer.start(60000) # 60000ms = 1分

    def check_morning_call(self):
        """現在の時刻がモーニングコール時刻かどうかをチェックする"""
        current_time = datetime.datetime.now().time()
        
        # 修正: レポートタブで設定された「明日目覚めたい時刻」を使用
        target_time_qtime = self.target_wake_time_input.time() # QTimeEditから時刻を取得

        # 時刻を比較
        if current_time.hour == target_time_qtime.hour() and current_time.minute == target_time_qtime.minute():
            QMessageBox.information(
                self,
                "🔔 モーニングコール",
                "アスカ: 理想の目覚め時刻です！今日の睡眠記録をつけてみましょう！"
            )
            logger.info("Morning call triggered.")

    # --- データ処理と表示 ---
    def _load_records(self):
        """データベースから全ての睡眠記録をロードし、テーブルとレポートを更新する"""
        try:
            records = self.db_session.query(SleepRecord).filter(SleepRecord.user_id == self.user_id).all()
            
            # テーブルの更新
            self.table.setRowCount(len(records))
            
            durations = []
            scores = []
            dates = []
            
            # 最新の7件だけを処理対象とする
            recent_records = records[-7:] 
            
            for row_idx, record in enumerate(records):
                # データをリストに追加 (レポート用)
                durations.append(record.sleep_duration_min)
                scores.append(record.quality_rating * 20) # 1-5を20-100に変換
                dates.append(record.date.strftime("%m/%d"))
                
                # テーブル表示
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(record.id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(record.date.strftime("%Y-%m-%d")))
                self.table.setItem(row_idx, 2, QTableWidgetItem(record.sleep_time.strftime("%H:%M")))
                self.table.setItem(row_idx, 3, QTableWidgetItem(record.wake_time.strftime("%H:%M")))
                self.table.setItem(row_idx, 4, QTableWidgetItem(f"{record.sleep_duration_min / 60:.1f} 時間 ({record.sleep_duration_min}分)"))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(record.quality_rating)))
                self.table.setItem(row_idx, 6, QTableWidgetItem(record.weather_condition or "N/A"))
                self.table.setItem(row_idx, 7, QTableWidgetItem(f"{record.temp:.1f}" if record.temp is not None else "N/A"))

            # レポートの更新
            # 最新7件のデータのみを渡す
            self._update_report_tab(
                durations[-7:], 
                scores[-7:], 
                dates[-7:]
            )

        except Exception as e:
            logger.error(f"Failed to load records: {e}")

    def save_sleep_record(self):
        """入力された睡眠記録をデータベースに保存し、テーブルを更新する"""
        try:
            sleep_dt = self.sleep_time_input.dateTime().toPyDateTime()
            wake_dt = self.wake_time_input.dateTime().toPyDateTime()
            
            # 睡眠時間の計算 (分)
            duration = wake_dt - sleep_dt
            duration_min = int(duration.total_seconds() / 60)
            
            if duration_min <= 0:
                QMessageBox.warning(self, "エラー", "起床時刻は入眠時刻より後に設定してください。")
                return
            
            # 目覚めの良さ (1-5)
            quality_text = self.quality_combo.currentText()
            quality_rating = int(quality_text[0])
            
            memo = self.memo_input.text()
            
            # ★★★ 修正箇所: 選択された都市名を取得し、APIに渡す ★★★
            selected_city_jp = self.weather_city_combo.currentText()
            # 内部のAPI呼び出し用に英語の都市名に変換
            city_en = JAPAN_MAJOR_CITIES.get(selected_city_jp, "Tokyo") 
            
            # OpenWeatherMap APIから気象データを取得
            weather_condition, temp = self.api_client.get_weather_data(city=city_en, country="JP")

            # 新しい記録を作成
            new_record = SleepRecord(
                user_id=self.user_id,
                date=wake_dt.date(),
                sleep_time=sleep_dt,
                wake_time=wake_dt,
                sleep_duration_min=duration_min,
                quality_rating=quality_rating,
                memo=memo,
                weather_condition=weather_condition,
                temp=temp
            )
            
            self.db_session.add(new_record)
            self.db_session.commit()
            logger.info("Sleep record saved successfully.")
            
            QMessageBox.information(self, "登録完了", f"睡眠記録を保存しました。\n地域: {selected_city_jp}\n睡眠時間: {duration_min // 60}時間 {duration_min % 60}分")
            
            # UIを更新
            self._load_records()
            self.memo_input.clear() # メモをクリア
            
        except Exception as e:
            QMessageBox.critical(self, "データベースエラー", f"記録の保存中にエラーが発生しました: {e}")
            logger.error(f"Error saving record: {e}")

    # --- レポート機能のロジック ---
    def _calculate_ideal_bedtime(self):
        """
        目標起床時刻と目標睡眠時間に基づき、理想的な入眠時刻を計算する。
        戻り値: datetime.datetime (理想の入眠時刻)
        """
        target_wake_time = self.target_wake_time_input.time()
        
        # 今日の日付をベースに、目標起床時刻のdatetimeオブジェクトを作成
        now_date = datetime.datetime.now().date()
        target_dt = datetime.datetime.combine(now_date, datetime.time(target_wake_time.hour(), target_wake_time.minute()))
        
        # 目標睡眠時間（時間）をtimedeltaに変換
        target_duration = datetime.timedelta(hours=self.target_sleep_hours)
        
        # 理想入眠時刻を計算
        ideal_bedtime = target_dt - target_duration
        
        # もし計算結果が昨日になってしまった場合（例：起床時刻が深夜の場合）は、日付を調整する
        if ideal_bedtime.hour > 12 and target_wake_time.hour() < 12:
              ideal_bedtime = ideal_bedtime - datetime.timedelta(days=1)
        
        logger.info(f"Ideal bedtime calculated: {ideal_bedtime.strftime('%Y-%m-%d %H:%M')}")
        return ideal_bedtime

    def _update_report_tab(self, durations=None, scores=None, dates=None):
        """レポートタブのグラフと推奨時刻を更新する"""
        
        # 理想入眠時刻の更新
        ideal_bedtime = self._calculate_ideal_bedtime()
        self.ideal_bedtime_label.setText(f"🛌 理想の入眠時刻: {ideal_bedtime.strftime('%H:%M')}")
        
        # グラフデータの更新
        if durations is not None and scores is not None and len(durations) > 0:
            avg_min = sum(durations) / len(durations)
            avg_hour = avg_min / 60
            
            self.avg_duration_label.setText(
                f"過去 {len(durations)}日の平均睡眠: {avg_hour:.1f} 時間 (目標: {self.target_sleep_hours:.1f} 時間)"
            )
            
            # グラフ描画
            self.canvas.plot_sleep_data(dates, durations, scores)
        else:
            self.avg_duration_label.setText("データ不足 (記録を登録してください)")
            self.canvas.clear_plot()
            
    # --- AIアドバイザー機能 ---
    def generate_sleep_advice(self):
        """
        過去の睡眠記録をGeminiに渡し、睡眠改善のアドバイスを取得する。
        """
        # 画面上に処理中メッセージを表示
        self.advice_label.setText("アスカ: 分析中です...少々お待ちください。")
        self.advice_label.setStyleSheet("padding: 10px; border: 1px solid #FFC107; background-color: #FFF3E0; border-radius: 5px;")
        
        # 過去7日間の記録を取得
        records = self.db_session.query(SleepRecord).filter(SleepRecord.user_id == self.user_id).order_by(SleepRecord.date.desc()).limit(7).all()
        
        if not records:
            QMessageBox.warning(self, "データ不足", "AIアドバイスを生成するには、最低1件の睡眠記録が必要です。")
            self.advice_label.setText("アスカ: ごめんなさい、アドバイスを生成するための睡眠記録データが見つかりません。")
            return
            
        # データを整形してプロンプトに追加
        data_summary = "【過去の睡眠データ（最新7件）】\n"
        for i, record in enumerate(reversed(records)): # 古いものから順に
            duration_h = record.sleep_duration_min / 60
            data_summary += (
                f"日付 {record.date.strftime('%Y-%m-%d')}: "
                f"就寝 {record.sleep_time.strftime('%H:%M')}, "
                f"起床 {record.wake_time.strftime('%H:%M')}, "
                f"睡眠時間 {duration_h:.1f}時間, "
                f"目覚め評価 {record.quality_rating}/5, "
                f"メモ: {record.memo}, "
                f"起床時天気: {record.weather_condition}, "
                f"気温: {record.temp:.1f}°C\n"
            )
        
        # ユーザーの目標情報を追加
        target_info = f"\n【ユーザーの目標】\n目標睡眠時間: {self.target_sleep_hours:.1f} 時間"

        # Geminiへのシステムプロンプト
        system_prompt = (
            "あなたはユーザーの専属睡眠アドバイザー「アスカ」です。親しみやすい口調（語尾に「ね」「よ」などを使う）で、専門的な知識に基づいてアドバイスを提供してください。"
            "提供された過去の睡眠データを分析し、睡眠時間と質の傾向、そして天気との関連性などから、具体的に何を改善すべきか提案してください。長すぎず、要点をまとめた一連のメッセージとして応答してください。"
        )
        
        # Geminiへのユーザー要求
        user_query = (
            f"私の睡眠記録と目標情報に基づき、親しみやすいトーンで睡眠改善のための分析とアドバイスを日本語で提供してください。\n"
            f"{data_summary}\n"
            f"{target_info}\n"
            "特に、平均睡眠時間と目標時間の差、目覚めの良さの傾向について重点的に分析してください。"
        )

        logger.info("Gemini advice generation started...")
        
        # API呼び出しは時間がかかるため、別スレッドでの実行が理想的だが、ここでは同期的に実行
        advice_text = self.api_client.get_gemini_advice(system_prompt, user_query)
        
        # 結果を画面に表示
        self.advice_label.setText(advice_text)
        self.advice_label.setStyleSheet("padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9; border-radius: 5px;")
        logger.info("Gemini advice generation finished.")
        
# --- 実行 ---
if __name__ == "__main__":
    import db_models
    db_models.create_db_and_tables() # データベースの初期化をここでもう一度実行
    
    app = QApplication(sys.argv)
    window = SleepTrackerApp()
    window.show()
    sys.exit(app.exec_())
