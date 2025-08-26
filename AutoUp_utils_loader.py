import json
import configparser

def load_input_json(filepath):
    """
    🔹 AutoUp_input_sample.json 파일 로드
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_ftp_config(filepath):
    """
    🔹 AutoUp_FTP_config.ini 파일 로드
    """
    config = configparser.ConfigParser()
    config.read(filepath)
    return dict(config["FTP"])

def log_error(message):
    """
    🔹 오류 메시지를 출력
    """
    print(message)

