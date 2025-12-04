import klipper_handler as mr
import time

print("----------------------------------------")
print("[TEST] 프린터 정지(취소) 명령 테스트 시작")
print("----------------------------------------")

# 1. 현재 연결 상태 확인 (선택 사항)
print(" >> 문레이커 연결 확인 중...")
try:
    status = mr.getPrinterStatus()
    if status['isConnected']:
        print(f" >> 연결 성공! (노즐 온도: {status['nozzleTemp']}도)")
    else:
        print(" >> 문레이커 연결 실패 (오프라인 상태일 수 있음)")
except Exception as e:
    print(f" >> 상태 확인 중 에러: {e}")

# 2. 정지 명령 실행
print("\n >> stopPrint() 함수 실행!")
mr.stopPrint()

print("\n----------------------------------------")
print("[TEST] 테스트 종료. Klipper 상태를 확인하세요.")
print("----------------------------------------")