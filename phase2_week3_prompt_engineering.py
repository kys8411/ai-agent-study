"""
============================================================
📘 Phase 2 | Week 3: 프롬프트 엔지니어링 + API 심화
============================================================
🎯 이번 주 목표: LLM을 "잘" 다루는 법 익히기
   - 월: system prompt의 위력
   - 화: few-shot / chain-of-thought 기법
   - 수: 출력 형식 제어 (JSON, 구조화)
   - 목: 토큰, 컨텍스트 윈도우, temperature 실험
   - 금: 프롬프트 템플릿 라이브러리 만들기

📌 전제: step1_basic_api_call.py를 성공적으로 실행한 상태
============================================================
"""

import anthropic
import json

client = anthropic.Anthropic()


# ============================================================
# 🗓️ 월요일: System Prompt — 에이전트의 성격을 결정하는 핵심
# ============================================================

"""
📌 System Prompt가 뭐냐면:
   Claude에게 "너는 이런 사람이야"라고 역할을 부여하는 겁니다.
   같은 질문이라도 system prompt에 따라 완전히 다른 답이 나옵니다.
   에이전트를 만들 때 가장 중요한 부분이에요!
"""

def test_system_prompt(system: str, question: str):
    """system prompt에 따라 응답이 어떻게 달라지는지 테스트"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": question}]
    )
    print(f"\n📋 System: {system[:60]}...")
    print(f"👤 질문: {question}")
    print(f"🤖 응답: {response.content[0].text[:200]}")
    print("-" * 50)

# 🔥 실습: 같은 질문, 다른 system prompt
QUESTION = "냉장고 온도가 자꾸 올라가요"

# 실행해보세요! 각각 어떻게 다른지 비교
# test_system_prompt(
#     "당신은 LG전자 가전 고객센터 상담원입니다. 친절하고 정중하게 응대하세요.",
#     QUESTION
# )
# test_system_prompt(
#     "당신은 냉장고 수리 전문 엔지니어입니다. 기술적 원인과 해결 방법을 상세히 설명하세요.",
#     QUESTION
# )
# test_system_prompt(
#     "당신은 IoT 데이터 분석가입니다. 센서 데이터 관점에서 원인을 분석하세요.",
#     QUESTION
# )


# ============================================================
# 🗓️ 화요일: Few-Shot + Chain-of-Thought
# ============================================================

"""
📌 Few-Shot이 뭐냐면:
   "이런 식으로 해줘"라고 예시를 보여주는 겁니다.
   예시를 2~3개 주면 Claude가 패턴을 이해하고 따라합니다.

📌 Chain-of-Thought(CoT)가 뭐냐면:
   "단계별로 생각해서 답해줘"라고 하는 겁니다.
   복잡한 문제에서 정확도가 크게 올라갑니다.
"""

def few_shot_example():
    """Few-Shot: 테이블 분류 에이전트 예시"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system="""당신은 데이터 테이블 분류 전문가입니다.
테이블 이름을 보고 어떤 가전제품 도메인에 속하는지 분류하세요.

## 예시 (Few-Shot)
테이블: ref_error_log → 도메인: 냉장고, 분류: 에러로그
테이블: wm_cycle_data → 도메인: 세탁기, 분류: 사용데이터  
테이블: ac_temp_sensor → 도메인: 에어컨, 분류: 센서데이터

## 출력 형식
도메인: [가전제품명]
분류: [데이터유형]
확신도: [상/중/하]
""",
        messages=[{"role": "user", "content": "테이블: ref_defrost_cycle_history"}]
    )
    print(response.content[0].text)

# few_shot_example()


def chain_of_thought_example():
    """CoT: 단계적 사고로 복잡한 분석하기"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system="""당신은 데이터 품질 분석가입니다.
문제를 분석할 때 반드시 아래 단계를 따라서 생각하세요:

1단계: 현상 파악 — 무엇이 문제인지 정리
2단계: 가능한 원인 — 왜 이런 일이 생겼는지 추론
3단계: 검증 방법 — 어떻게 확인할 수 있는지 SQL이나 방법 제시
4단계: 해결 제안 — 어떻게 고칠 수 있는지 제안
""",
        messages=[{"role": "user", "content": """
냉장고 에러 테이블(ref_error_log)에서 
어제 데이터가 평소의 10배가 들어왔습니다.
어떻게 분석해야 할까요?
"""}]
    )
    print(response.content[0].text)

# chain_of_thought_example()


# ============================================================
# 🗓️ 수요일: 출력 형식 제어 — JSON으로 받기
# ============================================================

"""
📌 왜 JSON이 중요하냐면:
   에이전트가 만든 결과를 "다음 단계"에서 쓰려면
   사람이 읽는 문장이 아니라, 코드가 읽을 수 있는 구조(JSON)로 받아야 합니다.
   이건 에이전트 체인을 만들 때 필수!
"""

def get_structured_output():
    """Claude에게 JSON 형식으로 응답받기"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system="""당신은 SQL 쿼리 생성기입니다.
사용자의 자연어 질문을 분석하여 반드시 아래 JSON 형식으로만 응답하세요.
다른 텍스트는 절대 포함하지 마세요.

{
    "intent": "질문의 의도",
    "tables": ["필요한 테이블 목록"],
    "sql": "생성된 SQL 쿼리",
    "explanation": "쿼리 설명"
}
""",
        messages=[{"role": "user", "content": "지난 달 냉장고 에러 중 가장 많이 발생한 에러 코드 5개 알려줘"}]
    )
    
    result_text = response.content[0].text
    print("📄 Raw 응답:")
    print(result_text)
    
    # JSON 파싱
    try:
        result = json.loads(result_text)
        print(f"\n✅ 파싱 성공!")
        print(f"   의도: {result['intent']}")
        print(f"   테이블: {result['tables']}")
        print(f"   SQL: {result['sql']}")
    except json.JSONDecodeError:
        print("❌ JSON 파싱 실패 — system prompt를 더 명확하게 수정해보세요")

# get_structured_output()


# ============================================================
# 🗓️ 목요일: 파라미터 실험 — temperature, max_tokens
# ============================================================

"""
📌 temperature가 뭐냐면:
   Claude의 "창의력 조절기"입니다.
   - 0.0: 매번 같은 답 (정확성 중요할 때)
   - 1.0: 매번 다른 답 (창의적 답변이 필요할 때)
   
   에이전트에서는 보통 0.0~0.3을 씁니다 (일관성이 중요하니까)
"""

def temperature_experiment(temp: float):
    """같은 질문, 다른 temperature로 3번 실행"""
    print(f"\n🌡️ Temperature = {temp}")
    print("-" * 40)
    for i in range(3):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            temperature=temp,
            messages=[{"role": "user", "content": "Python을 한 문장으로 설명해줘"}]
        )
        print(f"  시도 {i+1}: {response.content[0].text}")

# 🔥 실습: 두 값을 비교해보세요!
# temperature_experiment(0.0)  # 매번 같은 답?
# temperature_experiment(1.0)  # 매번 다른 답?


# ============================================================
# 🗓️ 금요일: 프롬프트 템플릿 라이브러리 만들기
# ============================================================

"""
🔥 이번 주 배운 것들을 재사용 가능한 템플릿으로 정리하세요!
   이 템플릿들은 앞으로 에이전트 만들 때 계속 써먹게 됩니다.
"""

PROMPT_TEMPLATES = {
    "data_analyst": {
        "system": """당신은 LG전자 IoT 데이터 분석가입니다.
데이터를 분석할 때 항상 다음 단계를 따르세요:
1. 현상 파악 2. 원인 추론 3. 검증 SQL 제시 4. 해결 제안
항상 한국어로 응답하세요.""",
        "use_case": "데이터 품질 이슈 분석, 이상치 탐지"
    },
    
    "sql_generator": {
        "system": """당신은 SQL 쿼리 생성 전문가입니다.
사용자의 자연어 질문을 Databricks SQL로 변환하세요.
반드시 JSON 형식으로만 응답하세요:
{"sql": "쿼리", "explanation": "설명"}""",
        "use_case": "자연어 → SQL 변환 에이전트"
    },
    
    "table_classifier": {
        "system": """당신은 데이터 테이블 분류 전문가입니다.
테이블 이름과 스키마를 보고 CEJ 도메인으로 분류하세요.
L1(가전제품) → L2(데이터유형) → L3(세부분류) 형식으로 출력하세요.""",
        "use_case": "1,900개 테이블 자동 분류"
    },
    
    "code_reviewer": {
        "system": """당신은 시니어 Python 개발자입니다.
코드를 리뷰할 때 다음 관점에서 분석하세요:
1. 버그 가능성 2. 성능 이슈 3. 가독성 4. 개선 제안
각 이슈는 심각도(높음/중간/낮음)와 함께 제시하세요.""",
        "use_case": "코드 리뷰 자동화"
    }
}

def use_template(template_name: str, user_message: str):
    """템플릿을 사용해서 Claude API 호출"""
    template = PROMPT_TEMPLATES[template_name]
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=template["system"],
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text

# 🔥 실습: 템플릿 사용해보기
# result = use_template("sql_generator", "이번 달 세탁기 모델별 평균 사용 횟수 알려줘")
# print(result)

"""
✅ 이번 주 체크리스트:
   □ system prompt로 에이전트 역할 부여 가능
   □ few-shot, chain-of-thought 활용 가능
   □ JSON 형식으로 구조화된 출력 받기 가능
   □ temperature 등 파라미터 이해
   □ 재사용 가능한 프롬프트 템플릿 보유
"""
