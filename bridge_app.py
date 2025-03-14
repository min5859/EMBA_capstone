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
            st.session_state.api_key = ""
        
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
        
        # API 키 입력 처리
        api_key = st.sidebar.text_input("OPEN DART API KEY를 입력하세요", type="password", key="dart_api_key")
        if api_key:
            st.session_state.api_key = api_key
            self.dart_api = DartAPI(api_key)
        
        # API 키 상태 표시
        if st.session_state.api_key:
            st.sidebar.success("API 키가 입력되었습니다.")
        else:
            st.sidebar.warning("API 키를 입력해주세요.")
    
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
   
    def display_financial_info(self, corp_code):
        """재무 정보 표시
        
        Args:
            corp_code (str): 기업 고유 코드
        """
        st.subheader("재무 정보")
        
        # 연도 선택 - 세션 상태 사용
        current_year = datetime.now().year
        year = st.selectbox(
            "기준 연도:", 
            list(range(current_year-5, current_year)), 
            index=list(range(current_year-5, current_year)).index(st.session_state.selected_year),
            on_change=self.on_year_change,
            args=(st.session_state.selected_year,)
        )
        
        # 연도가 변경되었으면 상태 업데이트
        if year != st.session_state.selected_year:
            self.on_year_change(year)
        
        # 3개년 재무제표 데이터 가져오기
        years = [year-2, year-1, year]
        financial_data_list = []
        valid_years = []
        valid_financial_data_list = []
        
        for yr in years:
            with st.spinner(f"{yr}년 재무제표 조회 중..."):
                fin_data = self.dart_api.get_financial_statements(corp_code, str(yr))
                financial_data_list.append(fin_data)
 
                # 유효한 데이터만 필터링
                if fin_data and 'list' in fin_data and len(fin_data['list']) > 0:
                    valid_financial_data_list.append(fin_data)
                    valid_years.append(yr)
                    st.success(f"{yr}년 데이터 조회 완료 ({len(fin_data['list'])}개 항목)")
                else:
                    st.warning(f"{yr}년 데이터가 없습니다.")

        # 유효한 데이터가 없으면 안내 메시지 출력
        if not valid_financial_data_list:
            st.error("조회 가능한 재무 데이터가 없습니다.")
            return

        # 유효한 데이터만으로 재무 분석 진행
        financial_data = self.financial_analyzer.process_financial_data(valid_financial_data_list, valid_years)

        # 자산/부채/자본 그래프
        st.subheader("재무상태")
        balance_df = pd.DataFrame({
            "연도": [str(y) for y in financial_data["years"]],
            "자산": financial_data["assets"],
            "부채": financial_data["liabilities"],
            "자본": financial_data["equity"]
        })
        
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
        st.subheader("손익 현황")
        income_df = pd.DataFrame({
            "연도": [str(y) for y in financial_data["years"]],
            "매출액": financial_data["revenue"],
            "영업이익": financial_data["operating_profit"],
            "당기순이익": financial_data["net_income"]
        })
        
        fig2 = px.line(
            income_df, 
            x="연도", 
            y=["매출액", "영업이익", "당기순이익"],
            title="매출 및 이익 추이",
            labels={"value": "금액 (백만원)", "variable": "항목"},
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # 재무 비율 계산 및 표시
        st.subheader("주요 재무 비율")
        ratios = self.financial_analyzer.calculate_financial_ratios(financial_data)
        ratio_df = pd.DataFrame(ratios)
        st.dataframe(ratio_df, hide_index=True)
        
        # 가치 평가
        st.subheader("간단 가치 평가")
        
        # 가치 평가 결과
        valuation_results = self.financial_analyzer.calculate_valuation(financial_data)
        valuation_df = pd.DataFrame(valuation_results["valuations"])
        st.dataframe(valuation_df, hide_index=True)
        
        # 가치 평가 범위
        min_value, max_value = valuation_results["range"]
        if min_value > 0 or max_value > 0:
            st.write(f"**추정 기업 가치 범위: {min_value:,.0f}백만원 ~ {max_value:,.0f}백만원**")
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

            # 기본 정보와 재무 정보를 나란히 표시
            col1, col2 = st.columns([1, 2])

            # 기업 기본 정보 표시
            with col1:
                self.display_company_info(st.session_state.company_info)

            # 재무 정보 표시
            with col2:
                self.display_financial_info(st.session_state.selected_company["corp_code"])