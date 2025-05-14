import os
import time
import json
import asyncio
import websockets
from datetime import datetime
from simpleobsws import WebSocketClient, Request, IdentificationParameters
import threading

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json 파일을 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError:
        print("config.json 파일 형식이 올바르지 않습니다.")
        return None

# 설정 로드
config = load_config()
if not config:
    print("프로그램을 종료합니다.")
    exit(1)

# OBS WebSocket 설정
OBS_HOST = config['obs']['host']
OBS_PORT = config['obs']['port']
OBS_PASSWORD = config['obs']['password']

# Sunshine 로그 파일 경로
SUNSHINE_LOG_PATH = config['sunshine']['log_path']

class LogMonitor:
    def __init__(self, websocket_server):
        self.websocket_server = websocket_server
        self.last_position = 0
        self.connected = False
        self.running = True

    async def start_monitoring(self):
        print(f"Sunshine 로그 파일 모니터링 시작: {SUNSHINE_LOG_PATH}")
        
        while self.running:
            try:
                if os.path.exists(SUNSHINE_LOG_PATH):
                    with open(SUNSHINE_LOG_PATH, 'r') as f:
                        f.seek(self.last_position)
                        new_lines = f.readlines()
                        self.last_position = f.tell()

                        for line in new_lines:
                            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            if "CLIENT CONNECTED" in line and not self.connected:
                                self.connected = True
                                print(f"[{current_time}] Moonlight 클라이언트 연결됨. OBS 녹화를 시작합니다.")
                                await self.websocket_server.start_recording()
                            elif "CLIENT DISCONNECTED" in line and self.connected:
                                self.connected = False
                                print(f"[{current_time}] Moonlight 클라이언트 연결 해제됨. OBS 녹화를 중지합니다.")
                                await self.websocket_server.stop_recording()
            except Exception as e:
                print(f"로그 파일 읽기 오류: {e}")
            
            await asyncio.sleep(1)  # 1초마다 확인

    def stop(self):
        self.running = False

class OBSController:
    def __init__(self):
        # simpleobsws WebSocketClient 사용 (인증 설정 및 이벤트 구독)
        ws_kwargs = {"url": f"ws://{OBS_HOST}:{OBS_PORT}"}
        if OBS_PASSWORD:
            ws_kwargs["password"] = OBS_PASSWORD
        # 기본 이벤트 구독 파라미터 (모든 이벤트)
        id_params = IdentificationParameters()
        # WebSocketClient 인스턴스 생성 및 이벤트 콜백 등록
        self.ws = WebSocketClient(**ws_kwargs, identification_parameters=id_params)
        self.ws.register_event_callback(self._on_event)

    async def connect(self):
        try:
            # OBS WebSocket 서버에 연결하고 식별 완료 대기
            await self.ws.connect()
            await self.ws.wait_until_identified()
            print("OBS WebSocket 연결 성공")
        except Exception as e:
            print(f"OBS WebSocket 연결 실패: {e}")

    async def disconnect(self):
        if self.ws:
            try:
                await self.ws.disconnect()
                print("OBS WebSocket 연결 해제")
            except Exception as e:
                print(f"OBS WebSocket 연결 해제 실패: {e}")

    async def start_recording(self):
        if self.ws:
            try:
                # Record 시작 요청
                response = await self.ws.call(Request("StartRecord"))
                # error 속성이 None이면 성공
                if getattr(response, 'error', None) is None:
                    print("OBS 녹화 시작")
                else:
                    print(f"OBS 녹화 시작 오류: {response.error}")
            except Exception as e:
                print(f"OBS 녹화 시작 실패: {e}")

    async def stop_recording(self):
        if self.ws:
            try:
                # Record 중지 요청
                response = await self.ws.call(Request("StopRecord"))
                # error 속성이 None이면 성공
                if getattr(response, 'error', None) is None:
                    print("OBS 녹화 중지")
                else:
                    print(f"OBS 녹화 중지 오류: {response.error}")
            except Exception as e:
                print(f"OBS 녹화 중지 실패: {e}")

    async def save_replay_buffer(self):
        if self.ws:
            try:
                response = await self.ws.call(Request("SaveReplayBuffer"))
                if getattr(response, 'error', None) is None:
                    print("OBS 리플레이 버퍼 저장 성공")
                else:
                    print(f"OBS 리플레이 버퍼 저장 오류: {response.error}")
            except Exception as e:
                print(f"OBS 리플레이 버퍼 저장 실패: {e}")

    async def _on_event(self, payload):
        """OBS WebSocket으로부터 수신된 이벤트를 출력합니다."""
        print(f"OBS 이벤트 수신: {payload}")

class WebSocketServer:
    def __init__(self):
        self.obs_controller = OBSController()
        self.clients = set()

    async def start(self):
        await self.obs_controller.connect()
        # 자동 녹화 시작
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{current_time}] 프로그램 시작 시 자동 녹화를 시작합니다.")
        await self.start_recording()
        server = await websockets.serve(self.handle_client, "localhost", 8765)
        print("WebSocket 서버가 시작되었습니다.")
        await server.wait_closed()

    async def handle_client(self, websocket, path):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                if message == "start_recording":
                    await self.start_recording()
                elif message == "stop_recording":
                    await self.stop_recording()
        finally:
            self.clients.remove(websocket)

    async def start_recording(self):
        await self.obs_controller.start_recording()
        for client in self.clients:
            try:
                await client.send("recording_started")
            except Exception as e:
                print(f"클라이언트에 메시지 전송 실패: {e}")

    async def stop_recording(self):
        await self.obs_controller.stop_recording()
        for client in self.clients:
            try:
                await client.send("recording_stopped")
            except Exception as e:
                print(f"클라이언트에 메시지 전송 실패: {e}")

def start_console_listener(ws_server, loop):
    def listener():
        while True:
            cmd = input().strip().lower()
            if cmd == 'r':
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{current_time}] 리플레이 버퍼 저장 요청")
                asyncio.run_coroutine_threadsafe(ws_server.obs_controller.save_replay_buffer(), loop)
            elif cmd == 's':
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{current_time}] 녹화 중지 요청")
                asyncio.run_coroutine_threadsafe(ws_server.obs_controller.stop_recording(), loop)
    t = threading.Thread(target=listener, daemon=True)
    t.start()

async def main():
    websocket_server = WebSocketServer()
    log_monitor = LogMonitor(websocket_server)
    
    # 콘솔 리스너 시작
    loop = asyncio.get_running_loop()
    start_console_listener(websocket_server, loop)
    try:
        # 로그 파일이 존재하는지 확인
        if not os.path.exists(SUNSHINE_LOG_PATH):
            print(f"로그 파일이 존재하지 않습니다: {SUNSHINE_LOG_PATH}")
            return

        # 로그 모니터링과 웹소켓 서버를 동시에 실행
        await asyncio.gather(
            log_monitor.start_monitoring(),
            websocket_server.start()
        )
    except KeyboardInterrupt:
        print("\n프로그램 종료 중...")
        log_monitor.stop()
        await websocket_server.obs_controller.disconnect()
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램이 종료되었습니다.") 