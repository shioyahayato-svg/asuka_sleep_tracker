# -*- coding: utf-8 -*-
# sleep_logic_mixin.py
import datetime
import logging
from datetime import timedelta, date 
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt5.QtCore import QDateTime, QTime, Qt

# DBモデルをインポート
from db_models import UserProfile, SleepRecord, create_db_and_tables

logger = logging.getLogger(__name__)

class SleepLogicMixin:
    """
    アプリケーションのコアロジック (DB操作, API連携, 時間計算, 通知) を扱うMixinクラス。
    SleepTrackerAppクラスに組み込まれて使用されます。
    """
    
    # ----------------------------------------------------
    # DB初期化とユーザープロファイル関連
    # ----------------------------------------------------

    def _initialize_db_and_data(self):
        """
        データベースの初期化と、ユーザープロファイルのロード/作成を行う。
        self.db_sessionが事前に初期化されている前提。
        """
        create_db_and_tables() # テーブルがなければ作成

        session = self.db_session
        user = session.query(UserProfile).filter_by(id=1).first()

        if not user:
            # ユーザーが存在しない場合は作成
            user = UserProfile(target_sleep_hours=7.5, weather_city_jp="東京都")
            session.add(user)
            session.commit()
            logger.info("New UserProfile created.")
            
        # インスタンス変数に格納
        self.target_sleep_hours = user.target_sleep_hours
        self.weather_city_jp = user.weather_city_jp

        # UIに初期値を反映させるために、設定タブのウィジェットに値をセット（後で`_connect_signals`後に実行される想定）
        try:
            # スライダーは 10倍で扱う (4.0 -> 40, 7.5 -> 75)
            slider_value = int(self.target_sleep_hours * 10)
            self.setting_target_slider.setValue(slider_value)
            self.setting_target_label.setText(f"目標睡眠時間: {self.target_sleep_hours:.1f} 時間")
            
            # 天気予報の地域を設定
            cities = list(self.JAPAN_MAJOR_CITIES.keys())
            if self.weather_city_jp in cities:
                index = cities.index(self.weather_city_jp)
                self.weather_city_combo.setCurrentIndex(index)
            
        except AttributeError:
            # ウィジェットが初期化されていない場合はスキップ
            logger.debug("UI widgets are not fully initialized yet. Skipping initial UI set.")

        return user.id, user.weather_city_jp


    def _update_target_sleep_hours(self, hours: float):
        """
        目標睡眠時間をDBとインスタンス変数に更新する。
        """
        self.target_sleep_hours = hours
        
        session = self.db_session
        user = session.query(UserProfile).filter_by(id=self.user_id).first()
        if user:
            user.target_sleep_hours = hours
            session.commit()
            logger.info(f"Updated target sleep hours to {hours:.1f}")
        
        # 目標が変わったので、レポートタブの表示も更新
        self._update_report_tab()

    def _update_weather_city(self, index: int):
        """
        設定タブのコンボボックスから選択された都市をDBに保存する。
        """
        city_jp = list(self.JAPAN_MAJOR_CITIES.keys())[index]
        self.weather_city_jp = city_jp
        
        session = self.db_session
        user = session.query(UserProfile).filter_by(id=self.user_id).first()
        if user:
            user.weather_city_jp = city_jp
            session.commit()
            self.status_label.setText(f"地域設定を '{city_jp}' に更新しました。")


    # ----------------------------------------------------
    # 睡眠記録の保存ロジック
    # ----------------------------------------------------

    def save_sleep_record(self):
        """
        記録タブのフォームからデータを取得し、SleepRecordとしてDBに保存する。
        """
        # 1. フォームデータの取得
        try:
            record_date = self.record_date_input.date().toPyDate()
            
            sleep_qtime = self.sleep_time_input.time()
            wake_qtime = self.wake_time_input.time()

            # QTimeをPythonのdatetime.timeに変換
            sleep_dt = datetime.datetime.combine(record_date, sleep_qtime.toPyTime())
            wake_dt = datetime.datetime.combine(record_date, wake_qtime.toPyTime())
            
            # 就寝時刻が日付をまたぐ場合を考慮 (例: 23:00就寝, 6:00起床 -> 6:00は翌日の時間)
            if wake_dt <= sleep_dt:
                wake_dt += timedelta(days=1)
            
            duration = wake_dt - sleep_dt
            duration_minutes = int(duration.total_seconds() / 60)
            
            if duration_minutes <= 60 or duration_minutes > (20 * 60): # 1時間未満または20時間以上の睡眠はエラー
                 QMessageBox.warning(self, "入力エラー", "睡眠時間が短すぎるか長すぎます。日付と時刻を確認してください。")
                 return
            
            quality_rating = self.quality_slider.value()
            memo = self.memo_input.toPlainText()
            
        except Exception as e:
            QMessageBox.critical(self, "データエラー", f"フォームデータの取得に失敗しました: {e}")
            logger.error(f"Form data acquisition failed: {e}")
            return
            
        # 2. 天気データの取得
        try:
            city_en = self.JAPAN_MAJOR_CITIES.get(self.weather_city_jp, "Tokyo")
            
            # OpenWeatherMapは現在時刻の天気を返す
            weather_data = self.api_client.get_weather_sync(city_en) 
            
            weather_condition = weather_data.get('description', '')
            temp = weather_data.get('temp_celsius')
            
        except Exception:
             # 天気APIが失敗しても記録はできるようにする
             weather_condition = "取得失敗"
             temp = None
             logger.warning("Weather data retrieval failed. Saving record without detailed weather.")
            
        # 3. DBへの保存
        new_record = SleepRecord(
            user_id=self.user_id,
            date=record_date,
            sleep_time=sleep_dt,
            wake_time=wake_dt,
            sleep_duration_min=duration_minutes,
            quality_rating=quality_rating,
            memo=memo,
            weather_city_name=self.weather_city_jp, # ★追加: 設定されている都市名（日本語）を保存
            weather_condition=weather_condition,
            temp=temp
        )

        session = self.db_session
        session.add(new_record)
        
        try:
            session.commit()
            logger.info(f"Sleep record for {record_date} saved successfully.")
            
            # 記録後にデータを再ロードし、UIを更新
            self._load_records(week_offset=self.current_week_offset) 

            # 記録フォームをクリア
            self._clear_record_form() 
            
            self.status_label.setText(f"✅ 睡眠記録 ({record_date}) が正常に保存されました！")

        except Exception as e:
            session.rollback()
            logger.error(f"DB transaction failed: {e}")
            self.status_label.setText("❌ 記録の保存中にデータベースエラーが発生しました。")

    # ----------------------------------------------------
    # レポート表示とデータロード
    # ----------------------------------------------------

    def _load_records(self, week_offset: int = 0):
        """
        指定された週の睡眠記録をDBからロードし、グラフと表を更新する。
        """
        # 週の範囲を計算
        today = date.today()
        # 月曜日を週の始まりとする (0=月曜, 6=日曜)
        start_of_current_week = today - timedelta(days=today.weekday())
        
        # オフセットを適用して表示対象の週の範囲を決定
        start_date = start_of_current_week + timedelta(weeks=week_offset)
        end_date = start_date + timedelta(days=6) # 日曜日まで

        # UIの週表示ラベルを更新
        self.report_week_label.setText(f"{start_date.strftime('%Y/%m/%d')} 〜 {end_date.strftime('%Y/%m/%d')}")
        
        # DBからデータを取得
        session = self.db_session
        self.sleep_records_data = session.query(SleepRecord) \
                                         .filter(SleepRecord.date.between(start_date, end_date)) \
                                         .order_by(SleepRecord.date) \
                                         .all()
        
        logger.info(f"Loaded {len(self.sleep_records_data)} records for week offset {week_offset}.")

        # データをロードした後、レポートタブを更新
        self._update_report_tab()

    def _update_report_tab(self):
        """
        ロードされたデータ (self.sleep_records_data) に基づき、グラフと表を更新する。
        """
        records = self.sleep_records_data
        
        # データがなければ空のグラフとテーブルで更新
        if not records:
            self.canvas.plot_sleep_data([], [], [])
            self.report_stats_label.setText(f"**記録日数:** 0 日 / **平均睡眠:** N/A / **平均満足度:** N/A")
            self._update_record_table([])
            return

        dates = [r.date.strftime("%a") for r in records] # 曜日に変換 (Mon, Tue...)
        durations_min = [r.sleep_duration_min for r in records]
        scores_pct = [(r.quality_rating / 5) * 100 for r in records]
        
        # グラフの更新
        self.canvas.plot_sleep_data(dates, durations_min, scores_pct)
        
        # 統計情報の計算
        total_duration = sum(durations_min)
        avg_duration_min = total_duration / len(records)
        avg_quality = sum(r.quality_rating for r in records) / len(records)

        # UIラベルの更新
        self.report_stats_label.setText(
            f"**記録日数:** {len(records)} 日"
            f" / **平均睡眠:** {avg_duration_min / 60:.1f} 時間"
            f" / **平均満足度:** {avg_quality:.1f} / 5"
        )
        
        # 詳細テーブルの更新
        self._update_record_table(records)

    def _update_record_table(self, records):
        """詳細な睡眠記録をテーブルウィジェットに表示する"""
        table = self.record_table
        table.setRowCount(len(records))
        
        for i, record in enumerate(records):
            # 記録日 (曜日)
            day_of_week = record.date.strftime("%a")
            self._set_table_item(table, i, 0, f"{record.date.strftime('%m/%d')} ({day_of_week})")
            # 睡眠時間 (H:MM)
            duration_h = record.sleep_duration_min // 60
            duration_m = record.sleep_duration_min % 60
            self._set_table_item(table, i, 1, f"{duration_h}時間 {duration_m:02d}分")
            # 品質
            self._set_table_item(table, i, 2, f"{record.quality_rating} / 5")
            # 天気・気温 (都市名を追加)
            temp_str = f"{record.temp:.1f}°C" if record.temp is not None else "N/A"
            # ★修正: 都市名と天気を表示
            city_name = record.weather_city_name if record.weather_city_name else "N/A"
            weather_text = f"[{city_name}] {record.weather_condition} / {temp_str}"
            self._set_table_item(table, i, 3, weather_text)
            # メモ
            self._set_table_item(table, i, 4, record.memo if record.memo else "-")

        table.resizeColumnsToContents()

    # ----------------------------------------------------
    # AIアドバイスと時間計算
    # ----------------------------------------------------

    def generate_sleep_advice(self):
        """
        現在のデータと目標に基づき、AI (API) に睡眠アドバイスを生成させる。
        """
        records = self.sleep_records_data
        if not records:
            self.advice_output.setText("データがありません。先に記録をいくつか保存してください。")
            return

        # 統計データの準備
        avg_duration_min = sum(r.sleep_duration_min for r in records) / len(records)
        avg_quality = sum(r.quality_rating for r in records) / len(records)
        
        # プロンプトの構築
        user_query = (
            f"あなたの目標睡眠時間は {self.target_sleep_hours:.1f} 時間です。 "
            f"過去の平均睡眠時間は {avg_duration_min / 60:.1f} 時間、平均的な目覚めスコアは {avg_quality:.1f}/5 です。 "
            f"これらのデータに基づき、あなたの睡眠の質を向上させるための、具体的で実行可能なアドバイスを3つ提供してください。"
            f"アドバイスは親しみやすいトーンで、日本語でお願いします。"
        )

        self.advice_output.setText("🤔 AIが睡眠アドバイスを生成中です...少々お待ちください。")

        try:
            # 💡 修正: api_client.pyの新しいメソッド名を使用
            advice_text = self.api_client.generate_advice_sync(user_query)
            self.advice_output.setText(advice_text)
        except Exception as e:
            self.advice_output.setText(f"❌ AIアドバイスの生成に失敗しました。APIエラー: {e}")
            logger.error(f"AI advice generation failed: {e}")

    # ----------------------------------------------------
    # RPA機能 (モーニングコール)
    # ----------------------------------------------------

    def check_morning_call(self):
        """
        1分ごとに実行され、目標起床時刻と比較して通知を行う。
        """
        # レポートタブの入力フィールドから目標時刻を取得
        target_wake_qtime = self.target_wake_time_input.time()
        
        now = datetime.datetime.now()
        
        # 目標起床時間を今日の日付と結合
        target_wake_dt = datetime.datetime.combine(now.date(), target_wake_qtime.toPyTime())
        
        # 目標時刻が過ぎている場合は、翌日の目標時刻と比較する
        if target_wake_dt < now - timedelta(minutes=1): 
            target_wake_dt += timedelta(days=1)

        # 目標時刻と現在時刻の差を計算
        diff = target_wake_dt - now
        diff_seconds = diff.total_seconds()

        # 目標時刻の前後30秒以内、かつ目標時刻が現在時刻よりも未来であれば通知
        if -30 <= diff_seconds <= 30:
            if target_wake_dt.date() == now.date(): # 当日または翌日であるかを確認
                 # 通知の実行 (QMessageBoxを使用)
                 QMessageBox.information(
                     self, 
                     "✨ モーニングコール ✨", 
                     f"目標起床時間 ({target_wake_qtime.toString('hh:mm')}) です！気持ちの良い一日を！"
                 )

                 logger.info("Morning call alert triggered.")
