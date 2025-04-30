# Sunshine OBS 자동 녹화 컨트롤러

Sunshine 서버에 Moonlight 클라이언트가 연결될 때 자동으로 OBS 녹화를 시작하고, 연결이 끊어질 때 녹화를 중지하는 프로그램입니다.

## 기능

- Sunshine 로그 파일을 실시간으로 모니터링하여 Moonlight 클라이언트 연결/해제 감지
- 클라이언트 연결 시 OBS Studio 녹화 자동 시작
- 클라이언트 연결 해제 시 OBS Studio 녹화 자동 중지
- 설정 파일 (`config.json`)을 통해 OBS 및 Sunshine 경로 등 사용자 맞춤 설정 가능

## 설정 방법

### 1. OBS WebSocket 설정

- OBS Studio를 실행합니다.
- 메뉴에서 `도구` > `WebSocket 서버 설정`으로 이동합니다.
- `WebSocket 서버 활성화`를 체크합니다.
- (선택 사항) `서버 비밀번호`를 설정합니다.
- 설정한 비밀번호는 아래 `config.json` 파일에 입력해야 합니다.

### 2. `config.json` 설정

프로그램 실행 파일 또는 스크립트와 **같은 경로**에 `config.json` 파일을 생성하고 아래 내용을 참고하여 사용자 환경에 맞게 수정합니다.

```json
{
  "obs": {
    "host": "localhost", // OBS WebSocket 서버 주소 (일반적으로 localhost)
    "port": 4455,        // OBS WebSocket 서버 포트 (OBS 설정 확인)
    "password": "YOUR_OBS_PASSWORD" // OBS WebSocket 비밀번호 (설정 안했으면 빈 문자열 "")
  },
  "sunshine": {
    "log_path": "C:/Program Files/Sunshine/config/sunshine.log" // Sunshine 로그 파일 전체 경로
  }
}
```

- `obs.password`: OBS WebSocket에서 설정한 비밀번호를 입력합니다. 설정하지 않았다면 `""`로 둡니다.
- `sunshine.log_path`: Sunshine 로그 파일의 **전체 경로**를 정확하게 입력합니다. 설치 경로 및 운영체제에 따라 다를 수 있습니다. (예: `C:/Program Files/Sunshine/config/sunshine.log`) **백슬래시(\) 대신 슬래시(/)를 사용하거나 백슬래시를 두 번(\\) 사용해야 합니다.**

## 사용 방법

### 실행 파일 (exe) 사용 (권장)

1. `dist` 폴더 안에 있는 `sunshine_obs_controller.exe` 파일을 실행합니다.
2. **중요:** `config.json` 파일이 `sunshine_obs_controller.exe` 파일과 **같은 폴더** (`dist` 폴더) 안에 있어야 합니다.
3. 프로그램이 실행되면 자동으로 Sunshine 로그 모니터링 및 OBS 녹화 제어를 시작합니다.

### Python 스크립트 사용 (개발/수정 시)

1. Python 개발 환경을 설정합니다 (가상 환경 권장).
2. 필요한 패키지를 설치합니다:
   ```bash
   pip install -r requirements.txt
   ```
3. `sunshine_obs_controller.py` 스크립트와 **같은 경로**에 `config.json` 파일을配置합니다.
4. 스크립트를 실행합니다:
   ```bash
   python sunshine_obs_controller.py
   ```

## 주의사항

- OBS Studio가 실행 중이고 WebSocket 서버가 활성화되어 있어야 합니다.
- Sunshine 서버가 정상적으로 실행 중이어야 합니다.
- `config.json` 파일의 경로 설정 (특히 Sunshine 로그 경로)이 정확해야 합니다.
- 프로그램 시작 시 간혹 녹화 시작/중지 실패 메시지가 여러 번 나타날 수 있습니다. 이는 초기 연결 과정의 문제로 보이며, 이후 정상 작동한다면 무시하셔도 됩니다. (개선 예정)