"""
============================================================
📘 Phase 1 | Week 1: Git 기초 완전정복
============================================================
🎯 이번 주 목표: Git의 핵심 명령어를 손에 익히기
   - 월: init, add, commit
   - 화: branch, checkout, merge
   - 수: conflict 해결 + .gitignore
   - 목: remote, push, pull (GitHub 연결)
   - 금: 전체 복습 + 나만의 워크플로우 정리

📌 사전 준비:
   - Git 설치: https://git-scm.com/downloads
   - 터미널(Windows: Git Bash / Mac: Terminal) 열기
   - GitHub 계정 만들기: https://github.com
============================================================
"""

# ============================================================
# 🗓️ 월요일: Git의 기본 — init, add, commit
# ============================================================

"""
📌 Git이 뭐냐면:
   코드의 "타임머신"이라고 생각하세요.
   파일을 수정할 때마다 "스냅샷"을 저장해두면,
   언제든 과거로 돌아갈 수 있습니다.
   
   Word 문서에서 Ctrl+Z를 100번 할 수 있는 것과 비슷한데,
   더 체계적이고, 여러 사람이 동시에 작업할 수 있습니다.

💻 터미널에서 따라해보세요:
"""

# --- 1. 프로젝트 폴더 만들기 ---
# mkdir ai-agent-study
# cd ai-agent-study

# --- 2. Git 저장소 초기화 ---
# git init
# → ".git" 폴더가 생김 = 이 폴더가 이제 Git으로 관리됨

# --- 3. 첫 번째 파일 만들기 ---
# echo "# AI Agent Study" > README.md

# --- 4. 파일을 Git에 등록 (staging) ---
# git add README.md
# → "이 파일을 다음 스냅샷에 포함시켜줘"라는 뜻

# --- 5. 스냅샷 저장 (commit) ---
# git commit -m "첫 커밋: README 추가"
# → -m 뒤에 "이번에 뭘 했는지" 메모를 남김

# --- 6. 상태 확인 ---
# git status    ← 현재 어떤 파일이 변경/추가됐는지 확인
# git log       ← 지금까지의 커밋 히스토리 확인

"""
🔥 실습 과제:
   1. hello.py 파일을 만들어서 print("Hello Git!") 작성
   2. git add → git commit 으로 저장
   3. hello.py를 수정해서 print("Hello AI Agent!") 로 변경
   4. 다시 git add → git commit
   5. git log로 커밋 2개가 보이는지 확인
"""


# ============================================================
# 🗓️ 화요일: Branch — 평행우주 만들기
# ============================================================

"""
📌 Branch가 뭐냐면:
   "평행우주"를 만드는 겁니다.
   main(메인)은 안전한 원본이고,
   새 기능을 만들 때는 별도의 branch에서 작업합니다.
   잘 되면 main에 합치고(merge), 망하면 그냥 버리면 됩니다.

💻 따라해보세요:
"""

# --- 1. 새 branch 만들기 ---
# git branch feature/add-greeting
# → "feature/add-greeting"이라는 평행우주 생성

# --- 2. 그 branch로 이동 ---
# git checkout feature/add-greeting
# → 이제 이 평행우주에서 작업 중

# (또는 한 번에: git checkout -b feature/add-greeting)

# --- 3. 이 branch에서 파일 수정 ---
# → hello.py에 새 함수 추가하고 commit

# --- 4. 다시 main으로 돌아가기 ---
# git checkout main
# → hello.py를 보면? 아까 수정한 게 없음! (평행우주니까)

# --- 5. branch를 main에 합치기 (merge) ---
# git merge feature/add-greeting
# → 평행우주의 변경사항이 main에 반영됨!

"""
🔥 실습 과제:
   1. feature/calculator 브랜치를 만들기
   2. calculator.py 파일을 만들어서 간단한 더하기 함수 작성
   3. commit 하고 main에 merge하기
   4. git log --oneline --graph 로 브랜치 히스토리 확인
"""


# ============================================================
# 🗓️ 수요일: Conflict 해결 — 충돌은 무섭지 않다
# ============================================================

"""
📌 Conflict(충돌)이 뭐냐면:
   두 branch에서 같은 파일의 같은 줄을 다르게 수정하면,
   Git이 "어떤 걸 살릴지 모르겠어!"라고 알려주는 겁니다.
   무서워할 필요 없이, 직접 골라주면 됩니다.

💻 일부러 충돌을 만들어봅시다:
"""

# --- 1. main에서 hello.py 1번째 줄 수정 후 commit ---
# (main에서) hello.py → print("Hello from MAIN")
# git add . && git commit -m "main에서 수정"

# --- 2. 새 branch에서 같은 줄 수정 후 commit ---
# git checkout -b feature/conflict-test
# hello.py → print("Hello from FEATURE")
# git add . && git commit -m "feature에서 수정"

# --- 3. main에서 merge 시도 ---
# git checkout main
# git merge feature/conflict-test
# → ❌ CONFLICT! 충돌 발생!

# --- 4. 파일을 열면 이렇게 보임 ---
# <<<<<<< HEAD
# print("Hello from MAIN")
# =======
# print("Hello from FEATURE")
# >>>>>>> feature/conflict-test

# --- 5. 원하는 걸 골라서 수정하고 저장 ---
# print("Hello from MAIN and FEATURE")  ← 둘 다 살릴 수도 있음

# --- 6. 충돌 해결 완료 ---
# git add hello.py
# git commit -m "충돌 해결: main과 feature 합침"

"""
💡 .gitignore 파일도 만들어두세요:
   → .env, __pycache__/, .DS_Store 등 Git에 올리면 안 되는 것들
"""

# .gitignore 예시 내용:
GITIGNORE_CONTENT = """
# Python
__pycache__/
*.pyc
.env
venv/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# API Keys (절대 올리면 안 됨!)
.env
*.key
"""


# ============================================================
# 🗓️ 목요일: GitHub 연결 — 세상에 코드 공개하기
# ============================================================

"""
📌 GitHub가 뭐냐면:
   Git이 "로컬 타임머신"이라면,
   GitHub는 "클라우드 타임머신"입니다.
   코드를 온라인에 백업하고, 다른 사람과 공유할 수 있습니다.

💻 따라해보세요:
"""

# --- 1. GitHub에서 새 Repository 만들기 ---
# → github.com → New Repository → "ai-agent-study" → Create

# --- 2. 로컬 Git에 GitHub 주소 연결 ---
# git remote add origin https://github.com/YOUR_USERNAME/ai-agent-study.git

# --- 3. 코드 올리기 (push) ---
# git push -u origin main
# → GitHub 사이트에서 코드가 보이면 성공!

# --- 4. 코드 내려받기 (pull) ---
# git pull origin main
# → 다른 PC에서 작업한 걸 가져올 때 사용

"""
🔥 실습 과제:
   1. GitHub에 ai-agent-study 저장소 만들기
   2. 지금까지 만든 파일들 전부 push
   3. GitHub 웹사이트에서 커밋 히스토리 확인
   4. README.md를 GitHub 웹에서 직접 수정 → pull로 받아보기
"""


# ============================================================
# 🗓️ 금요일: 복습 + 나만의 Git 워크플로우 정리
# ============================================================

"""
✅ 이번 주 체크리스트:
   □ git init / add / commit 자유자재로 사용 가능
   □ branch 만들고 merge 할 수 있음
   □ conflict 발생해도 당황하지 않고 해결 가능
   □ GitHub에 push / pull 가능
   □ .gitignore 설정 완료

📝 나만의 Git 커밋 메시지 규칙 정해두기 (추천):
   feat: 새 기능 추가
   fix: 버그 수정
   docs: 문서 수정
   refactor: 코드 구조 변경
   
   예시: git commit -m "feat: Tool Use 에이전트 기본 구조 구현"
"""
