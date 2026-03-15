"""
============================================================
📘 Phase 2 | Week 4: Tool Use 심화 + 멀티턴 에이전트
============================================================
🎯 이번 주 목표: 진짜 쓸모있는 에이전트 만들기
   - 월: 여러 도구를 조합하는 에이전트
   - 화: 대화 히스토리 관리 (멀티턴)
   - 수: 에러 핸들링 + 재시도 로직
   - 목: 스트리밍 응답 (실시간 출력)
   - 금: 미니 프로젝트 — 개인 비서 에이전트

📌 전제: step2_tool_use_agent.py를 이해한 상태
============================================================
"""

import anthropic
import json
from datetime import datetime

client = anthropic.Anthropic()


# ============================================================
# 🗓️ 월요일: 여러 도구를 조합하는 에이전트
# ============================================================

"""
📌 진짜 유용한 에이전트는 도구가 여러 개입니다.
   Claude가 질문에 따라 어떤 도구를 쓸지 "스스로 판단"합니다.
   도구가 많아질수록 description이 정확해야 합니다!
"""

tools = [
    {
        "name": "query_database",
        "description": "SQL 쿼리를 실행하여 데이터를 조회합니다. 데이터 분석, 통계, 집계가 필요할 때 사용하세요.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "실행할 SQL 쿼리"},
                "database": {"type": "string", "description": "대상 데이터베이스 (iot_prod, iot_lab)", "default": "iot_prod"}
            },
            "required": ["sql"]
        }
    },
    {
        "name": "get_table_schema",
        "description": "테이블의 컬럼 정보(이름, 타입, 설명)를 조회합니다. SQL을 작성하기 전에 테이블 구조를 확인할 때 사용하세요.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "조회할 테이블 이름"}
            },
            "required": ["table_name"]
        }
    },
    {
        "name": "create_chart",
        "description": "데이터를 시각화 차트로 만듭니다. 조회 결과를 그래프로 보여줄 때 사용하세요.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_type": {"type": "string", "enum": ["bar", "line", "pie"], "description": "차트 유형"},
                "title": {"type": "string", "description": "차트 제목"},
                "data": {"type": "object", "description": "차트 데이터 (labels, values)"}
            },
            "required": ["chart_type", "title", "data"]
        }
    },
    {
        "name": "send_notification",
        "description": "분석 결과를 Teams/Slack 메시지로 전송합니다. 보고서나 알림이 필요할 때 사용하세요.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "전송 채널 (teams, slack, email)"},
                "message": {"type": "string", "description": "전송할 메시지 내용"}
            },
            "required": ["channel", "message"]
        }
    }
]

# 가짜 도구 함수들
def query_database(sql: str, database: str = "iot_prod") -> dict:
    return {"columns": ["model", "error_count"], "rows": [["RF-9000", 1523], ["RF-8500", 987]], "row_count": 2}

def get_table_schema(table_name: str) -> dict:
    return {"table": table_name, "columns": [
        {"name": "error_code", "type": "STRING", "desc": "에러 코드"},
        {"name": "model", "type": "STRING", "desc": "제품 모델명"},
        {"name": "count", "type": "INT", "desc": "발생 횟수"},
        {"name": "date", "type": "DATE", "desc": "발생 일자"}
    ]}

def create_chart(chart_type: str, title: str, data: dict) -> dict:
    return {"status": "success", "chart_url": f"file://charts/{title}.png"}

def send_notification(channel: str, message: str) -> dict:
    return {"status": "sent", "channel": channel, "timestamp": datetime.now().isoformat()}

tool_functions = {
    "query_database": query_database,
    "get_table_schema": get_table_schema,
    "create_chart": create_chart,
    "send_notification": send_notification,
}

"""
🔥 실습: 아래 질문을 에이전트에게 던져보세요.
   Claude가 도구를 어떤 순서로 호출하는지 관찰하세요!
   
   "냉장고 에러 테이블의 구조를 확인하고, 모델별 에러 수를 조회한 다음,
    차트로 만들어서 Teams로 보내줘"
    
   → Claude는 아마 이 순서로 도구를 호출할 겁니다:
   1) get_table_schema → 테이블 구조 확인
   2) query_database → SQL 실행
   3) create_chart → 결과 시각화
   4) send_notification → 결과 전송
"""


# ============================================================
# 🗓️ 화요일: 멀티턴 대화 — 맥락을 기억하는 에이전트
# ============================================================

"""
📌 멀티턴이 뭐냐면:
   한 번의 질문-답변으로 끝나는 게 아니라,
   이전 대화를 기억하면서 연속으로 대화하는 겁니다.
   
   "냉장고 에러 보여줘" → "그중에서 RF-9000만 필터링해줘"
   → "그" 가 뭔지 알려면 이전 대화를 기억해야 함!
"""

class ConversationalAgent:
    """대화 히스토리를 관리하는 에이전트"""
    
    def __init__(self):
        self.messages = []  # 대화 히스토리 저장소
        self.system = """당신은 LG전자 IoT 데이터 분석 에이전트입니다.
이전 대화 맥락을 기억하고, 후속 질문에도 자연스럽게 답변하세요.
한국어로 응답하세요."""
    
    def chat(self, user_message: str) -> str:
        """사용자 메시지를 받아서 응답하고, 히스토리에 저장"""
        
        # 사용자 메시지 추가
        self.messages.append({"role": "user", "content": user_message})
        
        # API 호출 — 전체 히스토리를 보냄!
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=self.system,
            tools=tools,
            messages=self.messages,  # 👈 이전 대화 전부 포함!
        )
        
        # Tool Use 처리 (step2와 동일한 루프)
        while response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = tool_functions[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            
            self.messages.append({"role": "assistant", "content": response.content})
            self.messages.append({"role": "user", "content": tool_results})
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=self.system,
                tools=tools,
                messages=self.messages,
            )
        
        # 응답 텍스트 추출
        assistant_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_text += block.text
        
        # 히스토리에 응답 저장
        self.messages.append({"role": "assistant", "content": response.content})
        
        return assistant_text
    
    def show_history(self):
        """대화 히스토리 확인"""
        print(f"\n📜 대화 히스토리: {len(self.messages)}개 메시지")
        for msg in self.messages:
            role = "👤" if msg["role"] == "user" else "🤖"
            if isinstance(msg["content"], str):
                print(f"  {role} {msg['content'][:80]}")

"""
🔥 실습: 멀티턴 대화 테스트

agent = ConversationalAgent()

# 1번째 질문
print(agent.chat("냉장고 에러 테이블 구조 보여줘"))

# 2번째 질문 — "거기서"가 이전 맥락을 참조!
print(agent.chat("거기서 모델별 에러 수를 집계해줘"))

# 3번째 질문 — 계속 이어짐
print(agent.chat("가장 에러가 많은 모델은 뭐야?"))

# 히스토리 확인
agent.show_history()
"""


# ============================================================
# 🗓️ 수요일: 에러 핸들링 — 안 죽는 에이전트 만들기
# ============================================================

"""
📌 실전에서 에이전트가 죽는 이유 Top 3:
   1. API 호출 실패 (네트워크, 키 만료)
   2. 도구 실행 에러 (잘못된 SQL 등)
   3. JSON 파싱 실패 (Claude가 형식을 안 지킬 때)
   
   이걸 다 처리해야 "프로덕션 레벨" 에이전트입니다.
"""

import time

def robust_api_call(messages: list, max_retries: int = 3) -> dict:
    """재시도 로직이 있는 안전한 API 호출"""
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                tools=tools,
                messages=messages,
            )
            return response
            
        except anthropic.RateLimitError:
            # 요청이 너무 많을 때 — 잠깐 기다렸다 재시도
            wait_time = 2 ** attempt  # 1초, 2초, 4초 (지수 백오프)
            print(f"⏳ Rate limit! {wait_time}초 후 재시도... ({attempt+1}/{max_retries})")
            time.sleep(wait_time)
            
        except anthropic.APIError as e:
            # API 서버 에러
            print(f"❌ API 에러: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                raise
                
        except Exception as e:
            print(f"❌ 예상치 못한 에러: {e}")
            raise
    
    raise Exception("최대 재시도 횟수 초과")


def safe_tool_execution(tool_name: str, tool_input: dict) -> str:
    """안전한 도구 실행 — 에러가 나도 에이전트가 안 죽음"""
    try:
        func = tool_functions.get(tool_name)
        if not func:
            return json.dumps({"error": f"알 수 없는 도구: {tool_name}"})
        
        result = func(**tool_input)
        return json.dumps(result, ensure_ascii=False)
        
    except TypeError as e:
        return json.dumps({"error": f"파라미터 오류: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"도구 실행 실패: {str(e)}"})

"""
💡 핵심 포인트:
   도구 실행이 실패해도 에러 메시지를 Claude에게 돌려보내면,
   Claude가 "아, 실패했네. 다른 방법을 쓰자"라고 판단할 수 있습니다.
   에이전트가 스스로 복구하는 겁니다!
"""


# ============================================================
# 🗓️ 목요일: 스트리밍 — 실시간 응답 출력
# ============================================================

"""
📌 스트리밍이 뭐냐면:
   Claude가 답변을 다 만들 때까지 기다리지 않고,
   만들어지는 대로 한 글자씩 출력하는 겁니다.
   ChatGPT에서 글자가 하나씩 나오는 것처럼요.
   
   사용자 경험이 훨씬 좋아집니다!
"""

def streaming_chat(user_message: str):
    """스트리밍으로 실시간 응답 출력"""
    print(f"\n👤 {user_message}")
    print("🤖 ", end="", flush=True)
    
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    
    print()  # 줄바꿈

# streaming_chat("AI 에이전트의 미래에 대해 간단히 설명해줘")


# ============================================================
# 🗓️ 금요일: 미니 프로젝트 — 개인 비서 에이전트
# ============================================================

"""
🔥 이번 주 배운 것을 종합하는 미니 프로젝트!
   
   아래 코드를 완성해서 "나만의 개인 비서 에이전트"를 만들어보세요.
   이 구조가 Phase 3~4에서 발전시킬 기반이 됩니다.
"""

class PersonalAssistant:
    """개인 비서 에이전트 — 이번 주 배운 것 종합"""
    
    def __init__(self):
        self.messages = []
        self.system = """당신은 YongSeok의 개인 AI 비서입니다.
데이터 조회, 일정 관리, 코드 설명 등을 도와줍니다.
항상 한국어로, 친근하게 응대하세요.
복잡한 요청은 단계별로 나눠서 처리하세요."""
    
    def run(self):
        """대화형 루프"""
        print("🤖 안녕하세요! AI 비서입니다. ('quit'으로 종료)")
        print("-" * 50)
        
        while True:
            user_input = input("\n👤 You: ").strip()
            if user_input.lower() in ["quit", "exit", "종료"]:
                print("🤖 수고하셨습니다! 좋은 하루 되세요.")
                break
            
            if not user_input:
                continue
            
            response = self.chat(user_input)
            print(f"\n🤖 비서: {response}")
    
    def chat(self, user_message: str) -> str:
        """TODO: ConversationalAgent의 chat 메서드를 참고해서 구현하세요!"""
        # 힌트:
        # 1. self.messages에 user_message 추가
        # 2. robust_api_call로 API 호출
        # 3. tool_use 처리
        # 4. 응답 텍스트 반환
        pass  # ← 여기를 채워보세요!


# 실행:
# assistant = PersonalAssistant()
# assistant.run()

"""
✅ 이번 주 체크리스트:
   □ 여러 도구를 조합하는 에이전트 구현 가능
   □ 멀티턴 대화 히스토리 관리 이해
   □ 에러 핸들링 + 재시도 로직 구현 가능
   □ 스트리밍 응답 구현 가능
   □ 개인 비서 에이전트 미니 프로젝트 완성
"""
