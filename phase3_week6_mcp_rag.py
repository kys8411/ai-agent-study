"""
============================================================
📘 Phase 3 | Week 6: MCP + RAG 파이프라인
============================================================
🎯 이번 주 목표: 에이전트를 외부 시스템과 연결하기
   - 월: MCP(Model Context Protocol) 개념 이해
   - 화: MCP 서버 직접 만들기
   - 수: RAG 개념 + 벡터 검색 기초
   - 목: 테이블 메타데이터 RAG 구현
   - 금: MCP + RAG 통합 에이전트

📌 MCP = Claude가 외부 도구/데이터에 접근하는 표준 프로토콜
📌 RAG = 필요한 정보를 검색해서 LLM에 넣어주는 기법
============================================================
"""


# ============================================================
# 🗓️ 월요일: MCP 개념 이해
# ============================================================

"""
📌 MCP(Model Context Protocol)가 뭐냐면:
   Tool Use가 "Claude에게 도구를 알려주는 것"이라면,
   MCP는 "도구를 표준화된 방식으로 제공하는 프로토콜"입니다.
   
   비유하면:
   - Tool Use = USB 포트에 직접 납땜하는 것
   - MCP = USB 규격을 정해서 아무 기기나 꽂으면 되는 것
   
   MCP로 한 번 만들면:
   - Claude Code에서도 쓸 수 있고
   - Claude Desktop에서도 쓸 수 있고
   - 다른 LLM에서도 쓸 수 있습니다!

📚 공식 문서: https://modelcontextprotocol.io/
   이동 시간에 읽어오세요!
"""


# ============================================================
# 🗓️ 화요일: MCP 서버 직접 만들기
# ============================================================

"""
📌 MCP 서버 = 도구를 제공하는 서버
   Claude Code가 이 서버에 연결하면 도구를 자동으로 인식합니다.

💻 설치:
   pip install mcp

아래는 간단한 MCP 서버 예시입니다.
별도 파일(mcp_server.py)로 저장해서 실행하세요.
"""

MCP_SERVER_CODE = '''
"""
MCP 서버 예시: 데이터 카탈로그 조회 도구
이 서버를 실행하면 Claude Code에서 데이터 카탈로그를 조회할 수 있습니다.
"""
from mcp.server.fastmcp import FastMCP

# MCP 서버 생성
mcp = FastMCP("data-catalog")

# 가짜 데이터 카탈로그 (실전에서는 DB 연결)
CATALOG = {
    "refrigerator_errors": {
        "description": "냉장고 에러 로그 테이블",
        "domain": "냉장고",
        "columns": ["error_code", "model", "count", "date"],
        "owner": "Data Operations Team",
        "update_frequency": "daily"
    },
    "washer_status": {
        "description": "세탁기 상태 모니터링 테이블",
        "domain": "세탁기",
        "columns": ["model", "status", "cycle_count", "date"],
        "owner": "Data Operations Team",
        "update_frequency": "daily"
    },
    "ac_usage": {
        "description": "에어컨 사용 패턴 테이블",
        "domain": "에어컨",
        "columns": ["model", "temp_setting", "usage_hours", "date"],
        "owner": "Data Operations Team",
        "update_frequency": "daily"
    }
}

@mcp.tool()
def search_tables(keyword: str) -> str:
    """키워드로 데이터 카탈로그에서 테이블을 검색합니다."""
    results = []
    for table_name, info in CATALOG.items():
        if keyword.lower() in table_name.lower() or keyword.lower() in info["description"].lower():
            results.append({"table": table_name, **info})
    
    if not results:
        return f"'{keyword}'와 관련된 테이블을 찾지 못했습니다."
    return str(results)

@mcp.tool()
def get_table_detail(table_name: str) -> str:
    """특정 테이블의 상세 정보를 조회합니다."""
    info = CATALOG.get(table_name)
    if not info:
        return f"테이블 '{table_name}'을 찾을 수 없습니다."
    return str({"table": table_name, **info})

@mcp.tool()
def list_tables_by_domain(domain: str) -> str:
    """도메인(가전제품)별 테이블 목록을 조회합니다."""
    results = []
    for table_name, info in CATALOG.items():
        if domain in info["domain"]:
            results.append(table_name)
    return str(results) if results else f"'{domain}' 도메인의 테이블이 없습니다."

# 서버 실행
if __name__ == "__main__":
    mcp.run(transport="stdio")
'''

"""
💻 실행 방법:
   1. 위 코드를 mcp_data_catalog.py로 저장
   2. Claude Code에서 연결:
      claude --mcp-config config.json
      
   config.json 예시:
   {
     "mcpServers": {
       "data-catalog": {
         "command": "python",
         "args": ["mcp_data_catalog.py"]
       }
     }
   }
   
   3. Claude Code에서 테스트:
      > 냉장고 관련 테이블 검색해줘
      → Claude가 MCP 도구를 자동으로 사용!
"""


# ============================================================
# 🗓️ 수~목요일: RAG — 1,900개 테이블에서 필요한 것만 찾기
# ============================================================

"""
📌 RAG(Retrieval Augmented Generation)가 뭐냐면:
   1,900개 테이블 정보를 전부 Claude에게 줄 수 없으니까,
   질문과 관련된 테이블만 "검색"해서 context에 넣어주는 기법입니다.
   
   흐름:
   사용자: "냉장고 에러 트렌드 보여줘"
        ↓
   [검색] "냉장고 에러"로 벡터 검색 → 관련 테이블 3~5개 발견
        ↓
   [생성] 찾은 테이블 정보를 Claude context에 넣고 SQL 생성
        ↓
   Claude: SELECT ... FROM refrigerator_errors ...
"""

# pip install chromadb  (벡터 DB)

RAG_EXAMPLE_CODE = """
import chromadb

# 1. 벡터 DB 생성
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("table_catalog")

# 2. 테이블 메타데이터를 벡터로 저장
tables_metadata = [
    {"id": "ref_errors", "doc": "냉장고 에러 로그 테이블. 에러코드, 모델명, 발생횟수, 날짜 포함. 냉장고 고장 분석에 사용.", "table": "refrigerator_errors"},
    {"id": "wm_status", "doc": "세탁기 상태 모니터링. 모델, 상태, 사이클수, 날짜. 세탁기 점검 시기 판단에 사용.", "table": "washer_status"},
    {"id": "ac_usage", "doc": "에어컨 사용 패턴. 모델, 설정온도, 사용시간, 날짜. 에너지 효율 분석에 사용.", "table": "ac_usage"},
    # ... 1,900개 테이블 전부 등록
]

collection.add(
    documents=[t["doc"] for t in tables_metadata],
    metadatas=[{"table": t["table"]} for t in tables_metadata],
    ids=[t["id"] for t in tables_metadata]
)

# 3. 사용자 질문으로 관련 테이블 검색
results = collection.query(
    query_texts=["냉장고 에러가 가장 많은 모델"],
    n_results=3  # 상위 3개 테이블
)

print("🔍 관련 테이블:", results["metadatas"])
# → [{"table": "refrigerator_errors"}, ...]

# 4. 찾은 테이블 정보를 Claude의 system prompt에 동적으로 삽입!
relevant_tables = results["documents"][0]  # 검색된 테이블 설명
dynamic_system = f"사용 가능한 테이블 정보:\\n{relevant_tables}"
"""

"""
🔥 실습 과제:
   1. chromadb를 설치하고 위 코드를 실행
   2. 다양한 질문으로 검색해보기:
      - "세탁기 고장" → washer_status가 나오는지?
      - "에너지 효율" → ac_usage가 나오는지?
   3. 검색 결과를 step3의 NL2SQL 에이전트에 연결해보기
"""


# ============================================================
# 🗓️ 금요일: MCP + RAG 통합 아키텍처 설계
# ============================================================

"""
📝 이번 주 마무리: 전체 아키텍처를 그려보세요

[사용자 질문: "냉장고 에러 트렌드 보여줘"]
    │
    ▼
[RAG 모듈: 벡터 검색]
    │ "냉장고 에러" → refrigerator_errors 테이블 발견
    ▼
[에이전트: Claude + Tool Use]
    │ System Prompt에 검색된 테이블 정보 삽입
    │ Claude가 SQL 생성
    ▼
[MCP 서버: DB 연결]
    │ SQL 실행 → 결과 반환
    ▼
[에이전트: 결과 해석]
    │ Claude가 결과를 자연어로 설명
    ▼
[사용자에게 답변]

이 구조가 Phase 4 (서브에이전트)로 발전합니다!

✅ 이번 주 체크리스트:
   □ MCP 개념 이해 + 서버 구현 가능
   □ Claude Code와 MCP 연동 확인
   □ RAG의 필요성과 동작 원리 이해
   □ 벡터 DB에 메타데이터 저장/검색 가능
   □ MCP + RAG 통합 아키텍처 설계 완료
"""
