# 계산기 모듈 — feature/calculator 브랜치에서 작업 중!
def add(a, b):
    """더하기"""
    return a + b

def subtract(a, b):
    """빼기"""
    return a - b

def multiply(a, b):
    """곱하기"""
    return a * b

def divide(a, b):
    """나누기 — 0으로 나누면 에러 대신 메시지 반환"""
    if b == 0:
        return "0으로 나눌 수 없습니다"
    return a / b

if __name__ == "__main__":
    print("=== 계산기 테스트 ===")
    print(f"3 + 5 = {add(3, 5)}")
    print(f"10 - 4 = {subtract(10, 4)}")
    print(f"6 × 7 = {multiply(6, 7)}")
    print(f"15 ÷ 3 = {divide(15, 3)}")
    print(f"10 ÷ 0 = {divide(10, 0)}")