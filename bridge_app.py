import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime
from dart_api import DartAPI
from financial_analyzer import FinancialAnalyzer

class BridgeApp:
    """Bridge M&A 분석 애플리케이션 클래스"""
    
    def __init__(self):
        """Bridge 애플리케이션 초기화"""
        # 페이지 설정
        st.set_page_config(
            page_title="Bridge - 기업 정보 조회 시스템",
            page_icon="🌉",
            layout="wide"
        )
        
        # 세션 상태 초기화
        if 'api_key' not in st.session_state:
            # DartAPI 클래스를 통해 환경변수에서 API 키 로드
            st.session_state.api_key = DartAPI.get_api_key_from_env()
        
        if 'corp_code_data' not in st.session_state:
            st.session_state.corp_code_data = None
            
        # 기업 선택 상태 저장
        if 'selected_company' not in st.session_state:
            st.session_state.selected_company = None
            
        if 'company_info' not in st.session_state:
            st.session_state.company_info = None
            
        # 연도 선택을 위한 상태
        if 'selected_year' not in st.session_state:
            st.session_state.selected_year = datetime.now().year - 1
        
        # 클래스 인스턴스 초기화
        self.dart_api = None
        self.financial_analyzer = FinancialAnalyzer()

    def setup_sidebar(self):
        """사이드바 설정"""
        st.sidebar.title("Bridge POC")
        st.sidebar.markdown("""
        이 애플리케이션은 Open DART API를 활용하여 기업 정보를 조회하는 POC입니다.
        """)
        
        # API 키 상태 체크
        if not st.session_state.api_key:
            # API 키가 없을 경우에만 입력 필드 표시
            api_key = st.sidebar.text_input(
                "OPEN DART API KEY를 입력하세요", 
                type="password", 
                key="dart_api_key",
                help="API 키는 DART OpenAPI 사이트에서 발급받을 수 있습니다. .env 파일에 설정하면 자동으로 로드됩니다."
            )
            if api_key:
                st.session_state.api_key = api_key
                self.dart_api = DartAPI(api_key)
                st.sidebar.success("API 키가 설정되었습니다.")
                # 입력 필드 숨기기 위한 재실행
                st.experimental_rerun()
        else:
            # API 키가 이미 있는 경우
            st.sidebar.success("API 키가 설정되어 있습니다.")
            # API 키 재설정 옵션
            if st.sidebar.button("API 키 재설정"):
                st.session_state.api_key = ""
                st.rerun()
            
            # DartAPI 초기화
            self.dart_api = DartAPI(st.session_state.api_key)
    
    def search_companies(self, keyword):
        """키워드로 기업 검색
        
        Args:
            keyword (str): 검색 키워드
            
        Returns:
            list: 검색된 기업 목록
        """
        if self.dart_api is None:
            return []
        
        # 기업 코드 데이터가 없으면 가져오기
        if st.session_state.corp_code_data is None:
            with st.spinner("기업 목록을 가져오는 중..."):
                st.session_state.corp_code_data = self.dart_api.get_corp_codes()
        
        if st.session_state.corp_code_data is None:
            return []
        
        # 키워드로 필터링
        if keyword:
            filtered_companies = [comp for comp in st.session_state.corp_code_data if keyword.lower() in comp["corp_name"].lower()]
            return filtered_companies[:10]  # 최대 10개만 반환
        return st.session_state.corp_code_data[:10]  # 최대 10개만 반환

    def on_company_select(self, company):
        """기업 선택 시 호출될 콜백 함수"""
        st.session_state.selected_company = company
        
    def on_year_change(self, year):
        """연도 변경 시 호출될 콜백 함수"""
        st.session_state.selected_year = year

    def display_company_info(self, company_info):
        """기업 기본 정보 표시
        
        Args:
            company_info (dict): 기업 기본 정보
        """
        st.subheader("기업 기본 정보")
        
        # 기업 로고 (샘플 이미지)
        st.image(f"https://via.placeholder.com/150x150.png?text={company_info['corp_name']}", width=150)
        
        info_df = pd.DataFrame([
            {"항목": "기업명", "내용": company_info.get("corp_name", "")},
            {"항목": "영문명", "내용": company_info.get("corp_name_eng", "")},
            {"항목": "종목코드", "내용": company_info.get("stock_code", "")},
            {"항목": "대표이사", "내용": company_info.get("ceo_nm", "")},
            {"항목": "설립일", "내용": f"{company_info.get('est_dt', '')[:4]}년 {company_info.get('est_dt', '')[4:6]}월 {company_info.get('est_dt', '')[6:]}일" if company_info.get('est_dt', '') and len(company_info.get('est_dt', '')) >= 8 else "정보 없음"},
            {"항목": "주소", "내용": company_info.get("adres", "")},
            {"항목": "홈페이지", "내용": company_info.get("hm_url", "")},
            {"항목": "전화번호", "내용": company_info.get("phn_no", "")},
        ])
        
        st.dataframe(info_df, hide_index=True)
        
        # 회사 평가 점수 (샘플)
        st.subheader("M&A 적합성 평가 (샘플)")
        
        # 점수 시각화
        scores = {
            "성장성": random.randint(60, 95),
            "수익성": random.randint(60, 95),
            "안정성": random.randint(60, 95),
            "매각 가능성": random.randint(60, 95),
            "업계 경쟁력": random.randint(60, 95)
        }
        
        for metric, score in scores.items():
            st.metric(label=metric, value=f"{score}/100")
   
    def _load_financial_data(self, corp_code):
        """재무 데이터 로드하는 헬퍼 함수
        
        Args:
            corp_code (str): 기업 고유 코드
            
        Returns:
            tuple: (재무 데이터, 유효 데이터 존재 여부)
        """
        # 세션 상태에 재무 데이터가 있으면 재사용
        if 'financial_data' in st.session_state and 'last_year' in st.session_state and st.session_state.last_year == st.session_state.selected_year:
            return st.session_state.financial_data, True
            
        # 연도 설정
        current_year = datetime.now().year
        year = st.session_state.selected_year
        years = [year-2, year-1, year]
        
        # 데이터 초기화
        financial_data_list = []
        valid_years = []
        valid_financial_data_list = []
        
        # 데이터 로딩 진행 표시
        progress_bar = st.progress(0, "재무 데이터 로딩 중...")
        
        # 3개년 재무제표 데이터 가져오기
        for i, yr in enumerate(years):
            with st.spinner(f"{yr}년 재무제표 조회 중..."):
                fin_data = self.dart_api.get_financial_statements(corp_code, str(yr))
                financial_data_list.append(fin_data)
 
                # 유효한 데이터만 필터링
                if fin_data and 'list' in fin_data and len(fin_data['list']) > 0:
                    valid_financial_data_list.append(fin_data)
                    valid_years.append(yr)
                
                # 진행률 업데이트
                progress_bar.progress((i + 1) / len(years), f"{yr}년 데이터 로딩 완료")

        # 진행바 완료 후 제거
        progress_bar.empty()
        
        # 유효한 데이터가 없으면 안내 메시지 출력
        if not valid_financial_data_list:
            return None, False

        # 유효한 데이터만으로 재무 분석 진행
        financial_data = self.financial_analyzer.process_financial_data(valid_financial_data_list, valid_years)
        
        # 세션 상태에 저장
        st.session_state.financial_data = financial_data
        st.session_state.last_year = st.session_state.selected_year
        
        return financial_data, True
    
    def _year_selector(self, tab_name):
        """연도 선택 UI 표시
        
        Args:
            tab_name (str): 탭 이름 (고유 키 생성에 사용)
        
        Returns:
            bool: 연도가 변경되었는지 여부
        """
        current_year = datetime.now().year
        col1, col2 = st.columns([3, 1])
        
        with col1:
            year = st.selectbox(
                "기준 연도:", 
                list(range(current_year-5, current_year)), 
                index=list(range(current_year-5, current_year)).index(st.session_state.selected_year),
                key=f"year_select_{tab_name}"  # 고유한 키 추가
            )
        
        with col2:
            if st.button("조회", use_container_width=True, key=f"load_btn_{tab_name}"):  # 고유한 키 추가
                self.on_year_change(year)
                # 재무 데이터 초기화 (새로운 연도 선택 시)
                if 'financial_data' in st.session_state:
                    del st.session_state.financial_data
                    
                return True
        
        return False
    
    def display_financial_statements(self, corp_code):
        """재무제표 정보 표시
        
        Args:
            corp_code (str): 기업 고유 코드
        """
        st.subheader("재무상태표 및 손익계산서")
        
        # 연도 선택기 표시 (고유 키 전달)
        year_changed = self._year_selector("financial_statements")
        
        # 데이터 로드
        financial_data, success = self._load_financial_data(corp_code)
        if not success:
            st.error("조회 가능한 재무 데이터가 없습니다.")
            return
            
        # 자산/부채/자본 그래프
        st.subheader("재무상태표")
        balance_df = pd.DataFrame({
            "연도": [str(y) for y in financial_data["years"]],
            "자산": financial_data["assets"],
            "부채": financial_data["liabilities"],
            "자본": financial_data["equity"]
        })
        
        # 표 형태로 데이터 표시
        st.dataframe(balance_df, hide_index=True, use_container_width=True)
        
        # 그래프 표시
        fig1 = px.bar(
            balance_df, 
            x="연도", 
            y=["자산", "부채", "자본"],
            barmode="group",
            title="자산/부채/자본 추이",
            labels={"value": "금액 (백만원)", "variable": "항목"}
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # 매출/이익 그래프
        st.subheader("손익계산서")
        income_df = pd.DataFrame({
            "연도": [str(y) for y in financial_data["years"]],
            "매출액": financial_data["revenue"],
            "영업이익": financial_data["operating_profit"],
            "당기순이익": financial_data["net_income"]
        })
        
        # 표 형태로 데이터 표시
        st.dataframe(income_df, hide_index=True, use_container_width=True)
        
        # 그래프 표시
        fig2 = px.line(
            income_df, 
            x="연도", 
            y=["매출액", "영업이익", "당기순이익"],
            title="매출 및 이익 추이",
            labels={"value": "금액 (백만원)", "variable": "항목"},
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    def display_financial_ratios(self, corp_code):
        """재무 비율 정보 표시
        
        Args:
            corp_code (str): 기업 고유 코드
        """
        st.subheader("재무 비율 분석")
        
        # 연도 선택기 표시 (고유 키 전달)
        year_changed = self._year_selector("financial_ratios")
        
        # 데이터 로드
        financial_data, success = self._load_financial_data(corp_code)
        if not success:
            st.error("조회 가능한 재무 데이터가 없습니다.")
            return
        
        # 재무 비율 계산 및 표시
        ratios = self.financial_analyzer.calculate_financial_ratios(financial_data)
        ratio_df = pd.DataFrame(ratios)
        
        # 표 형태로 데이터 표시
        st.dataframe(ratio_df, hide_index=True, use_container_width=True)
        
        # 주요 비율 그래프로 표시
        # 1. 수익성 비율 (영업이익률, 순이익률)
        profit_ratios = pd.DataFrame({
            "연도": ratio_df["연도"],
            "영업이익률": [float(r.strip('%')) if r != '-' else 0 for r in ratio_df["영업이익률"]],
            "순이익률": [float(r.strip('%')) if r != '-' else 0 for r in ratio_df["순이익률"]]
        })
        
        fig1 = px.line(
            profit_ratios,
            x="연도",
            y=["영업이익률", "순이익률"],
            title="수익성 비율 추이",
            labels={"value": "비율 (%)", "variable": "항목"},
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # 2. 성장성 비율 (매출 성장률)
        growth_ratios = pd.DataFrame({
            "연도": ratio_df["연도"],
            "매출 성장률": [float(r.strip('%')) if r != '-' else 0 for r in ratio_df["매출 성장률"]]
        })
        
        fig2 = px.bar(
            growth_ratios,
            x="연도",
            y="매출 성장률",
            title="매출 성장률 추이",
            labels={"매출 성장률": "성장률 (%)"},
            color="매출 성장률",
            color_continuous_scale=["red", "yellow", "green"]
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # 3. 안정성 및 효율성 비율 (부채비율, ROE)
        stability_ratios = pd.DataFrame({
            "연도": ratio_df["연도"],
            "부채비율": [float(r.strip('%')) if r != '-' else 0 for r in ratio_df["부채비율"]],
            "ROE": [float(r.strip('%')) if r != '-' else 0 for r in ratio_df["ROE"]]
        })
        
        fig3 = px.bar(
            stability_ratios,
            x="연도",
            y=["부채비율", "ROE"],
            barmode="group",
            title="부채비율 및 ROE 추이",
            labels={"value": "비율 (%)", "variable": "항목"}
        )
        st.plotly_chart(fig3, use_container_width=True)
        
    def display_valuation(self, corp_code):
        """기업 가치 평가 정보 표시
        
        Args:
            corp_code (str): 기업 고유 코드
        """
        st.subheader("기업 가치 평가")
        
        # 연도 선택기 표시 (고유 키 전달)
        year_changed = self._year_selector("valuation")
        
        # 데이터 로드
        financial_data, success = self._load_financial_data(corp_code)
        if not success:
            st.error("조회 가능한 재무 데이터가 없습니다.")
            return
        
        # 가치 평가 결과
        valuation_results = self.financial_analyzer.calculate_valuation(financial_data)
        
        # 값 추출
        min_value, max_value = valuation_results["range"]
        if min_value > 0 or max_value > 0:
            # 가치 평가 범위를 시각적으로 표현
            st.subheader("기업 가치 범위")
            st.metric(
                label="추정 가치 범위 (백만원)", 
                value=f"{(min_value + max_value) / 2:,.0f}", 
                delta=f"{max_value - min_value:,.0f} 범위"
            )
            
            # 게이지 차트로 표현
            avg_value = (min_value + max_value) / 2
            
            # 상세 평가 결과 테이블
            st.subheader("평가 방법별 가치")
            valuation_df = pd.DataFrame(valuation_results["valuations"])
            st.dataframe(valuation_df, hide_index=True, use_container_width=True)
            
            # 평가 방법별 차트
            try:
                # 숫자 형식으로 변환
                values = []
                methods = []
                for val in valuation_results["valuations"]:
                    if val["추정 가치 (백만원)"] != "N/A":
                        values.append(float(val["추정 가치 (백만원)"].replace(",", "")))
                        methods.append(val["평가 방법"])
                
                if values:
                    valuation_chart_df = pd.DataFrame({
                        "평가 방법": methods,
                        "추정 가치 (백만원)": values
                    })
                    
                    fig = px.bar(
                        valuation_chart_df,
                        x="평가 방법",
                        y="추정 가치 (백만원)",
                        title="평가 방법별 기업 가치",
                        color="평가 방법"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"차트 생성 중 오류 발생: {e}")
            
            # 추가 설명
            st.info("""
            **참고 사항:**
            - PER 기준 가치: 당기순이익 × 업종 평균 PER(15배)
            - EBITDA Multiple 기준 가치: 영업이익의 120% × 업종 평균 EBITDA Multiple(8배)
            - 순자산 가치: 총자본
            
            이 평가는 간단한 예시이며, 실제 M&A 가치 평가는 더 복잡한 요소들을 고려해야 합니다.
            """)
        else:
            st.warning("가치 평가에 필요한 재무 데이터가 충분하지 않습니다.")
    
    def run(self):
        """애플리케이션 실행"""
        # 사이드바 설정
        self.setup_sidebar()

        # 메인 타이틀
        st.title("Bridge - 기업 정보 조회 시스템 POC")

        # API 키 확인
        if not st.session_state.api_key:
            st.warning("사이드바에 Open DART API 키를 입력해주세요.")
            return

        # API 연결
        self.dart_api = DartAPI(st.session_state.api_key)
        
        # 기업 검색 섹션
        with st.expander("기업 검색", expanded=not st.session_state.selected_company):
            search_keyword = st.text_input("기업명을 입력하세요:")
            companies = self.search_companies(search_keyword)

            if companies:
                company_names = [f"{comp['corp_name']} ({comp['stock_code']})" for comp in companies]
                selected_company_idx = st.selectbox("기업을 선택하세요:", range(len(company_names)), format_func=lambda x: company_names[x])

                if st.button("기업 정보 조회"):
                    selected_company = companies[selected_company_idx]
                    self.on_company_select(selected_company)

                    # 기업 정보 로딩
                    with st.spinner("기업 정보를 조회 중입니다..."):
                        company_info = self.dart_api.get_company_info(selected_company["corp_code"])
                        if company_info:
                            st.session_state.company_info = company_info
            else:
                if search_keyword:
                    st.info("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")
                else:
                    st.info("기업명을 입력하여 검색하세요.")

        # 선택된 기업 정보 표시
        if st.session_state.selected_company and st.session_state.company_info:
            # 선택된 기업 정보 헤더 표시
            st.markdown(f"## 선택된 기업: {st.session_state.company_info.get('corp_name', '알 수 없음')} ({st.session_state.selected_company.get('stock_code', '')})")

            # 탭 생성
            tabs = st.tabs(["기업 개요", "재무 현황", "재무 비율", "가치 평가"])
            
            # 탭 1: 기업 개요
            with tabs[0]:
                self.display_company_info(st.session_state.company_info)
                
            # 탭 2: 재무 현황
            with tabs[1]:
                self.display_financial_statements(st.session_state.selected_company["corp_code"])
                
            # 탭 3: 재무 비율
            with tabs[2]:
                self.display_financial_ratios(st.session_state.selected_company["corp_code"])
                
            # 탭 4: 가치 평가
            with tabs[3]:
                self.display_valuation(st.session_state.selected_company["corp_code"])