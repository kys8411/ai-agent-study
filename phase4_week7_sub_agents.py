"""
============================================================
📘 Phase 4 | Week 7: 서브에이전트 패턴
============================================================
🎯 이번 주 목표: 에이전트가 다른 에이전트에게 일을 시키는 구조
   - 월: 서브에이전트가 필요한 이유
   - 화: 오케스트레이터 패턴 구현
   - 수: 전문가 서브에이전트 구현
   - 목: 에이전트 간 결과 전달
   - 금: 미니 프로젝트 — 데이터 분석 멀티에이전트

📌 서브에이전트 = "사장님 에이전트가 전문가 에이전트들에게 업무를 분배"
   Claude Code의 쓰레드 방식과 같은 원리!
============================================================
"""

import anthropic
import json
from typing import Optional

client = anthropic.Anthropic()


# ============================================================
# 🗓️ 월요일: 왜 서브에이전트가 필요한가?
# ============================================================

"""
📌 싱글 에이전트의 한계:

   하나의 에이전트가 모든 걸 하려면:
   1. system prompt가 엄청 길어짐 → 성능 저하
   2. 도구가 너무 많아짐 → 잘못된 도구 선택 확률 증가
   3. 복잡한 작업에서 맥락을 잃음
   4. 하나가 실패하면 전체가 멈춤
   
   서브에이전트로 나누면:
   1. 각 에이전트가 짧은 system prompt → 정확도 향상
   2. 각자 2~3개 도구만 관리 → 올바른 도구 선택
   3. 독립된 컨텍스트 → 맥락 유지
   4. 하나가 실패해도 다른 건 계속 동작

📌 Claude Code 쓰레드와의 연결:
   Claude Code에서 "작업별 세션 분리"하는 것과 같은 원리!
   각 세션(쓰레드)이 독립된 맥락을 가지듯,
   각 서브에이전트도 독립된 system prompt + context를 가집니다.
"""


# ============================================================
# 🗓️ 화요일: 오케스트레이터 패턴 구현
# ============================================================

"""
📌 오케스트레이터 = 지휘자
   오케스트라에서 지휘자가 "바이올린 시작! → 첼로 들어와!" 하듯이,
   메인 에이전트가 서브에이전트들을 순서대로 호출합니다.
"""

class SubAgent:
    """서브에이전트 기본 클래스"""
    
    def __init__(self, name: str, system_prompt: str, tools: list = None):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.client = anthropic.Anthropic()
    
    def execute(self, task: str, context: Optional[str] = None) -> dict:
        """
        작업을 실행하고 결과를 반환
        context: 이전 서브에이전트의 결과를 전달받을 수 있음
        """
        # 컨텍스트가 있으면 task에 추가
        full_task = task
        if context:
            full_task = f"## 이전 단계 결과:\n{context}\n\n## 현재 작업:\n{task}"
        
        messages = [{"role": "user", "content": full_task}]
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=self.system_prompt,
            tools=self.tools if self.tools else [],  # 빈 리스트면 도구 없이
            messages=messages,
        )
        
        # Tool Use 처리 (간략화)
        result_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                result_text += block.text
        
        return {
            "agent": self.name,
            "task": task,
            "result": result_text,
            "status": "success"
        }


class Orchestrator:
    """오케스트레이터 — 서브에이전트들을 관리하고 순서대로 실행"""
    
    def __init__(self):
        self.sub_agents = {}
        self.execution_log = []
    
    def register(self, agent: SubAgent):
        """서브에이전트 등록"""
        self.sub_agents[agent.name] = agent
        print(f"  ✅ 서브에이전트 등록: {agent.name}")
    
    def execute_pipeline(self, pipeline: list) -> list:
        """
        파이프라인 실행
        pipeline: [{"agent": "이름", "task": "할 일"}, ...]
        이전 단계의 결과가 다음 단계의 context로 전달됩니다.
        """
        results = []
        previous_result = None
        
        print(f"\n{'='*60}")
        print(f"🎯 파이프라인 시작 ({len(pipeline)}단계)")
        print(f"{'='*60}")
        
        for i, step in enumerate(pipeline, 1):
            agent_name = step["agent"]
            task = step["task"]
            
            print(f"\n--- Step {i}: [{agent_name}] ---")
            print(f"📋 Task: {task}")
            
            agent = self.sub_agents.get(agent_name)
            if not agent:
                print(f"❌ 에이전트 '{agent_name}'을 찾을 수 없음!")
                continue
            
            # 이전 결과를 context로 전달
            result = agent.execute(task, context=previous_result)
            results.append(result)
            
            print(f"✅ Result: {result['result'][:150]}...")
            
            # 다음 단계에 전달할 context 업데이트
            previous_result = result["result"]
            
            self.execution_log.append({
                "step": i,
                "agent": agent_name,
                "task": task,
                "status": result["status"]
            })
        
        print(f"\n{'='*60}")
        print(f"🏁 파이프라인 완료!")
        print(f"{'='*60}")
        
        return results


# ============================================================
# 🗓️ 수요일: 전문가 서브에이전트 만들기
# ============================================================

"""
📌 각 서브에이전트는 "전문 분야"가 있습니다.
   system prompt와 도구를 그 분야에 맞게 설정합니다.
"""

# --- SQL 전문가 에이전트 ---
sql_agent = SubAgent(
    name="sql_expert",
    system_prompt="""당신은 SQL 쿼리 생성 전문가입니다.
사용자의 자연어 요청을 Databricks SQL로 변환합니다.
반드시 실행 가능한 SQL만 생성하세요.
SQL 쿼리를 ```sql 블록으로 감싸서 출력하세요.

사용 가능한 테이블:
- refrigerator_errors (error_code, model, count, date)
- washer_status (model, status, cycle_count, date)
- ac_usage (model, temp_setting, usage_hours, date)
"""
)

# --- 데이터 검증 에이전트 ---
validation_agent = SubAgent(
    name="data_validator",
    system_prompt="""당신은 데이터 품질 검증 전문가입니다.
주어진 SQL 쿼리 결과를 분석하여:
1. 이상치가 있는지 확인
2. 데이터 누락이 의심되는지 확인
3. 결과의 신뢰도를 평가 (높음/중간/낮음)
4. 주의사항을 제시

검증 결과를 구조화하여 보고하세요.
"""
)

# --- 리포트 작성 에이전트 ---
report_agent = SubAgent(
    name="report_writer",
    system_prompt="""당신은 데이터 분석 리포트 작성 전문가입니다.
주어진 분석 결과와 검증 결과를 바탕으로:
1. 핵심 인사이트 요약 (3줄 이내)
2. 상세 분석 내용
3. 권장 조치사항
4. 다음 분석 제안

비즈니스 담당자가 이해할 수 있는 한국어로 작성하세요.
전문 용어는 괄호 안에 설명을 추가하세요.
"""
)


# ============================================================
# 🗓️ 목요일: 파이프라인 실행 — 에이전트 간 결과 전달
# ============================================================

"""
🔥 실습: 3단계 파이프라인 실행
"""

def run_analysis_pipeline():
    """데이터 분석 멀티에이전트 파이프라인"""
    
    # 오케스트레이터 생성 + 에이전트 등록
    orchestrator = Orchestrator()
    orchestrator.register(sql_agent)
    orchestrator.register(validation_agent)
    orchestrator.register(report_agent)
    
    # 파이프라인 정의
    pipeline = [
        {
            "agent": "sql_expert",
            "task": "냉장고 모델별 최근 30일간 에러 발생 건수를 집계하고, 가장 에러가 많은 모델 Top 5를 조회하는 SQL을 작성해줘"
        },
        {
            "agent": "data_validator",
            "task": "위 SQL 쿼리와 실행 결과를 검증해줘. 데이터 품질에 문제가 없는지 확인해줘."
        },
        {
            "agent": "report_writer",
            "task": "분석 결과와 검증 결과를 바탕으로 경영진에게 보고할 리포트를 작성해줘."
        }
    ]
    
    # 실행!
    results = orchestrator.execute_pipeline(pipeline)
    
    # 최종 리포트 출력
    print("\n\n📊 최종 리포트:")
    print(results[-1]["result"])

# run_analysis_pipeline()


# ============================================================
# 🗓️ 금요일: 미니 프로젝트 — 동적 라우팅 오케스트레이터
# ============================================================

"""
📌 고급 패턴: 오케스트레이터가 질문을 분석하고
   "어떤 서브에이전트에게 보낼지"를 스스로 판단하는 구조
   
   이건 Claude를 오케스트레이터로 쓰는 겁니다!
"""

class SmartOrchestrator:
    """Claude가 라우팅까지 판단하는 스마트 오케스트레이터"""
    
    def __init__(self):
        self.sub_agents = {}
        self.router_system = """당신은 AI 에이전트 오케스트레이터입니다.
사용자의 요청을 분석하고, 어떤 전문가 에이전트에게 어떤 순서로 일을 시킬지 결정합니다.

사용 가능한 서브에이전트:
- sql_expert: SQL 쿼리 생성 전문가
- data_validator: 데이터 품질 검증 전문가
- report_writer: 리포트 작성 전문가

반드시 아래 JSON 형식으로만 응답하세요:
{
    "analysis": "요청 분석 내용",
    "pipeline": [
        {"agent": "에이전트이름", "task": "구체적 지시사항"},
        ...
    ]
}
"""
    
    def register(self, agent: SubAgent):
        self.sub_agents[agent.name] = agent
    
    def process(self, user_request: str) -> str:
        """사용자 요청을 분석하고 자동으로 파이프라인 실행"""
        
        print(f"\n👤 요청: {user_request}")
        print(f"\n🧠 라우팅 분석 중...")
        
        # 1단계: Claude가 파이프라인을 설계
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=self.router_system,
            messages=[{"role": "user", "content": user_request}]
        )
        
        route_text = response.content[0].text
        
        try:
            # JSON 파싱 (```json 제거)
            clean = route_text.replace("```json", "").replace("```", "").strip()
            route = json.loads(clean)
            
            print(f"📋 분석: {route['analysis']}")
            print(f"🔄 파이프라인: {len(route['pipeline'])}단계")
            
            # 2단계: 설계된 파이프라인 실행
            orchestrator = Orchestrator()
            for agent in self.sub_agents.values():
                orchestrator.register(agent)
            
            results = orchestrator.execute_pipeline(route["pipeline"])
            return results[-1]["result"] if results else "처리할 수 없었습니다."
            
        except json.JSONDecodeError:
            print(f"⚠️ 라우팅 JSON 파싱 실패, 기본 흐름으로 처리")
            return route_text

"""
🔥 실습:

smart = SmartOrchestrator()
smart.register(sql_agent)
smart.register(validation_agent)
smart.register(report_agent)

# 간단한 요청 → SQL 에이전트만 동작
smart.process("냉장고 에러 Top 5 보여줘")

# 복잡한 요청 → 3단계 파이프라인 자동 구성
smart.process("냉장고 에러 트렌드를 분석하고 품질 검증까지 해서 경영진 리포트 만들어줘")

✅ 이번 주 체크리스트:
   □ 서브에이전트의 필요성과 장점 이해
   □ 오케스트레이터 패턴 구현 가능
   □ 전문가 서브에이전트 설계 가능
   □ 에이전트 간 결과 전달 구현
   □ 동적 라우팅 오케스트레이터 이해
"""
