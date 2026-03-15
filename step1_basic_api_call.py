"""
============================================================
🔰 Step 1: Claude API 기본 호출 (10~15분)
============================================================
목표: API가 정상적으로 작동하는지 확인하기
이건 도구(Tool) 없이, 그냥 Claude랑 대화하는 코드입니다.

📌 사전 준비 (터미널에서):
   pip install anthropic
   
📌 API 키 설정 (터미널에서):
   [Windows] set ANTHROPIC_API_KEY=sk-ant-xxxxx
   [Mac/Linux] export ANTHROPIC_API_KEY=sk-ant-xxxxx
   
   또는 아래 코드에서 직접 입력해도 됩니다 (보안상 환경변수 추천)
============================================================
"""

import anthropic

# ✅ 클라이언트 생성 — API 키는 환경변수에서 자동으로 읽어옴
client = anthropic.Anthropic()
# 만약 환경변수 설정이 안 되면 아래처럼 직접 넣어도 됨:
# client = anthropic.Anthropic(api_key="sk-ant-여기에키입력")

# ✅ Claude에게 메시지 보내기 — 가장 기본적인 호출
response = client.messages.create(
    model="claude-sonnet-4-20250514",   # 사용할 모델
    max_tokens=1024,                     # 최대 응답 길이
    messages=[
        {
            "role": "user",
            "content": "안녕! 너는 Tool Use가 뭔지 중학생도 이해할 수 있게 설명해줄 수 있어?"
        }
    ]
)

# ✅ 응답 출력
print("=" * 50)
print("Claude의 응답:")
print("=" * 50)
print(response.content[0].text)

"""
🎯 여기까지 했으면 성공!
- API 키가 잘 작동하는지 확인
- response 구조를 눈으로 확인
- 다음 Step으로 넘어가세요!

💡 만약 에러가 나면:
- "AuthenticationError" → API 키가 잘못됨
- "ModuleNotFoundError" → pip install anthropic 다시 실행
"""
