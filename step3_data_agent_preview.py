"""
============================================================
⭐ Step 3 (보너스): 실무 연결 — 자연어 → SQL 에이전트
============================================================
시간이 남으면 도전! 안 되면 내일 아침에 이어서 하세요.

이건 Step 2의 Tool Use를 "데이터 조회"에 적용한 버전입니다.
YongSeok님의 Genie 프로젝트와 직접 연결되는 패턴이에요!

흐름:
  사용자: "냉장고 에러 코드 Top 5 보여줘"
  Claude: → query_database(sql="SELECT ...") 호출
  코드:  → SQL 실행 후 결과 반환
  Claude: "가장 많은 에러 코드는 E001로 전체의 23%를 차지합니다..."
============================================================
"""

import anthropic
import json

client = anthropic.Anthropic()

# ============================================================
# 📌 도구 정의: SQL 쿼리 실행 도구
# ============================================================
tools = [
    {
        "name": "query_database",
        "description": """데이터베이스에 SQL 쿼리를 실행합니다. 
사용 가능한 테이블:
- refrigerator_errors: 냉장고 에러 로그 (columns: error_code, model, count, date)
- washer_status: 세탁기 상태 데이터 (columns: model, status, cycle_count, date)
- ac_usage: 에어컨 사용 데이터 (columns: model, temp_setting, usage_hours, date)
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "실행할 SQL 쿼리"
                }
            },
            "required": ["sql"]
        }
    }
]


# ============================================================
# 📌 가짜 DB 실행 함수 (나중에 Databricks 연결로 교체!)
# ============================================================
def query_database(sql: str) -> dict:
    """
    가짜 SQL 실행 결과 반환
    실전에서는 여기를 Databricks SQL connector로 교체하면 됩니다!
    
    예: 
    from databricks import sql as dbsql
    connection = dbsql.connect(...)
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    """
    
    # 학습용 가짜 데이터
    if "refrigerator" in sql.lower() or "냉장고" in sql.lower():
        return {
            "columns": ["error_code", "model", "count"],
            "rows": [
                ["E001", "RF-9000", 1523],
                ["E003", "RF-8500", 987],
                ["E007", "RF-9000", 654],
                ["E002", "RF-7000", 432],
                ["E010", "RF-8500", 321],
            ],
            "row_count": 5
        }
    elif "washer" in sql.lower() or "세탁기" in sql.lower():
        return {
            "columns": ["model", "avg_cycle_count", "status"],
            "rows": [
                ["WM-3000", 2847, "정상"],
                ["WM-2500", 1923, "정상"],
                ["WM-3000", 3102, "점검필요"],
            ],
            "row_count": 3
        }
    else:
        return {"columns": [], "rows": [], "row_count": 0, "message": "해당 테이블을 찾을 수 없습니다"}


tool_functions = {"query_database": query_database}


# ============================================================
# 📌 에이전트 실행 (Step 2와 동일한 구조!)
# ============================================================
def run_data_agent(user_message: str):
    """데이터 조회 에이전트"""
    
    print(f"\n{'='*60}")
    print(f"👤 사용자: {user_message}")
    print(f"{'='*60}")
    
    messages = [{"role": "user", "content": user_message}]
    
    # system prompt로 에이전트 역할 부여
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system="""당신은 LG전자 IoT 데이터 분석 에이전트입니다.
사용자의 자연어 질문을 SQL로 변환하여 데이터를 조회하고,
결과를 이해하기 쉽게 설명해주세요.
항상 한국어로 응답하세요.""",    # 👈 system prompt로 에이전트 성격 부여!
        tools=tools,
        messages=messages,
    )
    
    while response.stop_reason == "tool_use":
        tool_use_block = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use_block = block
                break
        
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input
        tool_use_id = tool_use_block.id
        
        print(f"\n🔧 생성된 SQL:\n   {tool_input.get('sql', '')}")
        
        tool_result = tool_functions[tool_name](**tool_input)
        
        print(f"📊 조회 결과: {tool_result['row_count']}건")
        
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            ],
        })
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="당신은 LG전자 IoT 데이터 분석 에이전트입니다. 사용자의 자연어 질문을 SQL로 변환하여 데이터를 조회하고, 결과를 이해하기 쉽게 설명해주세요.",
            tools=tools,
            messages=messages,
        )
    
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text
    
    print(f"\n💬 분석 결과:\n{final_text}")
    print(f"\n{'='*60}\n")
    
    return final_text


# ============================================================
# 📌 테스트!
# ============================================================
if __name__ == "__main__":
    
    # 자연어로 데이터 질문하기
    run_data_agent("냉장고 에러 코드 Top 5 보여줘")
    
    run_data_agent("세탁기 중에서 점검이 필요한 모델이 있어?")
    
    run_data_agent("냉장고 RF-9000 모델에서 가장 많이 발생하는 에러가 뭐야?")


"""
============================================================
🎯 이 코드의 핵심 포인트:
============================================================
1. Tool 정의에 "테이블 스키마 정보"를 넣으면 Claude가 알아서 SQL을 생성함
2. system prompt로 에이전트의 역할과 성격을 부여할 수 있음
3. query_database 함수를 진짜 DB 커넥터로 바꾸면 바로 실전 투입 가능

🔗 Genie 프로젝트와의 연결:
- 이 패턴이 바로 자연어 → SQL 에이전트의 기본 구조
- 테이블 메타데이터를 tool description에 잘 넣는 게 성능의 핵심
- 1,900개 테이블을 전부 넣을 수는 없으니 → RAG로 관련 테이블만 찾아서 넣기 (다음 주제!)
============================================================
"""
