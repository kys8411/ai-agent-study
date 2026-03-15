"""
============================================================
📘 Phase 4 | Week 8: 멀티에이전트 심화 + LangGraph
============================================================
🎯 이번 주 목표: 프로덕션 수준 멀티에이전트 시스템
   - 월: 독립 컨텍스트 (쓰레드) 패턴 구현
   - 화: 병렬 실행 — 여러 에이전트 동시 처리
   - 수: LangGraph 기초 — 에이전트 그래프 설계
   - 목: LangGraph로 멀티에이전트 워크플로우 구현
   - 금: 미니 프로젝트 — 도메인별 IoT 분석 시스템

📌 이번 주가 끝나면 1,900개 테이블을 
   도메인별 서브에이전트로 나누는 구조를 만들 수 있습니다!
============================================================
"""

import anthropic
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

client = anthropic.Anthropic()


# ============================================================
# 🗓️ 월요일: 독립 컨텍스트 (쓰레드) 패턴
# ============================================================

"""
📌 Claude Code 쓰레드의 원리를 코드로 구현!
   각 서브에이전트가 독립된 messages(대화 히스토리)를 가집니다.
   메인 에이전트와 서브에이전트의 메모리가 완전히 분리됩니다.
"""

class ThreadedSubAgent:
    """독립 컨텍스트를 가진 서브에이전트"""
    
    def __init__(self, name: str, system_prompt: str, tools: list = None):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.messages = []        # 👈 이 에이전트만의 독립 히스토리!
        self.client = anthropic.Anthropic()
    
    def chat(self, message: str) -> str:
        """멀티턴 대화 (히스토리 유지)"""
        self.messages.append({"role": "user", "content": message})
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=self.system_prompt,
            messages=self.messages,
        )
        
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text
        
        self.messages.append({"role": "assistant", "content": text})
        return text
    
    def reset(self):
        """컨텍스트 초기화 (새 쓰레드 시작)"""
        self.messages = []
        print(f"  🔄 [{self.name}] 컨텍스트 초기화 (새 쓰레드)")
    
    def get_context_length(self) -> int:
        """현재 컨텍스트 길이 확인"""
        total = sum(len(str(m["content"])) for m in self.messages)
        return total

"""
🔥 실습: 독립 쓰레드 확인

agent_a = ThreadedSubAgent("SQL전문가", "당신은 SQL 전문가입니다.")
agent_b = ThreadedSubAgent("리포트작가", "당신은 리포트 작성 전문가입니다.")

# Agent A에게 SQL 질문
agent_a.chat("냉장고 에러 Top 5 SQL 작성해줘")
agent_a.chat("거기에 날짜 필터도 추가해줘")  # "거기"를 이해함!

# Agent B에게 리포트 질문 — Agent A의 맥락과 완전히 분리!
agent_b.chat("아래 데이터로 리포트 작성해줘: RF-9000 에러 1,523건...")

# 각 에이전트의 컨텍스트 길이 확인
print(f"Agent A 컨텍스트: {agent_a.get_context_length()} chars")
print(f"Agent B 컨텍스트: {agent_b.get_context_length()} chars")
"""


# ============================================================
# 🗓️ 화요일: 병렬 실행 — 여러 에이전트 동시 처리
# ============================================================

"""
📌 병렬 실행이 왜 중요하냐면:
   "냉장고 + 세탁기 + 에어컨 에러 비교해줘"라는 질문에
   3개 에이전트를 순서대로 실행하면 30초 걸리지만,
   동시에 실행하면 10초면 됩니다!
"""

def run_agents_parallel(agents_tasks: list) -> list:
    """여러 서브에이전트를 동시에 실행"""
    
    results = [None] * len(agents_tasks)
    
    def execute_one(index, agent, task):
        """하나의 에이전트 실행 (스레드에서)"""
        print(f"  🚀 [{agent.name}] 시작: {task[:50]}...")
        result = agent.chat(task)
        results[index] = {"agent": agent.name, "result": result}
        print(f"  ✅ [{agent.name}] 완료!")
        return result
    
    with ThreadPoolExecutor(max_workers=len(agents_tasks)) as executor:
        futures = []
        for i, (agent, task) in enumerate(agents_tasks):
            future = executor.submit(execute_one, i, agent, task)
            futures.append(future)
        
        # 모든 에이전트가 완료될 때까지 대기
        for future in futures:
            future.result()
    
    return results

"""
🔥 실습: 3개 도메인 에이전트 병렬 실행

ref_agent = ThreadedSubAgent("냉장고전문가", "당신은 냉장고 데이터 분석 전문가입니다.")
wm_agent = ThreadedSubAgent("세탁기전문가", "당신은 세탁기 데이터 분석 전문가입니다.")
ac_agent = ThreadedSubAgent("에어컨전문가", "당신은 에어컨 데이터 분석 전문가입니다.")

results = run_agents_parallel([
    (ref_agent, "냉장고 에러 Top 3 분석해줘"),
    (wm_agent, "세탁기 점검 필요 모델 분석해줘"),
    (ac_agent, "에어컨 에너지 효율 낮은 모델 분석해줘"),
])

# 결과 종합
for r in results:
    print(f"\\n[{r['agent']}] {r['result'][:100]}...")
"""


# ============================================================
# 🗓️ 수~목요일: LangGraph 기초
# ============================================================

"""
📌 LangGraph가 뭐냐면:
   에이전트들의 실행 순서를 "그래프"로 그리는 프레임워크입니다.
   
   "A 다음에 B, B 결과에 따라 C 또는 D" 같은 복잡한 흐름을
   코드로 깔끔하게 표현할 수 있습니다.

💻 설치:
   pip install langgraph langchain-anthropic
"""

LANGGRAPH_EXAMPLE = """
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# 1. 상태 정의 — 에이전트 간 공유되는 데이터
class AgentState(TypedDict):
    question: str                          # 사용자 질문
    sql_query: str                         # SQL 전문가가 생성한 SQL
    query_result: str                      # DB에서 가져온 결과
    validation: str                        # 검증 에이전트 결과
    report: str                            # 최종 리포트
    messages: Annotated[list, operator.add] # 전체 메시지 히스토리

# 2. 각 노드(에이전트) 정의
def sql_expert_node(state: AgentState) -> AgentState:
    \"\"\"SQL 생성 노드\"\"\"
    # Claude API 호출해서 SQL 생성
    sql = generate_sql(state["question"])
    return {"sql_query": sql}

def execute_query_node(state: AgentState) -> AgentState:
    \"\"\"쿼리 실행 노드\"\"\"
    result = execute_sql(state["sql_query"])
    return {"query_result": result}

def validator_node(state: AgentState) -> AgentState:
    \"\"\"검증 노드\"\"\"
    validation = validate_result(state["query_result"])
    return {"validation": validation}

def report_node(state: AgentState) -> AgentState:
    \"\"\"리포트 노드\"\"\"
    report = write_report(state["query_result"], state["validation"])
    return {"report": report}

# 3. 분기 조건 — 검증 결과에 따라 다른 경로
def should_regenerate(state: AgentState) -> str:
    if "품질 낮음" in state["validation"]:
        return "regenerate"   # SQL 다시 생성
    return "continue"         # 리포트 작성으로 진행

# 4. 그래프 구성
workflow = StateGraph(AgentState)

# 노드 추가
workflow.add_node("sql_expert", sql_expert_node)
workflow.add_node("execute", execute_query_node)
workflow.add_node("validate", validator_node)
workflow.add_node("report", report_node)

# 엣지 (연결) 추가
workflow.set_entry_point("sql_expert")
workflow.add_edge("sql_expert", "execute")
workflow.add_edge("execute", "validate")

# 조건부 분기!
workflow.add_conditional_edges(
    "validate",
    should_regenerate,
    {
        "regenerate": "sql_expert",   # 다시 SQL 생성으로
        "continue": "report"          # 리포트로 진행
    }
)
workflow.add_edge("report", END)

# 5. 실행
app = workflow.compile()
result = app.invoke({"question": "냉장고 에러 트렌드 분석해줘"})
print(result["report"])
"""

"""
📌 LangGraph의 핵심:
   - 노드(Node) = 에이전트 또는 작업
   - 엣지(Edge) = 실행 순서
   - 조건부 엣지 = 결과에 따라 다른 경로
   - 상태(State) = 에이전트 간 공유 데이터
   
   이걸 그림으로 그리면:
   
   [SQL전문가] → [쿼리실행] → [검증] ─┬─→ [리포트] → END
                                      │
                                      └─→ [SQL전문가] (재시도)
"""


# ============================================================
# 🗓️ 금요일: 미니 프로젝트 — 도메인별 IoT 분석 시스템
# ============================================================

"""
🔥 최종 미니 프로젝트: LG전자 IoT 멀티에이전트 시스템

[사용자: "전체 가전 제품 이상 현황 리포트 만들어줘"]
    │
    ▼
[라우터 에이전트] ← Claude가 질문을 분석
    │ "이건 냉장고, 세탁기, 에어컨 전부 필요하네"
    │
    ├──→ [냉장고 에이전트] ──→ 냉장고 분석 결과
    │     (300개 테이블)        (병렬!)
    │
    ├──→ [세탁기 에이전트] ──→ 세탁기 분석 결과
    │     (250개 테이블)        (병렬!)
    │
    └──→ [에어컨 에이전트] ──→ 에어컨 분석 결과
          (200개 테이블)        (병렬!)
    │
    ▼
[종합 리포트 에이전트]
    │ 3개 결과를 합쳐서 경영진 리포트 생성
    ▼
[최종 리포트 출력]
"""

class IoTMultiAgentSystem:
    """LG전자 IoT 멀티에이전트 시스템"""
    
    def __init__(self):
        # 도메인별 전문가 에이전트
        self.domain_agents = {
            "냉장고": ThreadedSubAgent(
                "냉장고분석가",
                """당신은 LG 냉장고 데이터 전문가입니다.
냉장고 관련 테이블: refrigerator_errors, ref_defrost, ref_temp_sensor, ref_door_events
에러 코드, 온도 이상, 제상 주기, 도어 개폐 패턴을 분석합니다."""
            ),
            "세탁기": ThreadedSubAgent(
                "세탁기분석가",
                """당신은 LG 세탁기 데이터 전문가입니다.
세탁기 관련 테이블: washer_status, wm_cycle, wm_vibration, wm_water_usage
사이클 수, 진동 이상, 수위 패턴을 분석합니다."""
            ),
            "에어컨": ThreadedSubAgent(
                "에어컨분석가",
                """당신은 LG 에어컨 데이터 전문가입니다.
에어컨 관련 테이블: ac_usage, ac_filter, ac_compressor, ac_energy
에너지 효율, 필터 상태, 압축기 부하를 분석합니다."""
            ),
        }
        
        # 종합 리포트 에이전트
        self.report_agent = ThreadedSubAgent(
            "종합리포터",
            """당신은 LG전자 IoT 데이터 분석 리포트 전문가입니다.
여러 도메인(냉장고/세탁기/에어컨)의 분석 결과를 종합하여
경영진이 의사결정에 활용할 수 있는 리포트를 작성합니다.
한국어로, 핵심 위주로, 차트 제안을 포함하세요."""
        )
    
    def analyze(self, question: str) -> str:
        """사용자 질문을 분석하고 적절한 에이전트 실행"""
        
        print(f"\n{'='*60}")
        print(f"🏭 IoT 멀티에이전트 시스템")
        print(f"👤 질문: {question}")
        print(f"{'='*60}")
        
        # 1단계: 라우팅 — 어떤 도메인 에이전트가 필요한지 판단
        router_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system="""사용자 질문을 분석하여 관련 도메인을 JSON으로 반환하세요.
도메인: 냉장고, 세탁기, 에어컨
형식: {"domains": ["냉장고", "세탁기"], "analysis_type": "에러분석"}
JSON만 출력하세요.""",
            messages=[{"role": "user", "content": question}]
        )
        
        try:
            clean = router_response.content[0].text.replace("```json", "").replace("```", "").strip()
            route = json.loads(clean)
            domains = route.get("domains", ["냉장고"])
        except (json.JSONDecodeError, KeyError):
            domains = ["냉장고"]  # 기본값
        
        print(f"\n🔀 라우팅 결과: {domains}")
        
        # 2단계: 도메인별 에이전트 병렬 실행
        agents_tasks = []
        for domain in domains:
            if domain in self.domain_agents:
                agents_tasks.append((
                    self.domain_agents[domain],
                    f"다음 질문에 대해 {domain} 관점에서 분석해줘: {question}"
                ))
        
        print(f"\n⚡ {len(agents_tasks)}개 에이전트 병렬 실행...")
        domain_results = run_agents_parallel(agents_tasks)
        
        # 3단계: 결과 종합
        combined = "\n\n".join([
            f"## [{r['agent']}] 분석 결과:\n{r['result']}"
            for r in domain_results if r
        ])
        
        final_report = self.report_agent.chat(
            f"아래 도메인별 분석 결과를 종합하여 경영진 리포트를 작성해줘:\n\n{combined}"
        )
        
        return final_report

"""
🔥 실습:

system = IoTMultiAgentSystem()

# 단일 도메인
print(system.analyze("냉장고 에러가 급증한 모델이 있어?"))

# 멀티 도메인
print(system.analyze("전체 가전 제품의 이번 달 이상 현황을 비교 분석해줘"))

# 특정 비교
print(system.analyze("냉장고와 에어컨 중 어떤 제품이 더 AS 요청이 많아?"))


✅ 이번 주 체크리스트:
   □ 독립 컨텍스트(쓰레드) 패턴 구현 가능
   □ 병렬 실행으로 성능 최적화 가능
   □ LangGraph 기본 구조 이해
   □ 조건부 분기(conditional edge) 구현 가능
   □ 도메인별 멀티에이전트 시스템 설계 + 구현
"""
