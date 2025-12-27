import serial
import threading
import time
import datetime
import sys

# --- COMポート設定 ---
COM_A_NAME = 'COM3'
COM_B_NAME = 'COM5'
BAUD_RATE = 9600

# ACK(0.03s)対応のため、ログにまとめる待機時間を短縮
LOG_PACKET_INTERVAL = 0.01

# エイリアス（ログ表示用）
ALIAS_A = 'Device_A (COM3)'
ALIAS_B = 'Device_B (COM5)'

# ログファイル設定
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"serial_bridge_log_{timestamp}.txt"

try:
    log_file = open(log_filename, "a", encoding='utf-8')
except IOError as e:
    print(f"ログファイルを開けませんでした: {e}")
    sys.exit(1)

log_lock = threading.Lock()
running = True


# ---------------------------------------------------------
#  ログ出力（共通）
# ---------------------------------------------------------
def write_log(message):
    with log_lock:
        print(message, end='')
        log_file.write(message)
        log_file.flush()


# ---------------------------------------------------------
#  DATA ログ（方向矢印つき）
# ---------------------------------------------------------
def log_data(src_alias, dest_alias, data):
    current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    hex_data = ' '.join(f'{b:02X}' for b in data)
    write_log(f"[{current_time}] DATA {src_alias} → {dest_alias}: {hex_data}\n")


# ---------------------------------------------------------
#  SIGNAL ログ（方向矢印つき）
# ---------------------------------------------------------
def log_signal(src_alias, dest_alias, rts_state):
    current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    status = "ON" if rts_state else "OFF"
    write_log(f"[{current_time}] SIGNAL {src_alias} → {dest_alias}: RTS={status}\n")


# ---------------------------------------------------------
#  データ転送スレッド（読み取ったら即書き込み）
# ---------------------------------------------------------
def data_bridge_thread(src_ser, dest_ser, src_alias, dest_alias):
    buffer = bytearray()
    last_receive_time = time.time()

    while running:
        try:
            if src_ser.in_waiting > 0:
                data = src_ser.read(src_ser.in_waiting)
                if data:
                    # 即時転送（ACK遅延防止）
                    dest_ser.write(data)

                    # ログ用バッファ
                    buffer.extend(data)
                    last_receive_time = time.time()

            # パケット区切り判定（ログ用）
            if len(buffer) > 0 and (time.time() - last_receive_time) > LOG_PACKET_INTERVAL:
                log_data(src_alias, dest_alias, buffer)
                buffer = bytearray()

            time.sleep(0.001)

        except Exception as e:
            write_log(f"Data Bridge Error ({src_alias}): {e}\n")
            break


# ---------------------------------------------------------
#  信号線（RTS/CTS）ブリッジスレッド
# ---------------------------------------------------------
def signal_bridge_thread(src_ser, dest_ser, src_alias, dest_alias):
    """
    src_ser.cts（入力）を読み取り、dest_ser.rts（出力）に反映する。
    これにより、デバイス間のフロー制御をソフトウェアで仲介する。
    """
    prev_cts = None

    while running:
        try:
            curr_cts = src_ser.cts

            if curr_cts != prev_cts:
                # CTS(入力) → 相手側 RTS(出力)
                dest_ser.rts = curr_cts

                # ログ（方向矢印つき）
                log_signal(src_alias, dest_alias, curr_cts)

                prev_cts = curr_cts

            time.sleep(0.005)

        except Exception as e:
            write_log(f"Signal Bridge Error ({src_alias}): {e}\n")
            break


# ---------------------------------------------------------
#  メイン処理
# ---------------------------------------------------------
def main():
    global running
    ser_a = None
    ser_b = None

    conf = {
        'baudrate': BAUD_RATE,
        'timeout': 0,
        'rtscts': False,  # OSの自動制御を完全に無効化
        'dsrdtr': False
    }

    try:
        ser_a = serial.Serial(COM_A_NAME, **conf)
        ser_b = serial.Serial(COM_B_NAME, **conf)

        # 初期状態の同期
        ser_b.rts = ser_a.cts
        ser_a.rts = ser_b.cts

        print(f"--- Serial Bridge Debugger Started ---")
        print(f"Port A: {COM_A_NAME} ({ALIAS_A})")
        print(f"Port B: {COM_B_NAME} ({ALIAS_B})")
        print(f"Log file: {log_filename}")
        print(f"Settings: {BAUD_RATE}bps, Flow Control: Manual Bridge")
        print("---------------------------------------")

        threads = [
            threading.Thread(target=data_bridge_thread, args=(ser_a, ser_b, ALIAS_A, ALIAS_B)),
            threading.Thread(target=data_bridge_thread, args=(ser_b, ser_a, ALIAS_B, ALIAS_A)),
            threading.Thread(target=signal_bridge_thread, args=(ser_a, ser_b, ALIAS_A, ALIAS_B)),
            threading.Thread(target=signal_bridge_thread, args=(ser_b, ser_a, ALIAS_B, ALIAS_A))
        ]

        for t in threads:
            t.daemon = True
            t.start()

        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        running = False
        time.sleep(0.5)
        if ser_a: ser_a.close()
        if ser_b: ser_b.close()
        if not log_file.closed: log_file.close()
        print("Done.")


if __name__ == "__main__":
    main()