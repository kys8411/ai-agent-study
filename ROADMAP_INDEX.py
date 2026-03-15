"""
============================================================
🗺️ AI 에이전트 10주 학습 로드맵 — 전체 인덱스
============================================================
작성일: 2026-03-08
학습자: YongSeok (김용석)
목표: AI 에이전트 개발 역량 확보 → 실무 적용

⏰ 학습 루틴:
   5:15  기상 → 씻기 + 스트레칭
   5:30  딥워크 — 코드 치기 (60분)
   6:30  전환 — git commit + 이어하기 메모
   6:40  이동 — 영상/docs 학습 (70분)
   7:50  도착 — 마무리/복습 (40분)
   9:45  취침 준비 알람
============================================================

📁 파일 목록 (학습 순서대로):

──────────────────────────────────────────────
Phase 1: 기반 도구 숙달 (1~2주차)
──────────────────────────────────────────────
📄 phase1_week1_git_basics.py
   → Git init/add/commit, branch/merge, conflict, GitHub
   
📄 phase1_week2_claude_code.py
   → Claude Code 설치, 쓰레드 관리, CLAUDE.md, 실무 활용


──────────────────────────────────────────────
Phase 2: LLM API + Tool Use (3~4주차)
──────────────────────────────────────────────
📄 step1_basic_api_call.py          ← 내일 아침 시작!
   → API 키 세팅 + 첫 호출

📄 step2_tool_use_agent.py          ← 내일 아침 메인!
   → Tool Use 핵심 구현 (날씨 에이전트)

📄 step3_data_agent_preview.py      ← 내일 보너스
   → 자연어→SQL 에이전트 미리보기

📄 phase2_week3_prompt_engineering.py
   → system prompt, few-shot, CoT, JSON 출력, temperature

📄 phase2_week4_advanced_tool_use.py
   → 멀티도구, 멀티턴, 에러핸들링, 스트리밍, 개인비서 에이전트


──────────────────────────────────────────────
Phase 3: 에이전트 아키텍처 (5~6주차)
──────────────────────────────────────────────
📄 phase3_week5_react_nl2sql.py
   → ReAct 패턴, 자연어→SQL 에이전트, SQL 자동수정

📄 phase3_week6_mcp_rag.py
   → MCP 서버 구축, RAG 벡터검색, 1900개 테이블 연결


──────────────────────────────────────────────
Phase 4: 서브에이전트 & 멀티에이전트 (7~8주차)
──────────────────────────────────────────────
📄 phase4_week7_sub_agents.py
   → 오케스트레이터, 전문가 에이전트, 동적 라우팅

📄 phase4_week8_multi_agent.py
   → 독립 쓰레드, 병렬실행, LangGraph, IoT 멀티에이전트


──────────────────────────────────────────────
Phase 5: 실무 프로젝트 MVP (9~10주차)
──────────────────────────────────────────────
📄 phase5_week9_10_mvp_project.py
   → 프로젝트 옵션 3가지 + 일일 체크리스트 + 최종 목표


──────────────────────────────────────────────
가이드
──────────────────────────────────────────────
📄 README_내일아침가이드.py
   → 내일 아침 60분 타임라인 (step1→2→3 순서)


============================================================
📌 학습 원칙:
   1. 아침엔 손 (코드 작성)
   2. 이동엔 눈 (영상/docs 학습)  
   3. 도착 후엔 마무리 (복습/커밋)
   4. 한 주에 한 가지만 집중
   5. 매일 Git 커밋 (잔디 심기)
============================================================

📌 추천 학습 리소스:
   - Anthropic 공식 Docs: https://docs.anthropic.com
   - Tool Use 가이드: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
   - MCP 공식 사이트: https://modelcontextprotocol.io
   - LangGraph Docs: https://langchain-ai.github.io/langgraph/
   - DeepLearning.AI: https://www.deeplearning.ai (무료 강의)
   - ChromaDB Docs: https://docs.trychroma.com
   
============================================================
"""
