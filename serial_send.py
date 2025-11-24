import serial
import sys

# --- 設定 ---
SERIAL_PORT = 'COM5'  # 使用するポート名 (環境に合わせて変更してください)
BAUD_RATE = 9600      # ボーレート (接続機器に合わせて変更してください)
TIMEOUT = 1           # タイムアウト時間 (秒)
# --------------

def write_hex_to_serial(port_name, baud_rate):
    try:
        # シリアルポートを開く
        ser = serial.Serial(port_name, baud_rate, timeout=TIMEOUT, write_timeout=TIMEOUT)
        print(f"COMポート {port_name} をボーレート {baud_rate} で開きました。")
        print("標準入力から16進数データをスペース区切りで入力してください (例: 00 11 22 FF)。")
        print("入力されたデータはそのままバイトデータとしてシリアルポートへ送信されます。")
        print("終了するには、Ctrl+C を押してください。")

        while True:
            # 標準入力から1行読み込む
            # rstrip()で末尾の改行や空白を削除
            line = sys.stdin.readline().rstrip()
            if not line:
                continue

            try:
                # スペースで分割し、各16進数文字列をバイト値のリストに変換
                # '00 11 FF' -> [0, 17, 255]
                byte_list = [int(hex_str, 16) for hex_str in line.split()]
                
                # バイト値のリストをbytesオブジェクトに変換
                data_to_send = bytes(byte_list)

                if not data_to_send:
                    print("有効な16進数データが入力されませんでした。")
                    continue
                
                # シリアルポートへバイトデータを書き込む
                ser.write(data_to_send)
                print(f"送信バイト数: {len(data_to_send)} -> 送信データ(hex): {' '.join(f'{b:02X}' for b in data_to_send)}")

            except ValueError as e:
                print(f"入力エラー: {e}")
                print("有効な16進数文字列 (00-FF) をスペース区切りで入力してください。")

    except serial.SerialException as e:
        print(f"シリアルポートのエラー: {e}")
        print("ポート名や接続を確認してください。")
    except KeyboardInterrupt:
        print("スクリプトを終了します。")
    finally:
        if 'ser' in locals() and ser.isOpen():
            ser.close()
            print("ポートを閉じました。")

if __name__ == "__main__":
    write_hex_to_serial(SERIAL_PORT, BAUD_RATE)
