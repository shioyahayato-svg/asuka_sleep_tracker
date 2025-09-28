import base64
import os
import sys

# ユーザーが指定したローカルパスを設定します
# ここをあなたの環境に合わせて正しく設定してください
IMAGE_PATH = r"C:\Users\hayam\Desktop\asuka_sleep_tracker\ASKA\Model1.png"

def convert_image_to_base64(path):
    """指定された画像ファイルを読み込み、Base64文字列に変換して出力します。"""
    if not os.path.exists(path):
        print(f"エラー: 指定されたファイルが見つかりません: {path}")
        print("ファイルパスを正確に確認してください。")
        return None
    
    try:
        with open(path, "rb") as image_file:
            # 画像ファイルをバイナリ形式で読み込み、Base64にエンコード
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        # クリップボード機能がないため、代わりに「コピーしやすい形」で出力します。
        print("\n==================================================================")
        print("  Base64 エンコード結果 (この長い文字列を全てコピーしてください)  ")
        print("==================================================================")
        
        # 重要な変更点: Pythonのコードとして、Base64文字列をそのまま出力します。
        # ユーザーはこの部分をそのまま assets.py に貼り付けることができます。
        print(f'ASUKA_IMAGE_BASE64 = "{encoded_string}"')
        
        print("\n==================================================================")
        print("↑↑↑ 上の行全体を assets.py にコピー＆ペーストしてください ↑↑↑")
        print("==================================================================\n")
        
        # ユーザーがクリップボード操作ライブラリ (pyperclip) を利用できる場合
        try:
            # クリップボード操作ライブラリがあれば利用（ローカル環境でのみ可能）
            import pyperclip
            pyperclip.copy(encoded_string)
            print("【注】Base64文字列がクリップボードにコピーされました。")
        except ImportError:
            # 外部環境なのでメッセージのみ表示
            print("【注】pyperclipライブラリがないため、自動コピーはできませんでした。")
            
        return encoded_string

    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")
        return None

if __name__ == "__main__":
    convert_image_to_base64(IMAGE_PATH)
