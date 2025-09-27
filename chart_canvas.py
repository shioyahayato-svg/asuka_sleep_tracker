# -*- coding: utf-8 -*-
# PyQt5とMatplotlibを連携させるためのライブラリをインポート
from PyQt5.QtWidgets import QWidget, QSizePolicy # QSizePolicyを追加
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class MplCanvas(FigureCanvas):
    """Matplotlibグラフを描画するためのカスタムキャンバスクラス"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # 日本語フォントの設定
        # 環境に応じて適切なフォントを設定することで、文字化けを防ぎます
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Yu Gothic', 'Meiryo', 'TakaoGothic', 'IPAexGothic', 'DejaVu Sans']

        # FigureとSubplotsの設定
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        # 親クラス（FigureCanvasQTAgg）の初期化
        super().__init__(self.fig)
        self.setParent(parent)
        
        # レイアウトとサイズの調整
        self.setSizePolicy(
            QSizePolicy.Expanding, # QWidget.QSizePolicy.Expanding を QSizePolicy.Expanding に修正
            QSizePolicy.Expanding
        )
        self.updateGeometry()

    def plot_sleep_data(self, dates, durations_min, scores_pct):
        """
        睡眠時間と目覚めスコアの複合グラフを描画する。
        
        :param dates: 日付 (X軸)
        :param durations_min: 睡眠時間 (分)
        :param scores_pct: 目覚めスコア (0-100%)
        """
        self.axes.clear()
        
        # データを時間に変換
        durations_hr = [d / 60 for d in durations_min]

        # --- 棒グラフ (睡眠時間) ---
        color_duration = '#0077B6'
        self.axes.bar(dates, durations_hr, color=color_duration, alpha=0.7, label='睡眠時間 (時間)')
        self.axes.set_ylabel('睡眠時間 (時間)', color=color_duration)
        self.axes.tick_params(axis='y', labelcolor=color_duration)
        # Y軸の最大値を動的に設定（最低8時間）
        self.axes.set_ylim(0, max(8, max(durations_hr) * 1.1 if durations_hr else 8))

        # --- 第2軸 (目覚めスコア) ---
        ax2 = self.axes.twinx()  # Y軸を共有しない第2軸を作成
        color_score = '#FF5A5F'
        ax2.plot(dates, scores_pct, color=color_score, marker='o', linestyle='-', linewidth=2, label='目覚めスコア (%)')
        ax2.set_ylabel('目覚めスコア (%)', color=color_score)
        ax2.tick_params(axis='y', labelcolor=color_score)
        ax2.set_ylim(0, 100) # スコアは0-100%に固定
        
        # タイトルとグリッド
        self.axes.set_title('週間睡眠データと目覚めスコア')
        self.axes.set_xlabel('日付')
        self.axes.grid(True, linestyle='--', alpha=0.6)
        
        # グラフが重ならないように調整し、再描画
        self.fig.tight_layout()
        self.draw()
