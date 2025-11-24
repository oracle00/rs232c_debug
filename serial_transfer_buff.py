import serial
import threading
import time
import datetime
import sys

# --- COMポートとボーレートの設定 ---
COM3_PORT_NAME = 'COM3'
COM5_PORT_NAME = 'COM5'
BAUD_RATE = 9600
BUFFER_TIMEOUT = 0.1  # 受信タイムアウト時間（秒）

# --- 出力時のポートの別名（エイリアス）設定 ---
# ここでログやコンソールに表示したい名前に変更してください。
COM3_ALIAS = 'Device_A (COM3)'
COM5_ALIAS = 'Device_B (COM5)'

# ログファイル名に日時を含める
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"serial_log_{timestamp}.txt"

# ログファイルを開く
try:
    log_file = open(log_filename, "a", encoding='utf-8')
except IOError as e:
    print(f"ログファイル {log_filename} を開けませんでした: {e}")
    sys.exit(1)

# グローバル変数とロック
log_lock = threading.Lock()
running = True

def log_data(source_alias, data):
    """
    データを受信元（別名）、日時とともにコンソールとファイルに出力する。
    """
    with log_lock:
        hex_data = ' '.join(f'{b:02X}' for b in data)
        current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_message = f"[{current_time}] From {source_alias}: {hex_data}\n"

        print(log_message, end='')
        log_file.write(log_message)
        log_file.flush()

def handle_port(source_port_name, source_alias, source_serial, dest_serial):
    """
    指定されたポートからのデータを受信し、バッファリングして転送・ログ出力するスレッド関数。
    ログ出力時には別名を使用する。
    """
    buffer = bytearray()
    last_receive_time = time.time()

    while running:
        if source_serial.in_waiting:
            data = source_serial.read(source_serial.in_waiting)
            if data:
                buffer.extend(data)
                last_receive_time = time.time()
        
        # データがバッファにあり、かつタイムアウト時間が経過したら転送・ログ出力
        if len(buffer) > 0 and (time.time() - last_receive_time) > BUFFER_TIMEOUT:
            if dest_serial and dest_serial.is_open:
                dest_serial.write(buffer)  # バッファ全体を一度に転送
            log_data(source_alias, buffer)  # ここで別名を使用し、バッファ全体をログ出力
            buffer = bytearray()  # バッファをクリア
        
        time.sleep(0.001)

def main():
    global running
    ser_c3 = None
    ser_c5 = None
    try:
        # 実際のポート名でシリアルポートを開く
        ser_c3 = serial.Serial(COM3_PORT_NAME, BAUD_RATE, timeout=0.1)
        ser_c5 = serial.Serial(COM5_PORT_NAME, BAUD_RATE, timeout=0.1)
        print(f"物理ポート {COM3_PORT_NAME} ({COM3_ALIAS}) および {COM5_PORT_NAME} ({COM5_ALIAS}) を開きました。")
        print(f"ボーレート: {BAUD_RATE} bps, ログファイル: {log_filename}")
        print("停止するには Ctrl+C を押してください。")

        # 各ポートのハンドリングを別スレッドで実行し、引数に別名を渡す
        thread_c3_to_c5 = threading.Thread(target=handle_port, args=(COM3_PORT_NAME, COM3_ALIAS, ser_c3, ser_c5))
        thread_c5_to_c3 = threading.Thread(target=handle_port, args=(COM5_PORT_NAME, COM5_ALIAS, ser_c5, ser_c3))

        thread_c3_to_c5.start()
        thread_c5_to_c3.start()

        # メインスレッドは終了を待つ
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("スクリプトを終了します。")
    except serial.SerialException as e:
        print(f"シリアルポートエラー: {e}")
    finally:
        running = False
        if 'thread_c3_to_c5' in locals() and thread_c3_to_c5.is_alive():
            thread_c3_to_c5.join()
        if 'thread_c5_to_c3' in locals() and thread_c5_to_c3.is_alive():
            thread_c5_to_c3.join()
        if ser_c3 and ser_c3.is_open:
            ser_c3.close()
        if ser_c5 and ser_c5.is_open:
            ser_c5.close()
        if 'log_file' in globals() and not log_file.closed:
            log_file.close()
        print("ポートとログファイルを閉じました。")

if __name__ == "__main__":
    main()
