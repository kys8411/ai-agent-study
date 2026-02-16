import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import re
from io import BytesIO

class TeamsPasteCollector:
    """팀즈 메시지 복사-붙여넣기로 수집"""
    
    def __init__(self, csv_path='governance_inquiries.csv'):
        self.csv_path = csv_path
    
    @staticmethod
    def load_data(csv_path='governance_inquiries.csv'):
        """데이터 로드"""
        try:
            return pd.read_csv(csv_path, encoding='utf-8-sig')
        except FileNotFoundError:
            return pd.DataFrame(columns=[
                '수집일시', '발신자', '이메일', '내용', '카테고리', '키워드'
            ])
    
    @staticmethod
    def parse_teams_message(text):
        """팀즈 메시지 파싱 (단건)"""
        lines = text.strip().split('\n')

        if len(lines) < 1:
            return None

        # 첫 줄: 발신자 이름
        sender_name = lines[0].strip()

        # 시간 패턴 찾기 (오전/오후 10:30 형식)
        time_pattern = r'(오전|오후)\s*\d{1,2}:\d{2}'

        # 내용 추출
        content_lines = []
        for line in lines[1:]:
            # 시간 라인은 건너뛰기
            if re.search(time_pattern, line):
                continue
            if line.strip():
                content_lines.append(line.strip())

        content = ' '.join(content_lines).strip()

        if not content:
            return None

        return {
            'sender_name': sender_name,
            'content': content
        }

    @staticmethod
    def parse_teams_messages_batch(text):
        """팀즈 메시지 일괄 파싱 (여러 메시지를 한번에 처리)

        Teams에서 여러 메시지를 복사하면 다음과 같은 형식:
        홍길동
        오전 10:30
        테이블 접근 권한 신청합니다

        김철수
        오후 2:15
        메타데이터 업데이트 요청드립니다
        """
        time_pattern = r'^(오전|오후)\s*\d{1,2}:\d{2}$'
        lines = text.strip().split('\n')

        messages = []
        current_sender = None
        current_content_lines = []

        for line in lines:
            stripped = line.strip()

            # 빈 줄은 건너뛰기
            if not stripped:
                continue

            # 시간 패턴이면 건너뛰기 (발신자 바로 다음에 오는 시간)
            if re.match(time_pattern, stripped):
                continue

            # 새 발신자 감지: 다음 줄이 시간 패턴인지 확인
            line_idx = lines.index(line)
            next_non_empty = None
            for next_line in lines[line_idx + 1:]:
                if next_line.strip():
                    next_non_empty = next_line.strip()
                    break

            is_new_sender = (
                next_non_empty is not None
                and re.match(time_pattern, next_non_empty)
                and len(stripped) < 30  # 이름은 보통 짧음
                and not any(kw in stripped for kw in ['테이블', '권한', '접근', '메타데이터', '신청', '요청', '문의'])
            )

            if is_new_sender:
                # 이전 메시지 저장
                if current_sender and current_content_lines:
                    content = ' '.join(current_content_lines).strip()
                    if content:
                        messages.append({
                            'sender_name': current_sender,
                            'content': content
                        })
                # 새 발신자 시작
                current_sender = stripped
                current_content_lines = []
            else:
                # 내용 라인
                if current_sender is None:
                    # 첫 줄이 발신자인 경우 (시간 패턴이 뒤에 없는 경우)
                    current_sender = stripped
                else:
                    current_content_lines.append(stripped)

        # 마지막 메시지 저장
        if current_sender and current_content_lines:
            content = ' '.join(current_content_lines).strip()
            if content:
                messages.append({
                    'sender_name': current_sender,
                    'content': content
                })

        # 메시지가 하나도 파싱되지 않으면 단건 파싱으로 폴백
        if not messages:
            single = TeamsPasteCollector.parse_teams_message(text)
            if single:
                messages = [single]

        return messages
    
    @staticmethod
    def categorize(content):
        """카테고리 분류"""
        content_lower = content.lower()
        if any(kw in content_lower for kw in ['권한', '접근', '승인']):
            return '권한관리'
        elif any(kw in content_lower for kw in ['메타데이터', '컬럼', '설명']):
            return '메타데이터'
        elif any(kw in content_lower for kw in ['개인정보', '분류', '민감']):
            return '데이터분류'
        elif any(kw in content_lower for kw in ['테이블', '스키마']):
            return '테이블관리'
        else:
            return '기타'
    
    @staticmethod
    def extract_keywords(content):
        """키워드 추출"""
        keywords = ['권한', '접근', '테이블', '메타데이터', '승인', '스키마', '개인정보']
        found = [kw for kw in keywords if kw in content]
        return ', '.join(found)
    
    @staticmethod
    def add_inquiry(df, sender_name, sender_email, content):
        """문의 추가"""
        record = {
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '발신자': sender_name,
            '이메일': sender_email,
            '내용': content,
            '카테고리': TeamsPasteCollector.categorize(content),
            '키워드': TeamsPasteCollector.extract_keywords(content)
        }
        
        new_df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        return new_df, record


# Streamlit 페이지 설정
st.set_page_config(
    page_title="거버넌스 문의 수집기",
    page_icon="📋",
    layout="wide"
)

# 세션 상태 초기화
if 'df' not in st.session_state:
    st.session_state.df = TeamsPasteCollector.load_data()

# 타이틀
st.title("📋 거버넌스 문의 수집기")
st.markdown("---")

# 사이드바 - 통계
with st.sidebar:
    st.header("📊 수집 통계")
    
    total_count = len(st.session_state.df)
    st.metric("전체 문의", f"{total_count}건")
    
    if total_count > 0:
        st.subheader("카테고리별 분포")
        category_counts = st.session_state.df['카테고리'].value_counts()
        for category, count in category_counts.items():
            st.write(f"**{category}**: {count}건")
        
        st.markdown("---")
        
        st.subheader("주요 문의자 (Top 5)")
        sender_counts = st.session_state.df['발신자'].value_counts().head(5)
        for sender, count in sender_counts.items():
            st.write(f"**{sender}**: {count}건")

# 메인 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 새 문의 추가")
    
    # 탭으로 입력 방식 구분
    tab1, tab2, tab3 = st.tabs(["📋 팀즈 붙여넣기 (단건)", "📦 팀즈 일괄 붙여넣기", "✍️ 직접 입력"])

    with tab1:
        st.info("💡 팀즈에서 메시지를 복사(Ctrl+C)한 후, 아래 **클립보드에서 가져오기** 버튼을 클릭하세요.")

        # 클립보드 자동 읽기 버튼 (단건)
        components.html("""
        <button id="clipBtn" onclick="readClipboard()" style="
            background-color:#FF4B4B; color:white; border:none; padding:8px 20px;
            border-radius:8px; cursor:pointer; font-size:14px; font-weight:600;
        ">📋 클립보드에서 가져오기</button>
        <span id="clipStatus" style="margin-left:10px; font-size:13px; color:#888;"></span>
        <script>
        async function readClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                if (!text) { document.getElementById('clipStatus').textContent = '⚠️ 클립보드가 비어있습니다'; return; }
                const doc = window.parent.document;
                const ta = doc.querySelector('textarea[aria-label="팀즈 메시지 붙여넣기"]');
                if (ta) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                    setter.call(ta, text);
                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                    ta.dispatchEvent(new Event('change', { bubbles: true }));
                    document.getElementById('clipStatus').textContent = '✅ 붙여넣기 완료! 아래 자동 추가 버튼을 클릭하세요.';
                }
            } catch(e) {
                document.getElementById('clipStatus').innerHTML = '❌ 클립보드 접근이 차단됨. <b>주소창 왼쪽 자물쇠 → 클립보드 허용</b> 후 다시 시도하세요.';
            }
        }
        </script>
        """, height=45)

        pasted_text = st.text_area(
            "팀즈 메시지 붙여넣기",
            height=150,
            placeholder="""예시:
홍길동
오전 10:30
ic360_customer_master 테이블 접근 권한 신청합니다""",
            key="single_paste"
        )

        if st.button("🚀 자동 추가", type="primary", key="paste_add"):
            if pasted_text.strip():
                parsed = TeamsPasteCollector.parse_teams_message(pasted_text)

                if parsed:
                    email = f"{parsed['sender_name']}@lg.com"

                    st.session_state.df, record = TeamsPasteCollector.add_inquiry(
                        st.session_state.df,
                        parsed['sender_name'],
                        email,
                        parsed['content']
                    )

                    st.session_state.df.to_csv('governance_inquiries.csv',
                                               index=False,
                                               encoding='utf-8-sig')

                    st.success(f"✅ 추가 완료: [{record['카테고리']}] {record['발신자']}")
                    st.info(f"내용: {record['내용'][:100]}...")
                    st.rerun()
                else:
                    st.error("❌ 메시지 형식을 인식할 수 없습니다")
            else:
                st.warning("⚠️ 내용을 입력해주세요")

    with tab2:
        st.info("💡 팀즈에서 **여러 메시지를 한꺼번에** 복사(Ctrl+C)한 후, 아래 **클립보드에서 가져오기** 버튼을 클릭하세요.")

        # 클립보드 자동 읽기 버튼 (일괄)
        components.html("""
        <button id="clipBtnBatch" onclick="readClipboardBatch()" style="
            background-color:#FF4B4B; color:white; border:none; padding:8px 20px;
            border-radius:8px; cursor:pointer; font-size:14px; font-weight:600;
        ">📋 클립보드에서 가져오기</button>
        <span id="clipStatusBatch" style="margin-left:10px; font-size:13px; color:#888;"></span>
        <script>
        async function readClipboardBatch() {
            try {
                const text = await navigator.clipboard.readText();
                if (!text) { document.getElementById('clipStatusBatch').textContent = '⚠️ 클립보드가 비어있습니다'; return; }
                const doc = window.parent.document;
                const ta = doc.querySelector('textarea[aria-label="팀즈 메시지 일괄 붙여넣기"]');
                if (ta) {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                    setter.call(ta, text);
                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                    ta.dispatchEvent(new Event('change', { bubbles: true }));
                    document.getElementById('clipStatusBatch').textContent = '✅ 붙여넣기 완료! 아래 일괄 추가 버튼을 클릭하세요.';
                }
            } catch(e) {
                document.getElementById('clipStatusBatch').innerHTML = '❌ 클립보드 접근이 차단됨. <b>주소창 왼쪽 자물쇠 → 클립보드 허용</b> 후 다시 시도하세요.';
            }
        }
        </script>
        """, height=45)

        batch_text = st.text_area(
            "팀즈 메시지 일괄 붙여넣기",
            height=250,
            placeholder="""예시 (여러 메시지를 한번에 붙여넣기):
홍길동
오전 10:30
ic360_customer_master 테이블 접근 권한 신청합니다

김철수
오후 2:15
메타데이터 업데이트 요청드립니다

이영희
오전 9:00
개인정보 분류 관련 문의입니다""",
            key="batch_paste"
        )

        if st.button("🚀 일괄 추가", type="primary", key="batch_add"):
            if batch_text.strip():
                parsed_list = TeamsPasteCollector.parse_teams_messages_batch(batch_text)

                if parsed_list:
                    added_records = []
                    for parsed in parsed_list:
                        email = f"{parsed['sender_name']}@lg.com"
                        st.session_state.df, record = TeamsPasteCollector.add_inquiry(
                            st.session_state.df,
                            parsed['sender_name'],
                            email,
                            parsed['content']
                        )
                        added_records.append(record)

                    st.session_state.df.to_csv('governance_inquiries.csv',
                                               index=False,
                                               encoding='utf-8-sig')

                    st.success(f"✅ 총 {len(added_records)}건 일괄 추가 완료!")
                    for rec in added_records:
                        st.write(f"  - **[{rec['카테고리']}]** {rec['발신자']}: {rec['내용'][:50]}...")
                    st.rerun()
                else:
                    st.error("❌ 메시지 형식을 인식할 수 없습니다")
            else:
                st.warning("⚠️ 내용을 입력해주세요")
    
    with tab3:
        st.info("💡 직접 정보를 입력하세요")
        
        with st.form("manual_form"):
            sender = st.text_input("발신자 이름", placeholder="홍길동")
            email = st.text_input("이메일", placeholder="hong@lg.com")
            content = st.text_area("문의 내용", height=100, 
                                   placeholder="테이블 접근 권한 신청합니다...")
            
            submitted = st.form_submit_button("➕ 추가", type="primary")
            
            if submitted:
                if sender and content:
                    # 이메일 자동 생성 (입력 안 했을 경우)
                    if not email:
                        email = f"{sender}@lg.com"
                    
                    # 문의 추가
                    st.session_state.df, record = TeamsPasteCollector.add_inquiry(
                        st.session_state.df,
                        sender,
                        email,
                        content
                    )
                    
                    # CSV 저장
                    st.session_state.df.to_csv('governance_inquiries.csv', 
                                               index=False, 
                                               encoding='utf-8-sig')
                    
                    st.success(f"✅ 추가 완료: [{record['카테고리']}] {record['발신자']}")
                    st.rerun()
                else:
                    st.error("❌ 발신자와 내용은 필수입니다")

with col2:
    st.header("💾 데이터 다운로드")
    
    if total_count > 0:
        # Excel 다운로드
        def convert_to_excel(df):
            """DataFrame을 Excel 파일로 변환"""
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='거버넌스문의')
                
                # 워크시트 가져오기
                worksheet = writer.sheets['거버넌스문의']
                
                # 열 너비 자동 조정
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return output.getvalue()
        
        excel_data = convert_to_excel(st.session_state.df)
        
        st.download_button(
            label="📥 Excel 다운로드",
            data=excel_data,
            file_name=f"거버넌스문의_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
        # CSV 다운로드
        csv_data = st.session_state.df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="📄 CSV 다운로드",
            data=csv_data,
            file_name=f"거버넌스문의_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        
        # 데이터 초기화
        if st.button("🗑️ 전체 데이터 삭제", type="secondary"):
            if st.checkbox("정말 삭제하시겠습니까?"):
                st.session_state.df = pd.DataFrame(columns=[
                    '수집일시', '발신자', '이메일', '내용', '카테고리', '키워드'
                ])
                st.session_state.df.to_csv('governance_inquiries.csv', 
                                           index=False, 
                                           encoding='utf-8-sig')
                st.success("✅ 데이터가 초기화되었습니다")
                st.rerun()
    else:
        st.info("📭 아직 수집된 문의가 없습니다")

# 수집된 데이터 테이블
st.markdown("---")
st.header("📊 수집된 문의 목록")

if total_count > 0:
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_filter = st.multiselect(
            "카테고리 필터",
            options=st.session_state.df['카테고리'].unique(),
            default=st.session_state.df['카테고리'].unique()
        )
    
    with col2:
        sender_filter = st.multiselect(
            "발신자 필터",
            options=st.session_state.df['발신자'].unique(),
            default=st.session_state.df['발신자'].unique()
        )
    
    with col3:
        search_keyword = st.text_input("내용 검색", placeholder="키워드 입력...")
    
    # 필터 적용
    filtered_df = st.session_state.df[
        (st.session_state.df['카테고리'].isin(category_filter)) &
        (st.session_state.df['발신자'].isin(sender_filter))
    ]
    
    if search_keyword:
        filtered_df = filtered_df[
            filtered_df['내용'].str.contains(search_keyword, case=False, na=False)
        ]
    
    # 테이블 표시
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400,
        column_config={
            "수집일시": st.column_config.DatetimeColumn(
                "수집일시",
                format="YYYY-MM-DD HH:mm:ss"
            ),
            "카테고리": st.column_config.TextColumn(
                "카테고리",
                width="small"
            ),
            "내용": st.column_config.TextColumn(
                "내용",
                width="large"
            )
        }
    )
    
    st.caption(f"총 {len(filtered_df)}건 표시 중")
else:
    st.info("📭 수집된 문의가 없습니다. 위에서 문의를 추가해보세요!")

# 푸터
st.markdown("---")
st.caption("🏢 LG Electronics IC360 Data Operations Team | Governance Inquiry Collector v1.0")