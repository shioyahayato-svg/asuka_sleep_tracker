# -*- coding: utf-8 -*-
# ui_creator.py
import datetime
import base64 
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, 
    QLabel, QLineEdit, QDateTimeEdit, QDateEdit, QTimeEdit, QPushButton, 
    QSlider, QSpinBox, QComboBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QFrame
)
from PyQt5.QtGui import QFont, QColor, QPixmap 
from PyQt5.QtCore import Qt, QDateTime, QTime, QByteArray 

# assets.py から画像データをインポート
try:
    # ユーザーが指定した定数名でBase64画像データをインポート
    from assets import ASUKA_IMAGE_BASE64
except ImportError:
    # assets.py が存在しないか、定数名が一致しない場合のフォールバック
    ASUKA_IMAGE_BASE64 = ""
    print("Warning: assets.py not found or ASUKA_IMAGE_BASE64 is missing.")

# --- Base64が空の場合のプレースホルダー画像を定義 ---
# 1x1の透明なPNG画像
PLACEHOLDER_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

class UICreatorMixin:
    """
    SleepTrackerAppのためのUIウィジェットを作成するMixinクラス。
    """

    def _create_character_widget(self):
        """左側に表示する子の立ち絵エリアを作成する"""
        
        # --- ★DEBUG: 処理開始ログ★ ---
        print("\n--- DEBUG: Starting character widget image loading ---")
        
        character_frame = QFrame()
        character_frame.setFrameShape(QFrame.StyledPanel)
        character_frame.setStyleSheet("""
            QFrame {
                background-color: #E6F7FF; /* キャラクターエリアの背景色（水色） */
                border-radius: 12px;
                border: 1px solid #B3E5FC;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(character_frame)
        
        # 立ち絵を表示するためのQLabel
        self.character_label = QLabel()
        self.character_label.setAlignment(Qt.AlignCenter)
        self.character_label.setMinimumHeight(400) 
        
        # キャラクターからのコメントエリア（最小限のスペース確保）
        self.character_comment = QLabel("今日の記録を待ってるよ！")
        self.character_comment.setAlignment(Qt.AlignCenter)
        self.character_comment.setWordWrap(True)
        self.character_comment.setStyleSheet("background-color: white; border: 1px solid #B3E5FC; border-radius: 8px; padding: 10px; font-style: italic;")
        
        # --- Base64画像のデコードと表示処理 ---
        image_base64_data = ASUKA_IMAGE_BASE64 if ASUKA_IMAGE_BASE64 else PLACEHOLDER_IMAGE_BASE64

        if image_base64_data:
            data_source = 'ASUKA_IMAGE_BASE64 (User Data)' if ASUKA_IMAGE_BASE64 else 'PLACEHOLDER_IMAGE_BASE64'
            print(f"DEBUG: Using data source: {data_source}")
            
            try:
                # Base64データをデコード
                image_data = base64.b64decode(image_base64_data)
                pixmap = QPixmap()
                # QByteArrayを使用して画像をロード
                pixmap.loadFromData(QByteArray(image_data))
                
                if not pixmap.isNull():
                    print("DEBUG: Image loaded successfully (QPixmap is valid).")
                    
                    # 適切なサイズにスケーリング
                    scaled_pixmap = pixmap.scaled(
                        400, 500, # 最大サイズを設定
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.character_label.setPixmap(scaled_pixmap)
                    self.character_label.setStyleSheet("margin-top: 10px;")
                    
                    if image_base64_data == PLACEHOLDER_IMAGE_BASE64:
                        # プレースホルダーが使われた場合の警告表示
                        print("DEBUG: Showing placeholder warning message.")
                        self.character_comment.setText("画像ロード中... (assets.pyにBase64データをセットしてください)")
                        self.character_comment.setStyleSheet("background-color: white; border: 1px solid #FFC107; border-radius: 8px; padding: 10px; font-style: italic; color: #FFA000;")
                    else:
                        print("DEBUG: User's image is now displayed.")
                        # ユーザー画像が正常にロードされた場合、コメントはデフォルトの「今日の記録を待ってるよ！」が使われます。
                        
                else:
                    # QPixmapがNullの場合 (デコードできたが画像形式として不正)
                    print("DEBUG ERROR: QPixmap is null (Data is not a recognized image format: PNG/JPEG/etc.).")
                    self.character_label.setText("画像をロードできませんでした (無効な画像データか、Base64文字列が不正です)")
                    self.character_label.setFont(QFont("Inter", 12, QFont.Bold))
                    self.character_label.setStyleSheet("color: #CC0000; margin-top: 20px;")
                    self.character_comment.setText("❌ 画像のロードに失敗しました。Base64データを確認してください。")
                    self.character_comment.setStyleSheet("background-color: #FFF0F0; border: 1px solid #FF5A5F; border-radius: 8px; padding: 10px; font-style: italic; color: #CC0000;")
                    
            except Exception as e:
                # Base64デコード自体に失敗した場合
                print(f"DEBUG ERROR: Base64 decode failed: {type(e).__name__}: {e}")
                self.character_label.setText(f"画像デコードエラー: {type(e).__name__}が発生しました。")
                self.character_label.setFont(QFont("Inter", 12))
                self.character_label.setStyleSheet("color: #CC0000; margin-top: 20px;")
                self.character_comment.setText("❌ Base64文字列のデコードでエラーが発生しました。不正な文字が含まれている可能性があります。")
                self.character_comment.setStyleSheet("background-color: #FFF0F0; border: 1px solid #FF5A5F; border-radius: 8px; padding: 10px; font-style: italic; color: #CC0000;")
        else:
            # image_base64_dataが空の場合 (このパスは事実上PLACEHOLDER_IMAGE_BASE64で防がれていますが、念のため残す)
            print("DEBUG: Image data is completely empty (ASUKA_IMAGE_BASE64 is empty and PLACEHOLDER is not used).")
            self.character_label.setText("アスカ (画像未設定)") 
            self.character_label.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
            self.character_label.setFont(QFont("Inter", 16, QFont.Bold))
            self.character_label.setStyleSheet("color: #0077B6; margin-top: 20px; min-height: 400px;")
            self.character_comment.setText("今日の記録を待ってるよ！")
            
        # ------------------------------------
        
        layout.addWidget(self.character_comment)
        layout.addWidget(self.character_label, 1) # 立ち絵エリアを拡張
        layout.setContentsMargins(10, 10, 10, 10)
        
        return character_frame

    def _create_record_tab(self):
        """記録タブ (データ入力) のUIを作成する - モダン化"""
        record_tab = QWidget()
        # 全体をモダンなカード風にスタイル設定
        record_tab.setStyleSheet("""
            QWidget { 
                background-color: #FFFFFF; 
                border-radius: 12px; 
                padding: 20px;
                /*box-shadowはPyQtの標準機能では直接シミュレートが難しいため、境界線と背景で代用*/
            }
            QLabel { font-size: 11pt; color: #333333; }
            QDateEdit, QTimeEdit, QTextEdit { 
                border: 1px solid #CCCCCC; 
                border-radius: 6px; 
                padding: 8px; 
                background-color: #F9F9F9; 
            }
        """)
        
        layout = QGridLayout(record_tab)
        
        # --- 入力フォーム ---
        form_layout = QFormLayout()
        form_layout.setSpacing(18) # スペーシングを調整
        form_layout.setContentsMargins(10, 10, 10, 10)

        # 記録日
        self.record_date_input = QDateEdit(datetime.datetime.now().date())
        self.record_date_input.setCalendarPopup(True)
        self.record_date_input.setDisplayFormat("yyyy/MM/dd")
        form_layout.addRow("📅 記録日 (起床日):", self.record_date_input)

        # 就寝時刻 (デフォルト: 23:00)
        self.sleep_time_input = QTimeEdit(QTime(23, 0))
        self.sleep_time_input.setDisplayFormat("HH:mm")
        form_layout.addRow("🌙 就寝時刻:", self.sleep_time_input)

        # 起床時刻 (デフォルト: 6:00)
        self.wake_time_input = QTimeEdit(QTime(6, 0))
        self.wake_time_input.setDisplayFormat("HH:mm")
        form_layout.addRow("☀️ 起床時刻:", self.wake_time_input)

        # 目覚めの良さ (品質) スライダー
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 5)
        self.quality_slider.setSingleStep(1)
        self.quality_slider.setValue(4) # 初期値: 4/5
        self.quality_slider.setTickInterval(1)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        
        # スライダーの見た目をモダンに
        self.quality_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ddd;
                height: 8px;
                border-radius: 4px;
                background: #f0f0f0;
            }
            QSlider::handle:horizontal {
                background: #0077B6; /* メインカラー */
                border: 1px solid #00568c;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        
        # 品質ラベル
        self.quality_label = QLabel("目覚めの良さ: 4 / 5 (良い)")
        self.quality_label.setFont(QFont("Inter", 10))
        # ここで tab_widget が存在しないため、シグナル接続はメインクラスに任せるか、
        # あるいは後で self に属性として追加されていることを前提とする。
        # 今回は Mixin の責務として self.quality_slider.valueChanged.connect を残します。
        try:
             self.quality_slider.valueChanged.connect(self._update_quality_label)
        except AttributeError:
             pass # メインクラスで connect されることを期待

        quality_layout = QVBoxLayout()
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_label)

        form_layout.addRow("✨ 目覚めの良さ (1-5):", quality_layout)

        # メモ
        self.memo_input = QTextEdit()
        self.memo_input.setPlaceholderText("メモ (例: 寝る前にカフェインを摂った、夢を見たなど)")
        self.memo_input.setFixedHeight(80)
        form_layout.addRow("📝 メモ:", self.memo_input)

        layout.addLayout(form_layout, 0, 0, 1, 2)
        
        # --- 保存ボタンとステータス ---
        self.save_button = QPushButton("💾 睡眠記録を保存")
        self.save_button.setFont(QFont("Inter", 12, QFont.Bold))
        # ボタンのスタイルを改善 (ホバー効果も)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #0077B6; 
                color: white; 
                padding: 12px; 
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #00568c;
            }
            QPushButton:pressed {
                background-color: #003F66;
            }
        """)
        layout.addWidget(self.save_button, 1, 0, 1, 2)
        
        self.status_label = QLabel("準備完了。データを入力してください。")
        self.status_label.setStyleSheet("color: #0077B6; font-style: italic; margin-top: 10px; padding: 5px;")
        layout.addWidget(self.status_label, 2, 0, 1, 2)

        # レイアウト調整
        layout.setRowStretch(0, 1) # フォーム部分を広げる
        layout.setContentsMargins(0, 0, 0, 0) 

        # self.tab_widget が Mixin 適用先のクラスで定義されていることを前提とする
        if hasattr(self, 'tab_widget'):
            self.tab_widget.addTab(record_tab, "記録")
        else:
             return record_tab # tab_widget がなければウィジェットを返す

    def _update_quality_label(self, value: int):
        """品質スライダーの値に応じてラベルテキストを更新する"""
        ratings = {
            1: "最低", 2: "悪い", 3: "普通", 4: "良い", 5: "最高"
        }
        self.quality_label.setText(f"目覚めの良さ: {value} / 5 ({ratings.get(value, '不明')})")

    # --- レポートタブ ---
    
    def _create_report_tab(self):
        """レポートタブ (グラフと分析) のUIを作成する - モダン化"""
        report_tab = QWidget()
        report_tab.setStyleSheet("background-color: #F7F7F7;") # 全体の背景を少しグレーに
        layout = QVBoxLayout(report_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 1. 週ナビゲーションと統計情報
        nav_stats_layout = QHBoxLayout()
        
        # ナビゲーションボタンのスタイル改善
        button_style = """
            QPushButton {
                background-color: #E0E0E0; 
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #CCCCCC;
            }
            QPushButton:disabled {
                background-color: #F0F0F0;
                color: #AAAAAA;
            }
        """
        
        self.prev_week_button = QPushButton("◀️ 前の週")
        self.prev_week_button.setStyleSheet(button_style)
        self.next_week_button = QPushButton("次の週 ▶️")
        self.next_week_button.setStyleSheet(button_style)
        self.next_week_button.setEnabled(False) # 未来の週は無効
        
        self.report_week_label = QLabel("YYYY/MM/DD 〜 YYYY/MM/DD")
        self.report_week_label.setFont(QFont("Inter", 12, QFont.Bold))
        self.report_week_label.setAlignment(Qt.AlignCenter)
        self.report_week_label.setStyleSheet("color: #444444;")

        nav_stats_layout.addWidget(self.prev_week_button)
        nav_stats_layout.addWidget(self.report_week_label)
        nav_stats_layout.addWidget(self.next_week_button)
        
        layout.addLayout(nav_stats_layout)
        
        # 統計ラベル (インフォメーションカード風)
        self.report_stats_label = QLabel("統計情報: ロード中...")
        self.report_stats_label.setFont(QFont("Inter", 10))
        self.report_stats_label.setWordWrap(True)
        self.report_stats_label.setStyleSheet("""
            QLabel {
                padding: 15px; 
                background-color: #FFFFFF; 
                border-radius: 10px; 
                border: 1px solid #EEEEEE;
                /* box-shadowの代わりにボーダーと背景を使用 */
                min-height: 50px;
            }
        """)
        layout.addWidget(self.report_stats_label)

        # 2. グラフ (MplCanvas)
        # self.canvas は Mixin 適用先のクラスで定義されていることを前提とする
        if hasattr(self, 'canvas'):
            self.canvas.setStyleSheet("border: 1px solid #E0E0E0; border-radius: 8px; background-color: white;")
            layout.addWidget(self.canvas) 
        else:
            # canvasがない場合のプレースホルダー
            canvas_placeholder = QLabel("グラフ表示エリア (MplCanvas未設定)")
            canvas_placeholder.setAlignment(Qt.AlignCenter)
            canvas_placeholder.setFixedHeight(300)
            canvas_placeholder.setStyleSheet("background-color: #F0F0F0; border: 1px dashed #AAAAAA; border-radius: 8px;")
            layout.addWidget(canvas_placeholder)
        
        # 3. 詳細テーブル (直近の記録)
        self.record_table = QTableWidget()
        self.record_table.setColumnCount(5)
        self.record_table.setHorizontalHeaderLabels(["記録日", "睡眠時間", "品質", "天気/気温", "メモ"])
        
        # テーブルのスタイル改善
        table_style = """
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #EEEEEE;
            }
            QHeaderView::section {
                background-color: #0077B6; /* ヘッダーをメインカラーに */
                color: white;
                padding: 5px;
                border: 1px solid #00568c;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #B3E5FC; /* 選択行を明るい青に */
                color: black;
            }
        """
        self.record_table.setStyleSheet(table_style)
        
        # テーブルの設定 (既存の設定を維持)
        self.record_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.record_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch) 
        self.record_table.setEditTriggers(QTableWidget.NoEditTriggers) 
        self.record_table.setSelectionBehavior(QTableWidget.SelectRows) 
        self.record_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        layout.addWidget(self.record_table)
        
        # 4. AIアドバイスセクション
        advice_group_layout = QGridLayout()
        advice_group_layout.setSpacing(10)
        
        self.target_wake_time_input = QTimeEdit(QTime(7, 0)) 
        self.target_wake_time_input.setDisplayFormat("HH:mm")
        self.target_wake_time_input.setStyleSheet("border: 1px solid #CCCCCC; border-radius: 6px; padding: 5px; background-color: #FFFFFF;")
        
        self.advice_button = QPushButton("💡 AIにアドバイスをもらう")
        # ボタンのスタイルを改善
        self.advice_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5A5F; /* アクセントカラー */
                color: white; 
                padding: 8px; 
                border-radius: 6px;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """)
        
        advice_group_layout.addWidget(QLabel("目標起床時間 (アラーム):"), 0, 0)
        advice_group_layout.addWidget(self.target_wake_time_input, 0, 1)
        advice_group_layout.addWidget(self.advice_button, 0, 2)
        
        self.advice_output = QTextEdit()
        self.advice_output.setReadOnly(True)
        self.advice_output.setPlaceholderText("AIによる睡眠の分析とアドバイスがここに表示されます。")
        self.advice_output.setFixedHeight(120)
        self.advice_output.setStyleSheet("border: 1px solid #B3E5FC; border-radius: 8px; padding: 10px; background-color: #E1F5FE;") # ソフトな青の背景

        layout.addLayout(advice_group_layout)
        layout.addWidget(self.advice_output)

        # self.tab_widget が Mixin 適用先のクラスで定義されていることを前提とする
        if hasattr(self, 'tab_widget'):
            self.tab_widget.addTab(report_tab, "レポート・分析")
        else:
             return report_tab # tab_widget がなければウィジェットを返す

    def _set_table_item(self, table, row, col, text):
        """QTableWidgetItemを中央寄せで設定するヘルパーメソッド"""
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, col, item)

    # --- 設定タブ ---
    
    def _create_setting_tab(self, major_cities: dict):
        """設定タブ (目標や地域設定) のUIを作成する - モダン化"""
        setting_tab = QWidget()
        setting_tab.setStyleSheet("""
            QWidget { 
                background-color: #FFFFFF; 
                border-radius: 12px; 
                padding: 20px;
            }
            QLabel { font-size: 11pt; color: #333333; }
            QComboBox { 
                border: 1px solid #CCCCCC; 
                border-radius: 6px; 
                padding: 6px; 
                background-color: #F9F9F9;
            }
        """)
        layout = QVBoxLayout(setting_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        
        # 1. 目標睡眠時間設定
        self.setting_target_label = QLabel("目標睡眠時間: 7.5 時間") 
        self.setting_target_label.setFont(QFont("Inter", 11, QFont.Bold))
        self.setting_target_slider = QSlider(Qt.Horizontal)
        self.setting_target_slider.setRange(40, 120) 
        self.setting_target_slider.setSingleStep(5)
        self.setting_target_slider.setValue(75) 
        self.setting_target_slider.setTickInterval(10)
        self.setting_target_slider.setTickPosition(QSlider.TicksBelow)

        # 設定スライダーの見た目をモダンに (アクセントカラーを使用)
        self.setting_target_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ddd;
                height: 8px;
                border-radius: 4px;
                background: #f0f0f0;
            }
            QSlider::handle:horizontal {
                background: #FF5A5F; /* アクセントカラー */
                border: 1px solid #E64A19;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        
        target_layout = QVBoxLayout()
        target_layout.addWidget(self.setting_target_label)
        target_layout.addWidget(self.setting_target_slider)
        
        form_layout.addRow("目標設定:", target_layout)
        
        # 2. 天気予報の地域設定
        self.weather_city_combo = QComboBox()
        self.weather_city_combo.addItems(list(major_cities.keys()))
        form_layout.addRow("天気予報の地域:", self.weather_city_combo)
        
        layout.addLayout(form_layout)
        
        # Spacer
        layout.addStretch(1)

        # self.tab_widget が Mixin 適用先のクラスで定義されていることを前提とする
        if hasattr(self, 'tab_widget'):
            self.tab_widget.addTab(setting_tab, "設定")
        else:
             return setting_tab # tab_widget がなければウィジェットを返す
        
    def _clear_record_form(self):
        """
        記録タブのフォームをデフォルト値にリセットする。
        記録保存後に呼び出される。
        """
        now = datetime.datetime.now()

        # 就寝時刻は23:00、起床時刻は6:00にリセット
        self.sleep_time_input.setTime(QTime(23, 0))
        self.wake_time_input.setTime(QTime(6, 0))
        
        # 記録日の設定 (今日の日付)
        self.record_date_input.setDate(now.date()) 
        
        # 品質とメモをリセット
        self.quality_slider.setValue(4) 
        self._update_quality_label(4) # ラベルを更新


        self.memo_input.clear()
