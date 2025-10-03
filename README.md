# AutoUp V3.2 - FTP 대용량 파일 업로더

## 🚀 주요 기능

- **멀티스레드 업로드**: 5개 채널 동시 업로드
- **대용량 파일 지원**: GB급 파일 안정적 전송
- **자동 재시도**: 실패 시 자동 재시도 메커니즘
- **이어받기 지원**: 중단된 업로드 자동 재개
- **UTF-8 완벽 지원**: 한글 파일명 처리
- **실시간 진행률**: 로그와 GUI 완벽 동기화

---

## 📦 최신 업데이트 (V2.3 - 2025.01)

### ✅ 예외 처리 개선
- 커스텀 예외 클래스 추가 (`UploadStuckError`, `UploadIncompleteError`)
- Helper 함수로 로직 분리 (`check_upload_status`, `monitor_large_upload`)
- 우선순위 기반 완료 판정

### ✅ 로그-GUI 동기화
- 로그 출력과 GUI 업데이트 완벽 동기화
- 95%까지만 callback에서 표시 (버퍼링 고려)
- 100%는 실제 전송 완료 후 표시

### ✅ 90% 이후 모니터링
- 90% 도달 시 별도 모니터링 시작
- SIZE 명령으로 원격 파일 크기 확인
- 멈춤 감지 및 자동 재시도

---

## 🛠️ 설치 및 실행

### 1. 설정 파일 수정 (`AutoUp_env.ini`)
```ini
[FTP1]
host = your.ftp.server
port = 21
user = username
pass = password

[DEFAULT]
selected_ftp = FTP1
network_delay = 1
```

### 2. 실행 방법
```bash
# Python으로 실행
python AutoUp.py

# 또는 컴파일된 실행 파일
AutoUp.exe
```

### 3. 컴파일 (선택사항)
```bash
python -m PyInstaller --onefile --windowed --icon=AutoPath.ico --name=AutoUp AutoUp.py
```

---

## 📂 파일 구조

```
AutoUp/
├── AutoUp.py                 # 메인 프로그램
├── AutoUp_GUI.py             # GUI 인터페이스
├── AutoUp_upload_util.py     # 업로드 유틸리티 (v2.3)
├── AutoUp_uploader.py        # 업로드 관리자
├── AutoUp_env.py            # 환경 설정 로더
├── AutoUp_env.ini           # 설정 파일
└── test/
    ├── test_sync.py         # 로그-GUI 동기화 테스트
    ├── test_improved_upload.py  # 개선된 업로드 테스트
    └── test_ftp_connection.py   # FTP 연결 테스트
```

---

## 🔧 문제 해결

### 중복 실행 오류
```bash
# PID 파일 삭제
rm AutoUp_instance.pid
```

### FTP 연결 실패
```bash
# 연결 테스트
python test_ftp_connection.py
```

### 업로드 중단/실패
- 자동 재시도 (최대 3회)
- 이어받기 자동 시도
- 상세 로그: `AutoUp_error.log`

---

## 📊 성능 최적화

| 파일 크기 | 버퍼 크기 | 타임아웃 |
|----------|----------|----------|
| < 10MB   | 32KB     | 5분      |
| < 100MB  | 128KB    | 계산값    |
| < 500MB  | 256KB    | 계산값    |
| ≥ 500MB  | 512KB    | 최대 2시간 |

---

## 🧪 테스트

```bash
# 동기화 테스트
python test_sync.py

# 개선된 업로드 테스트
python test_improved_upload.py

# FTP 연결 테스트
python test_ftp_connection.py
```

---

## 📝 변경 이력

### V2.3 (2025.01)
- 복잡한 예외 처리 개선
- 로그-GUI 완벽 동기화
- 100% 완료 판정 개선

### V3.2 (2025.01)
- 5채널 동시 업로드
- 159 파일서버 개선
- PID 기반 중복실행 체크

### V3.1 (2025.01)
- UTF-8 인코딩 안전 처리
- 대용량 파일 업로드 개선
- 자동 재시도 메커니즘

---

## 📞 지원

- **로그 파일**: `AutoUp_error.log`
- **GitHub**: [uwo337/AutoUp](https://github.com/uwo337/AutoUp)
- **버전**: 2.3 (Latest)

---

**개발자**: uwo337  
**최종 업데이트**: 2025년 1월
