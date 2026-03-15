"""
============================================================
📘 Phase 3 | Week 5: ReAct 패턴 + 자연어→SQL 에이전트
============================================================
🎯 이번 주 목표: 에이전트의 "사고 과정"을 설계하기
   - 월: ReAct 패턴 이해 + 직접 구현
   - 화: 자연어→SQL 에이전트 v1 (단일 테이블)
   - 수: 자연어→SQL 에이전트 v2 (멀티 테이블 + JOIN)
   - 목: SQL 검증 + 자동 수정 에이전트
   - 금: Genie 프로젝트 연결 설계

📌 ReAct = Reasoning(추론) + Acting(행동)
   Claude가 "생각하고 → 행동하고 → 관찰하고 → 다시 생각하는" 루프
============================================================
"""

import anthropic
import json

client = anthropic.Anthropic()


# ============================================================
# 🗓️ 월요일: ReAct 패턴 직접 구현
# ============================================================

"""
📌 ReAct가 뭐냐면:
   보통 에이전트: "질문 받으면 바로 도구 실행"
   ReAct 에이전트: "질문 받으면 먼저 생각 → 도구 실행 → 결과 관찰 → 다시 생각"
   
   사람이 문제를 풀 때와 같은 과정입니다:
   "음... 이 문제는 먼저 A를 확인해야겠다" (Reasoning)
   → A를 확인함 (Acting)
   → "A 결과가 이렇네, 그러면 B를 해봐야겠다" (Reasoning)
   → B를 실행 (Acting)
   → "다 됐다, 최종 답은 이거다" (Final Answer)
"""

REACT_SYSTEM_PROMPT = """당신은 ReAct 방식으로 사고하는 데이터 분석 에이전트입니다.

모든 작업에서 다음 과정을 따르세요:

## 사고 과정
1. **Thought**: 무엇을 해야 하는지 먼저 생각합니다.
2. **Action**: 필요한 도구를 호출합니다.
3. **Observation**: 도구 결과를 관찰합니다.
4. **Thought**: 결과를 바탕으로 다음 단계를 생각합니다.
5. 필요하면 2~4를 반복합니다.
6. **Final Answer**: 충분한 정보가 모이면 최종 답변을 제공합니다.

매 단계에서 [Thought], [Action], [Observation] 태그를 사용하여 
사고 과정을 명시적으로 보여주세요.

사용 가능한 테이블:
- refrigerator_errors (error_code, model, count, date)
- washer_status (model, status, cycle_count, date)
- ac_usage (model, temp_setting, usage_hours, date)
"""

tools_for_react = [
    {
        "name": "query_database",
        "description": "SQL 쿼리를 실행합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "실행할 SQL"},
                "purpose": {"type": "string", "description": "이 쿼리의 목적"}
            },
            "required": ["sql", "purpose"]
        }
    },
    {
        "name": "get_table_info",
        "description": "테이블 스키마와 샘플 데이터를 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "테이블 이름"}
            },
            "required": ["table_name"]
        }
    }
]

"""
🔥 실습: ReAct 에이전트에게 이 질문을 던져보세요:
   "지난 달 냉장고와 세탁기 중 어떤 제품군에서 문제가 더 많았어?"
   
   Claude가 단계적으로 사고하는 과정을 관찰하세요:
   [Thought] 냉장고와 세탁기 각각의 문제 수를 비교해야겠다
   [Action] 냉장고 에러 수 조회
   [Observation] 냉장고 에러: 3,500건
   [Thought] 이제 세탁기도 확인해봐야겠다
   [Action] 세탁기 문제 수 조회
   [Observation] 세탁기 문제: 1,200건
   [Thought] 냉장고가 약 3배 더 많다. 최종 답변을 정리하자.
   [Final Answer] 지난 달 냉장고(3,500건)가 세탁기(1,200건)보다...
"""


# ============================================================
# 🗓️ 화~수요일: 자연어 → SQL 에이전트 (핵심!)
# ============================================================

"""
📌 이 에이전트가 왜 중요하냐면:
   Genie 프로젝트의 핵심 기능이 바로 이것입니다!
   사용자가 "냉장고 에러 Top 5"라고 하면
   자동으로 SQL을 만들어서 실행하는 에이전트.
"""

NL2SQL_SYSTEM = """당신은 자연어를 SQL로 변환하는 전문 에이전트입니다.

## 작업 순서
1. 사용자 질문을 분석하여 필요한 테이블과 컬럼을 파악합니다.
2. 테이블 스키마가 확실하지 않으면 get_table_info로 확인합니다.
3. SQL을 생성하고 query_database로 실행합니다.
4. 결과를 사용자가 이해하기 쉽게 설명합니다.

## SQL 작성 규칙
- Databricks SQL 문법을 사용합니다.
- 집계 시 반드시 GROUP BY를 사용합니다.
- 날짜 필터는 date 컬럼을 사용합니다.
- 일별 집계 테이블이므로 가중평균에 주의합니다.
- 순위를 매길 때 동점 가능성이 있으면 RANK()를, 없으면 ROW_NUMBER()를 사용합니다.
- LAG/LEAD 윈도우 함수에서 ORDER BY 방향에 주의합니다.
"""

class NL2SQLAgent:
    """자연어 → SQL 변환 에이전트"""
    
    def __init__(self):
        self.messages = []
        # 쿼리 히스토리 저장 (어떤 SQL이 생성됐는지 추적)
        self.query_history = []
    
    def ask(self, question: str) -> str:
        """자연어 질문을 SQL로 변환하고 실행"""
        self.messages.append({"role": "user", "content": question})
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=NL2SQL_SYSTEM,
            tools=tools_for_react,
            messages=self.messages,
        )
        
        # Tool Use 루프
        while response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  🔧 {block.name}: {json.dumps(block.input, ensure_ascii=False)[:100]}")
                    
                    # SQL 쿼리 히스토리 저장
                    if block.name == "query_database":
                        self.query_history.append(block.input.get("sql", ""))
                    
                    result = self._execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            
            self.messages.append({"role": "assistant", "content": response.content})
            self.messages.append({"role": "user", "content": tool_results})
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=NL2SQL_SYSTEM,
                tools=tools_for_react,
                messages=self.messages,
            )
        
        answer = ""
        for block in response.content:
            if hasattr(block, "text"):
                answer += block.text
        
        self.messages.append({"role": "assistant", "content": response.content})
        return answer
    
    def _execute_tool(self, name: str, input_data: dict) -> dict:
        """도구 실행 (가짜 데이터)"""
        if name == "get_table_info":
            return {
                "table": input_data["table_name"],
                "columns": [
                    {"name": "error_code", "type": "STRING"},
                    {"name": "model", "type": "STRING"},
                    {"name": "count", "type": "INT"},
                    {"name": "date", "type": "DATE"}
                ],
                "sample_rows": [
                    ["E001", "RF-9000", 45, "2025-02-01"],
                    ["E003", "RF-8500", 32, "2025-02-01"]
                ]
            }
        elif name == "query_database":
            return {
                "columns": ["error_code", "total_count"],
                "rows": [["E001", 1523], ["E003", 987], ["E007", 654]],
                "row_count": 3
            }
        return {"error": "Unknown tool"}
    
    def show_generated_sqls(self):
        """지금까지 생성된 SQL 확인"""
        print("\n📋 생성된 SQL 히스토리:")
        for i, sql in enumerate(self.query_history, 1):
            print(f"  {i}. {sql}")

"""
🔥 실습:
agent = NL2SQLAgent()

print(agent.ask("냉장고 에러 코드별 발생 횟수 Top 3 보여줘"))
print(agent.ask("그중에서 RF-9000 모델만 필터링하면?"))  # 멀티턴!

agent.show_generated_sqls()  # 어떤 SQL이 생성됐는지 확인
"""


# ============================================================
# 🗓️ 목요일: SQL 검증 + 자동 수정
# ============================================================

"""
📌 실전에서는 Claude가 잘못된 SQL을 생성할 수 있습니다.
   "SQL 실행 → 에러 발생 → 에러 메시지를 Claude에게 전달 → SQL 수정"
   이 자동 수정 루프가 프로덕션 에이전트의 핵심!
"""

SQL_VALIDATOR_PROMPT = """당신은 SQL 검증 및 수정 에이전트입니다.

SQL 실행 결과가 에러이면:
1. 에러 메시지를 분석합니다.
2. 원인을 파악합니다. (컬럼명 오타, 문법 에러, 타입 불일치 등)
3. 수정된 SQL을 생성합니다.
4. 다시 실행합니다.

최대 3번까지 재시도하고, 그래도 실패하면 사용자에게 알립니다.
"""

"""
🔥 실습: 일부러 잘못된 SQL 시나리오를 만들어서 테스트
   → query_database 함수에서 에러를 반환하게 만들고
   → Claude가 자동으로 SQL을 수정하는지 관찰
"""


# ============================================================
# 🗓️ 금요일: Genie 프로젝트 연결 설계
# ============================================================

"""
📝 이번 주를 마무리하며, 실무 Genie 프로젝트에 적용할 설계를 정리하세요.

생각해볼 질문들:
1. Genie Space의 Instructions에 어떤 정보를 넣어야 하나?
   → 테이블 스키마, 비즈니스 용어 정의, SQL 작성 규칙
   
2. 1,900개 테이블을 전부 context에 넣을 수 없으면?
   → RAG로 관련 테이블만 검색해서 넣기 (다음 주!)
   
3. 멀티턴 대화에서 temporal condition은?
   → "지난 달" → 구체적 날짜로 변환하는 로직 필요
   
4. 집계 테이블에서 가중평균은?
   → daily 집계 + monthly 재집계 시 SUM/COUNT 주의

✅ 이번 주 체크리스트:
   □ ReAct 패턴의 사고 과정 이해 + 구현
   □ 자연어→SQL 에이전트 동작 확인
   □ 멀티턴 SQL 대화 구현
   □ SQL 자동 수정 패턴 이해
   □ Genie 프로젝트 연결 포인트 정리
"""
