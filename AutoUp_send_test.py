# AutoUp_test_client.py
import tkinter as tk
import requests
import json
import os
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def send_test_data():
    try:
        print("📂 JSON 로드 시도 중")
        with open("AutoUp_send_test_info.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        print("🛠️ JSON 문자열 변환 (utf-8 encoding)...")
        json_string = json.dumps(data, ensure_ascii=False).encode('utf-8')

        print("🚀 서버로 POST 전송 시도 중...")
        headers = {"Content-Type": "application/json; charset=utf-8"}
        host = get_local_ip()
        port = 8088
        url = f"http://{host}:{port}/"
        response = requests.post(url, data=json_string, headers=headers)

        print("📬 응답 코드:", response.status_code)
        print("📬 응답 본문:", response.text)

        if response.status_code == 200:
            result_label.config(text="✅ 전송 성공", fg="green")
        else:
            result_label.config(text=f"❌ 실패: {response.status_code}", fg="red")

    except Exception as e:
        print(f"⚠️ 예외 발생: {e}")
        result_label.config(text=f"⚠️ 오류 발생: {str(e)}", fg="orange")

# 🔘 GUI 구성
root = tk.Tk()
root.title("AutoUp 테스트 클라이언트")
root.geometry("300x180")

send_button = tk.Button(root, text="정보 전송", font=("Arial", 14), bg="blue", fg="white", command=send_test_data)
send_button.pack(pady=20)

result_label = tk.Label(root, text="", font=("Arial", 12))
result_label.pack()

# ✅ 서버 주소 표시
def update_server_label():
    host = get_local_ip()
    port = 8088
    server_label.config(text=f"서버: {host}:{port}")

server_label = tk.Label(root, text="", font=("Arial", 10), fg="gray")
server_label.pack(pady=5)
update_server_label()

root.mainloop()
