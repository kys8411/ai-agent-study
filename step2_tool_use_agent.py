"""
============================================================
🔧 Step 2: Tool Use 구현하기 (25분)
============================================================
목표: Claude가 "도구"를 사용하는 에이전트 만들기

🧠 Tool Use가 뭐냐면:
   평소 Claude는 "말"만 할 수 있잖아요?
   Tool Use는 Claude에게 "도구 목록"을 알려주면,
   Claude가 스스로 판단해서 필요한 도구를 "호출"하는 겁니다.
   
   예시) 
   사용자: "서울 날씨 알려줘"
   Claude: (생각) 날씨를 알려면 get_weather 도구를 써야겠다!
   Claude: → get_weather(city="서울") 호출 요청
   우리 코드: → 실제로 날씨 데이터를 가져와서 Claude에게 돌려줌
   Claude: "서울은 현재 15도이고 맑습니다!"
   
   이 흐름이 바로 AI 에이전트의 핵심입니다! 🚀
============================================================
"""

import anthropic
import json

client = anthropic.Anthropic()

# ============================================================
# 📌 PART 1: 도구(Tool) 정의하기
# ============================================================
# Claude에게 "너 이런 도구들 쓸 수 있어"라고 알려주는 부분
# JSON Schema 형식으로 도구의 이름, 설명, 파라미터를 정의합니다

tools = [
    {
        "name": "get_weather",              # 도구 이름 (Claude가 호출할 때 이 이름을 씀)
        "description": "특정 도시의 현재 날씨 정보를 가져옵니다. 사용자가 날씨를 물어볼 때 사용하세요.",
        "input_schema": {                   # 이 도구에 어떤 입력값이 필요한지 정의
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "날씨를 조회할 도시 이름 (예: 서울, 부산, 뉴욕)"
                }
            },
            "required": ["city"]            # city는 반드시 있어야 함
        }
    },
    {
        "name": "get_time",
        "description": "특정 도시의 현재 시간을 가져옵니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "시간을 조회할 도시 이름"
                }
            },
            "required": ["city"]
        }
    }
]


# ============================================================
# 📌 PART 2: 도구가 실제로 하는 일 (가짜 데이터)
# ============================================================
# 실제 서비스라면 여기서 API를 호출하겠지만,
# 학습용이니까 가짜 데이터를 돌려줍니다.
# 나중에 여기를 진짜 API로 바꾸면 실전 에이전트가 됩니다!

def get_weather(city: str) -> dict:
    """가짜 날씨 데이터 반환 (나중에 진짜 API로 교체 가능)"""
    fake_weather = {
        "서울": {"temp": 3, "condition": "맑음", "humidity": 45},
        "부산": {"temp": 7, "condition": "흐림", "humidity": 60},
        "뉴욕": {"temp": -2, "condition": "눈", "humidity": 70},
    }
    weather = fake_weather.get(city, {"temp": 20, "condition": "알 수 없음", "humidity": 50})
    return {"city": city, **weather}


def get_time(city: str) -> dict:
    """가짜 시간 데이터 반환"""
    fake_time = {
        "서울": "2025-02-23 05:45:00 KST",
        "부산": "2025-02-23 05:45:00 KST",
        "뉴욕": "2025-02-22 15:45:00 EST",
    }
    return {"city": city, "current_time": fake_time.get(city, "알 수 없음")}


# 도구 이름 → 실제 함수 매핑 (Claude가 호출하면 이 딕셔너리에서 찾아서 실행)
tool_functions = {
    "get_weather": get_weather,
    "get_time": get_time,
}


# ============================================================
# 📌 PART 3: Tool Use 대화 루프 (핵심!)
# ============================================================
# 이 함수가 에이전트의 "두뇌"입니다.
# 
# 흐름:
# 1) 사용자 메시지를 Claude에게 보냄 (도구 목록도 같이)
# 2) Claude가 "도구를 쓰겠다"고 응답하면 → 우리가 실제로 실행
# 3) 실행 결과를 다시 Claude에게 보냄
# 4) Claude가 최종 답변을 만들어줌
#
# 이 루프가 바로 ReAct 패턴의 기초입니다!

def run_agent(user_message: str):
    """Tool Use 에이전트 실행"""
    
    print(f"\n{'='*60}")
    print(f"👤 사용자: {user_message}")
    print(f"{'='*60}")
    
    messages = [{"role": "user", "content": user_message}]
    
    # ---- 1단계: Claude에게 메시지 + 도구 목록 보내기 ----
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tools,                    # 👈 여기서 도구 목록을 넘겨줌!
        messages=messages,
    )
    
    print(f"\n🤖 Claude의 판단: stop_reason = '{response.stop_reason}'")
    # stop_reason이 "tool_use"면 → Claude가 도구를 쓰고 싶다는 뜻!
    # stop_reason이 "end_turn"이면 → 도구 없이 바로 답변
    
    # ---- 2단계: Claude가 도구 사용을 요청했는지 확인 ----
    while response.stop_reason == "tool_use":
        
        # Claude의 응답에서 도구 호출 정보 추출
        tool_use_block = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use_block = block
                break
        
        tool_name = tool_use_block.name       # 어떤 도구를 쓸 건지
        tool_input = tool_use_block.input      # 어떤 입력값을 넣을 건지
        tool_use_id = tool_use_block.id        # 이 호출의 고유 ID
        
        print(f"\n🔧 도구 호출: {tool_name}({json.dumps(tool_input, ensure_ascii=False)})")
        
        # ---- 3단계: 실제로 도구 실행 ----
        tool_function = tool_functions[tool_name]
        tool_result = tool_function(**tool_input)
        
        print(f"📊 도구 결과: {json.dumps(tool_result, ensure_ascii=False)}")
        
        # ---- 4단계: 도구 결과를 Claude에게 다시 보내기 ----
        # Claude의 응답(도구 호출 포함)과 도구 결과를 messages에 추가
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,        # 어떤 호출에 대한 결과인지 매칭
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            ],
        })
        
        # Claude에게 다시 요청 (도구 결과를 보고 최종 답변 생성)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )
        
        print(f"\n🤖 Claude 재판단: stop_reason = '{response.stop_reason}'")
    
    # ---- 5단계: 최종 응답 출력 ----
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text
    
    print(f"\n💬 Claude 최종 답변:\n{final_text}")
    print(f"\n{'='*60}\n")
    
    return final_text


# ============================================================
# 📌 PART 4: 테스트해보기!
# ============================================================
# 다양한 질문으로 Claude가 어떻게 도구를 쓰는지 관찰하세요

if __name__ == "__main__":
    
    # 테스트 1: 날씨 질문 → Claude가 get_weather를 호출할 것
    run_agent("서울 날씨 어때?")
    
    # 테스트 2: 시간 질문 → Claude가 get_time을 호출할 것
    run_agent("뉴욕은 지금 몇 시야?")
    
    # 테스트 3: 도구가 필요 없는 질문 → Claude가 도구 없이 답변할 것
    run_agent("파이썬이 뭐야?")
    
    # 테스트 4: 복합 질문 → Claude가 여러 도구를 쓸 수도 있음
    run_agent("서울 날씨랑 뉴욕 시간 알려줘")


"""
============================================================
🎯 여기까지 완료하면 당신은:
============================================================
1. ✅ Tool Use의 전체 흐름을 이해했습니다
2. ✅ Claude가 "스스로 판단해서" 도구를 호출하는 걸 봤습니다
3. ✅ 에이전트의 핵심 루프 (요청→판단→도구실행→결과반환→최종답변)을 구현했습니다

🚀 다음 단계 (내일 아침):
- get_weather를 진짜 날씨 API로 교체해보기
- 새로운 도구 추가해보기 (예: DB 조회, 계산기)
- system prompt를 추가해서 에이전트 성격 부여하기
============================================================
"""
