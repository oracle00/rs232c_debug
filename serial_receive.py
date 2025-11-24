import serial
import time
from datetime import datetime
import sys

# COMポートとボーレートの設定
SERIAL_PORT = 'COM8'
BAUD_RATE = 9600
# タイムアウト時間。この時間データが来ないと、バッファの内容をフラッシュします。
TIMEOUT = 0.5 

def receive_serial_data():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        print(f"ポート[{SERIAL_PORT}]を開きました (Baudrate: {BAUD_RATE}, Timeout: {TIMEOUT}s)")
        
        # 受信データを一時的に保持するバッファ
        received_buffer = []
        # 最初のデータを受信した時刻を記録する変数
        first_data_timestamp = None

        while True:
            # 受信バッファにある全てのデータを読み込む
            data = ser.read(ser.in_waiting or 1)
            
            if data:
                # データがある場合、バッファに追加する
                if not first_data_timestamp:
                    first_data_timestamp = datetime.now()
                    
                # 受信データを1バイトごとに16進数フォーマットのリストに変換してバッファに追加
                hex_list = [f"{b:02X}" for b in data]
                received_buffer.extend(hex_list)
                
            else:
                # タイムアウトによりデータが受信されなかった場合
                # バッファにデータが溜まっていれば、まとめて出力する
                if received_buffer:
                    timestamp_str = first_data_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    # バッファ内の全データをスペース区切りで結合して1行で出力
                    print(f"[{timestamp_str}] 受信データ: {' '.join(received_buffer)}", flush=True)
                    
                    # バッファとタイムスタンプをリセット
                    received_buffer = []
                    first_data_timestamp = None
                
                # バッファが空なら何もせず、次のループへ

    except serial.SerialException as e:
        print(f"\nシリアルポートエラー: {e}")
        print("COMポートの設定や接続を確認してください。")
    except KeyboardInterrupt:
        print("\nスクリプトを終了します。")
    finally:
        if 'ser' in locals() and ser.is_open:
            # 終了時にバッファに残っているデータがあれば出力
            if received_buffer:
                timestamp_str = first_data_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                print(f"[{timestamp_str}] 受信データ: {' '.join(received_buffer)}", flush=True)
            ser.close()
            print("COMポートを閉じました。")

if __name__ == "__main__":
    receive_serial_data()

