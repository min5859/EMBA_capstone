import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime
from dart_api import DartAPI
from financial_analyzer import FinancialAnalyzer
from llm_analyzer import LLMAnalyzer
from llm_analyzer import GemmaAnalyzer
from llm_analyzer import Gemma3Analyzer
from llm_analyzer import ClaudeAnalyzer
import json
from display_valuation import display_valuation_results

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
            
        if 'openai_api_key' not in st.session_state:
            # LLMAnalyzer 클래스를 통해 환경변수에서 API 키 로드
            st.session_state.openai_api_key = LLMAnalyzer.get_api_key_from_env()
        
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
        if st.session_state.api_key:
            self.dart_api = DartAPI(st.session_state.api_key)
        else:
            self.dart_api = None
        self.financial_analyzer = FinancialAnalyzer()
        self.llm_analyzer = LLMAnalyzer()
        self.gemma_analyzer = GemmaAnalyzer()
        self.gemma3_analyzer = Gemma3Analyzer()
        self.claude_analyzer = ClaudeAnalyzer()

    def setup_sidebar(self):
        """사이드바 설정"""
        st.sidebar.title("🌉 Bridge POC")
        
        # 기업 검색 섹션
        with st.sidebar.expander("기업 검색", expanded=not st.session_state.selected_company):
            search_keyword = st.text_input("기업명을 입력하세요:", value="삼성전자")
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
        st.dataframe(balance_df, hide_index=True, use_container_width=True, key="statements_balance_table")
        
        # 그래프 표시
        fig1 = px.bar(
            balance_df, 
            x="연도", 
            y=["자산", "부채", "자본"],
            barmode="group",
            title="자산/부채/자본 추이",
            labels={"value": "금액 (백만원)", "variable": "항목"}
        )
        st.plotly_chart(fig1, use_container_width=True, key="statements_balance_chart")
        
        # 매출/이익 그래프
        st.subheader("손익계산서")
        income_df = pd.DataFrame({
            "연도": [str(y) for y in financial_data["years"]],
            "매출액": financial_data["revenue"],
            "영업이익": financial_data["operating_profit"],
            "당기순이익": financial_data["net_income"]
        })
        
        # 표 형태로 데이터 표시
        st.dataframe(income_df, hide_index=True, use_container_width=True, key="statements_income_table")
        
        # 그래프 표시
        fig2 = px.line(
            income_df, 
            x="연도", 
            y=["매출액", "영업이익", "당기순이익"],
            title="매출 및 이익 추이",
            labels={"value": "금액 (백만원)", "variable": "항목"},
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True, key="statements_income_chart")
    
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
        
        # 데이터프레임 피봇을 위한 데이터 준비
        ratio_data = []
        for ratio_type in ["매출 성장률", "영업이익률", "순이익률", "ROE", "부채비율"]:
            ratio_data.append({
                "항목": ratio_type,
                **{year: value for year, value in zip(ratios["연도"], ratios[ratio_type])}
            })
        
        # 피봇된 데이터프레임 생성
        ratio_df = pd.DataFrame(ratio_data)
        
        # 표 형태로 데이터 표시
        st.dataframe(ratio_df, hide_index=True, use_container_width=True, key="ratios_summary_table")
        
        # 주요 비율 그래프로 표시

        # 0. 영업이익과 순이익의 실제 값 (막대 그래프)
        profit_values = pd.DataFrame({
            "연도": financial_data["years"],
            "영업이익": financial_data["operating_profit"],
            "순이익": financial_data["net_income"]
        })
        
        fig4 = px.bar(
            profit_values,
            x="연도",
            y=["영업이익", "순이익"],
            barmode="group",
            title="영업이익 및 순이익 추이",
            labels={"value": "금액 (백만원)", "variable": "항목"}
        )
        st.plotly_chart(fig4, use_container_width=True, key="ratios_profit_values_chart")

        # 1. 수익성 비율 (영업이익률, 순이익률)
        profit_ratios = pd.DataFrame({
            "연도": ratios["연도"],
            "영업이익률": [float(r.strip('%')) if r != '-' else 0 for r in ratios["영업이익률"]],
            "순이익률": [float(r.strip('%')) if r != '-' else 0 for r in ratios["순이익률"]]
        })
        
        fig1 = px.line(
            profit_ratios,
            x="연도",
            y=["영업이익률", "순이익률"],
            title="수익성 비율 추이",
            labels={"value": "비율 (%)", "variable": "항목"},
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True, key="ratios_profit_ratios_chart")
        
        # 2. 성장성 비율 (매출 성장률)
        growth_ratios = pd.DataFrame({
            "연도": ratios["연도"],
            "매출 성장률": [float(r.strip('%')) if r != '-' else 0 for r in ratios["매출 성장률"]]
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
        st.plotly_chart(fig2, use_container_width=True, key="ratios_growth_ratios_chart")
        
        # 3. 안정성 및 효율성 비율 (부채비율, ROE)
        stability_ratios = pd.DataFrame({
            "연도": ratios["연도"],
            "부채비율": [float(r.strip('%')) if r != '-' else 0 for r in ratios["부채비율"]],
            "ROE": [float(r.strip('%')) if r != '-' else 0 for r in ratios["ROE"]]
        })
        
        fig3 = px.bar(
            stability_ratios,
            x="연도",
            y=["부채비율", "ROE"],
            barmode="group",
            title="부채비율 및 ROE 추이",
            labels={"value": "비율 (%)", "variable": "항목"}
        )
        st.plotly_chart(fig3, use_container_width=True, key="ratios_stability_ratios_chart")
        
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
    
    def display_llm_analysis(self, company_info, corp_code):
        """LLM을 이용한 기업 분석 표시"""
        st.subheader("AI 기반 기업 가치 분석")

        # 분석기 선택을 위한 탭 생성
        analyzer_tabs = st.tabs(["GPT-4 분석", "Gemma 분석", "Gemma3 분석", "Claude 분석"])

        # 각 분석기별로 공통된 분석 로직을 함수로 추출
        def perform_analysis(analyzer, analysis_mode_key, run_analysis_key, question_key, question_result_key):
            # 데이터 로드
            financial_data, success = self._load_financial_data(corp_code)
            if not success:
                st.error("조회 가능한 재무 데이터가 없습니다.")
                return

            # 분석 모드 선택
            analysis_mode = st.radio(
                "분석 모드 선택:", 
                ["기업 가치 종합 분석", "맞춤형 질문 분석"],
                horizontal=True,
                key=analysis_mode_key
            )

            # 분석 결과를 저장할 세션 상태 키 생성
            result_key = f"{analyzer.__class__.__name__.lower()}_analysis_result"
            valuation_data_key = f"{analyzer.__class__.__name__.lower()}_valuation_data"

            if analysis_mode == "기업 가치 종합 분석":
                if st.button(f"{analyzer.__class__.__name__} 종합 분석 시작", key=run_analysis_key, type="primary", use_container_width=True):
                    with st.spinner(f"{analyzer.__class__.__name__}가 기업을 분석 중입니다..."):
                        industry_info = {
                            "sector": company_info.get('induty', '알 수 없음'),
                            "avg_per": "15.2",
                            "avg_pbr": "1.8"
                        }

                        # 분석 수행
                        result = analyzer.analyze_company_value(
                            company_info, 
                            financial_data, 
                            industry_info
                        )

                        # 결과를 세션 상태에 저장
                        st.session_state[result_key] = result

                        if result["status"] == "success":
                            st.success(f"{analyzer.__class__.__name__} 분석이 완료되었습니다!")

                            # 시각화 함수 호출
                            valuation_data = result.get("valuation_data")
                            if valuation_data:
                                # 시각화 데이터를 세션 상태에 저장
                                st.session_state[valuation_data_key] = valuation_data
                                display_valuation_results(valuation_data)

                                # 결과 다운로드 버튼 추가
                                st.download_button(
                                    label="결과 JSON 다운로드",
                                    data=json.dumps(valuation_data, indent=2, ensure_ascii=False),
                                    file_name=f"{company_info['corp_name']}_{analyzer.__class__.__name__.lower()}_valuation.json",
                                    mime="application/json"
                                )
                            else:
                                st.error("기업 가치 평가 결과를 가져오지 못했습니다.")
                        else:
                            st.error(f"분석 중 오류가 발생했습니다: {result.get('message', '알 수 없는 오류')}")
                        return  # 분석이 완료되면 함수 종료
                else:
                    # 이전 분석 결과가 있으면 표시
                    if result_key in st.session_state and st.session_state[result_key]["status"] == "success":
                        result = st.session_state[result_key]
                        st.success(f"{analyzer.__class__.__name__} 분석이 완료되었습니다!")

                        # 시각화 함수 호출
                        valuation_data = st.session_state.get(valuation_data_key)
                        if valuation_data:
                            display_valuation_results(valuation_data)

                            # 결과 다운로드 버튼 추가
                            st.download_button(
                                label="결과 JSON 다운로드",
                                data=json.dumps(valuation_data, indent=2, ensure_ascii=False),
                                file_name=f"{company_info['corp_name']}_{analyzer.__class__.__name__.lower()}_valuation.json",
                                mime="application/json"
                            )

            else:  # 맞춤형 질문 분석 모드
                st.subheader(f"맞춤형 기업 분석 질문 ({analyzer.__class__.__name__})")

                default_questions = [
                    "이 기업의 성장성과 수익성 측면에서 투자 매력도는 어떤가요?",
                    "이 기업의 재무 상태는 안정적인가요?",
                    "이 기업의 주요 리스크 요인은 무엇인가요?",
                    "이 기업은 M&A 대상으로서 적합한가요?",
                    "이 기업의 경쟁 우위는 무엇인가요?"
                ]

                question_option = st.selectbox(
                    "질문 선택 또는 직접 입력하기:",
                    ["직접 입력하기"] + default_questions,
                    key=question_key
                )

                if question_option == "직접 입력하기":
                    user_question = st.text_area(
                        "분석할 질문을 입력하세요:",
                        height=100,
                        key=f"{analyzer.__class__.__name__.lower()}_user_question"
                    )
                else:
                    user_question = question_option

                if user_question and st.button(f"{analyzer.__class__.__name__}로 질문 분석하기", type="primary", key=f"analyze_{analyzer.__class__.__name__.lower()}_question", use_container_width=True):
                    with st.spinner(f"{analyzer.__class__.__name__}가 질문을 분석 중입니다..."):
                        result = analyzer.analyze_investment_potential(
                            company_info,
                            financial_data,
                            user_question
                        )

                        # 결과를 세션 상태에 저장
                        st.session_state[question_result_key] = result

                        if result["status"] == "success":
                            st.success("질문 분석이 완료되었습니다!")
                            st.markdown("### 분석 결과")
                            st.markdown(result["analysis"])
                        else:
                            st.error(f"분석 중 오류가 발생했습니다: {result.get('message', '알 수 없는 오류')}")
                    return  # 분석이 완료되면 함수 종료
                else:
                    # 이전 질문 분석 결과가 있으면 표시
                    if question_result_key in st.session_state and st.session_state[question_result_key]["status"] == "success":
                        result = st.session_state[question_result_key]
                        st.success("질문 분석이 완료되었습니다!")
                        st.markdown("### 분석 결과")
                        st.markdown(result["analysis"])

        # 각 탭에 대해 분석 수행
        with analyzer_tabs[0]:
            perform_analysis(self.llm_analyzer, "gpt4_analysis_mode", "run_gpt4_analysis", "gpt4_question_option", "gpt4_question_result")

        with analyzer_tabs[1]:
            perform_analysis(self.gemma_analyzer, "gemma_analysis_mode", "run_gemma_analysis", "gemma_question_option", "gemma_question_result")

        with analyzer_tabs[2]:
            perform_analysis(self.gemma3_analyzer, "gemma3_analysis_mode", "run_gemma3_analysis", "gemma3_question_option", "gemma3_question_result")

        with analyzer_tabs[3]:
            perform_analysis(self.claude_analyzer, "claude_analysis_mode", "run_claude_analysis", "claude_question_option", "claude_question_result")

    def run(self):
        """애플리케이션 실행"""
        # 사이드바 설정
        self.setup_sidebar()

        # API 키 확인
        if not st.session_state.api_key:
            st.warning("사이드바에 Open DART API 키를 입력해주세요.")
            return

        # 선택된 기업 정보 표시
        if st.session_state.selected_company and st.session_state.company_info:
            # 선택된 기업 정보 헤더 표시
            st.markdown(f"## {st.session_state.company_info.get('corp_name', '알 수 없음')} ({st.session_state.selected_company.get('stock_code', '')})")

            # 탭 생성
            tabs = st.tabs(["기업 개요", "재무", "가치 평가", "LLM 분석"])
            
            # 탭 1: 기업 개요
            with tabs[0]:
                self.display_company_info(st.session_state.company_info)
                
            # 탭 2: 재무
            with tabs[1]:
                # 재무 내부 탭 생성
                finance_tabs = st.tabs(["재무현황", "재무상태표", "손익계산서", "종합"])
                
                # 재무현황 탭
                with finance_tabs[0]:
                    self.display_financial_ratios(st.session_state.selected_company["corp_code"])
                
                # 재무상태표 탭
                with finance_tabs[1]:
                    self.display_balance_sheet(st.session_state.selected_company["corp_code"])
                
                # 손익계산서 탭
                with finance_tabs[2]:
                    self.display_income_statement(st.session_state.selected_company["corp_code"])
                
                # 종합 탭
                with finance_tabs[3]:
                    self.display_financial_overview(st.session_state.selected_company["corp_code"])
                
            # 탭 3: 가치 평가
            with tabs[2]:
                self.display_valuation(st.session_state.selected_company["corp_code"])
                
            # 탭 4: LLM 기업 분석
            with tabs[3]:
                self.display_llm_analysis(st.session_state.company_info, st.session_state.selected_company["corp_code"])
        else:
            st.info("기업을 선택하세요.")

    def display_balance_sheet(self, corp_code):
        """재무상태표 정보 표시
        
        Args:
            corp_code (str): 기업 고유 코드
        """
        st.subheader("재무상태표")
        
        # 연도 선택기 표시
        year_changed = self._year_selector("balance_sheet")
        
        # 데이터 로드
        financial_data, success = self._load_financial_data(corp_code)
        if not success:
            st.error("조회 가능한 재무 데이터가 없습니다.")
            return
            
        # 재무상태표 데이터프레임 생성
        balance_sheet_data = []
        years = financial_data["years"]
        
        # 자산 섹션
        balance_sheet_data.extend([
            {"항목": "자산", "구분": "총계"} | {str(year): value for year, value in zip(years, financial_data["assets"])},
            {"항목": "유동자산", "구분": "소계"} | {str(year): value for year, value in zip(years, financial_data["current_assets"])},
            {"항목": "당기자산", "구분": "상세"} | {str(year): value for year, value in zip(years, financial_data["cash_and_equivalents"])},
            {"항목": "매출채권", "구분": "상세"} | {str(year): value for year, value in zip(years, financial_data["trade_receivables"])},
            {"항목": "재고자산", "구분": "상세"} | {str(year): value for year, value in zip(years, financial_data["inventories"])},
            {"항목": "비유동자산", "구분": "소계"} | {str(year): value for year, value in zip(years, financial_data["non_current_assets"])},
        ])
        
        # 부채 섹션
        balance_sheet_data.extend([
            {"항목": "부채", "구분": "총계"} | {str(year): value for year, value in zip(years, financial_data["liabilities"])},
            {"항목": "유동부채", "구분": "소계"} | {str(year): value for year, value in zip(years, financial_data["current_liabilities"])},
            {"항목": "매입채무", "구분": "상세"} | {str(year): value for year, value in zip(years, financial_data["trade_payables"])},
            {"항목": "단기차입금", "구분": "상세"} | {str(year): value for year, value in zip(years, financial_data["short_term_borrowings"])},
            {"항목": "비유동부채", "구분": "소계"} | {str(year): value for year, value in zip(years, financial_data["non_current_liabilities"])},
        ])
        
        # 자본 섹션
        balance_sheet_data.extend([
            {"항목": "자본", "구분": "총계"} | {str(year): value for year, value in zip(years, financial_data["equity"])},
        ])
        
        # 데이터프레임 생성
        df = pd.DataFrame(balance_sheet_data)
        
        # 스타일 적용을 위한 함수
        def highlight_totals(row):
            if row["구분"] == "총계":
                return ["font-weight: bold; background-color: #f0f2f6"] * len(row)
            elif row["구분"] == "소계":
                return ["font-weight: bold; background-color: #f8f9fa"] * len(row)
            return [""] * len(row)
        
        # 스타일이 적용된 데이터프레임 표시
        st.dataframe(
            df.style.apply(highlight_totals, axis=1),
            hide_index=True,
            use_container_width=True,
            key="balance_sheet_table"
        )
        
        # 주요 비율 계산 및 표시
        st.subheader("주요 재무비율")
        
        ratios_data = []
        for i, year in enumerate(years):
            if financial_data["assets"][i] > 0:  # 0으로 나누기 방지
                current_ratio = (financial_data["current_assets"][i] / financial_data["current_liabilities"][i] * 100) if financial_data["current_liabilities"][i] > 0 else 0
                debt_ratio = (financial_data["liabilities"][i] / financial_data["assets"][i] * 100)
                equity_ratio = (financial_data["equity"][i] / financial_data["assets"][i] * 100)
                
                ratios_data.append({
                    "연도": str(year),
                    "유동비율": f"{current_ratio:.1f}%",
                    "부채비율": f"{debt_ratio:.1f}%",
                    "자기자본비율": f"{equity_ratio:.1f}%"
                })
        
        ratios_df = pd.DataFrame(ratios_data)
        st.dataframe(ratios_df, hide_index=True, use_container_width=True, key="balance_sheet_ratios_table")
        
        # 시각화 섹션
        col1, col2 = st.columns(2)
        
        with col1:
            # 자산/부채/자본 막대 그래프
            st.subheader("자산/부채/자본 추이")
            balance_df = pd.DataFrame({
                "연도": [str(y) for y in years],
                "자산": financial_data["assets"],
                "부채": financial_data["liabilities"],
                "자본": financial_data["equity"]
            })
            
            fig1 = px.bar(
                balance_df,
                x="연도",
                y=["자산", "부채", "자본"],
                title="자산/부채/자본 추이",
                labels={"value": "금액 (백만원)", "variable": "항목"},
                barmode="group"
            )
            st.plotly_chart(fig1, use_container_width=True, key="balance_sheet_balance_chart")
        
        with col2:
            # 자산 구조 시각화
            st.subheader("자산 구조 추이")
            asset_structure = pd.DataFrame({
                "연도": [str(y) for y in years],
                "유동자산": financial_data["current_assets"],
                "비유동자산": financial_data["non_current_assets"]
            })
            
            fig2 = px.bar(
                asset_structure,
                x="연도",
                y=["유동자산", "비유동자산"],
                title="자산 구조 추이",
                labels={"value": "금액 (백만원)", "variable": "구분"},
                barmode="stack"
            )
            st.plotly_chart(fig2, use_container_width=True, key="balance_sheet_asset_structure_chart")

    def display_income_statement(self, corp_code):
        """손익계산서 정보 표시
        
        Args:
            corp_code (str): 기업 고유 코드
        """
        st.subheader("손익계산서")
        
        # 연도 선택기 표시
        year_changed = self._year_selector("income_statement")
        
        # 데이터 로드
        financial_data, success = self._load_financial_data(corp_code)
        if not success:
            st.error("조회 가능한 재무 데이터가 없습니다.")
            return
        
        # 손익계산서 데이터프레임 생성
        income_data = []
        for item in ["매출액", "영업이익", "당기순이익"]:
            income_data.append({
                "항목": item,
                **{str(year): value for year, value in zip(financial_data["years"], financial_data[{
                    "매출액": "revenue",
                    "영업이익": "operating_profit",
                    "당기순이익": "net_income"
                }[item]])}
            })
        
        # 피봇된 데이터프레임 생성
        df = pd.DataFrame(income_data)
        
        # 표 형태로 데이터 표시
        st.dataframe(df, hide_index=True, use_container_width=True, key="income_statement_table")
        
        # 그래프 표시
        fig = px.line(
            pd.DataFrame({
                "연도": [str(y) for y in financial_data["years"]],
                "매출액": financial_data["revenue"],
                "영업이익": financial_data["operating_profit"],
                "당기순이익": financial_data["net_income"]
            }),
            x="연도", 
            y=["매출액", "영업이익", "당기순이익"],
            title="매출 및 이익 추이",
            labels={"value": "금액 (백만원)", "variable": "항목"},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True, key="income_statement_chart")

    def display_financial_overview(self, corp_code):
        """모든 재무 관련 그래프를 한 화면에서 표시
        
        Args:
            corp_code (str): 기업 고유 코드
        """
        st.subheader("재무 종합 분석")
        
        # 연도 선택기 표시
        year_changed = self._year_selector("financial_overview")
        
        # 데이터 로드
        financial_data, success = self._load_financial_data(corp_code)
        if not success:
            st.error("조회 가능한 재무 데이터가 없습니다.")
            return
        
        # 재무 비율 계산
        ratios = self.financial_analyzer.calculate_financial_ratios(financial_data)
        
        # 2열 레이아웃으로 그래프 배치
        col1, col2 = st.columns(2)
        
        with col1:
            # 1. 자산/부채/자본 그래프
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
            st.plotly_chart(fig1, use_container_width=True, key="overview_balance_chart")
            
            # 3. 수익성 비율 (영업이익률, 순이익률)
            profit_ratios = pd.DataFrame({
                "연도": ratios["연도"],
                "영업이익률": [float(r.strip('%')) if r != '-' else 0 for r in ratios["영업이익률"]],
                "순이익률": [float(r.strip('%')) if r != '-' else 0 for r in ratios["순이익률"]]
            })
            
            fig3 = px.line(
                profit_ratios,
                x="연도",
                y=["영업이익률", "순이익률"],
                title="수익성 비율 추이",
                labels={"value": "비율 (%)", "variable": "항목"},
                markers=True
            )
            st.plotly_chart(fig3, use_container_width=True, key="overview_profit_ratios_chart")
            
            # 5. 안정성 및 효율성 비율 (부채비율, ROE)
            stability_ratios = pd.DataFrame({
                "연도": ratios["연도"],
                "부채비율": [float(r.strip('%')) if r != '-' else 0 for r in ratios["부채비율"]],
                "ROE": [float(r.strip('%')) if r != '-' else 0 for r in ratios["ROE"]]
            })
            
            fig5 = px.bar(
                stability_ratios,
                x="연도",
                y=["부채비율", "ROE"],
                barmode="group",
                title="부채비율 및 ROE 추이",
                labels={"value": "비율 (%)", "variable": "항목"}
            )
            st.plotly_chart(fig5, use_container_width=True, key="overview_stability_ratios_chart")
        
        with col2:
            # 2. 매출/이익 그래프
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
            st.plotly_chart(fig2, use_container_width=True, key="overview_income_chart")
            
            # 4. 성장성 비율 (매출 성장률)
            growth_ratios = pd.DataFrame({
                "연도": ratios["연도"],
                "매출 성장률": [float(r.strip('%')) if r != '-' else 0 for r in ratios["매출 성장률"]]
            })
            
            fig4 = px.bar(
                growth_ratios,
                x="연도",
                y="매출 성장률",
                title="매출 성장률 추이",
                labels={"매출 성장률": "성장률 (%)"},
                color="매출 성장률",
                color_continuous_scale=["red", "yellow", "green"]
            )
            st.plotly_chart(fig4, use_container_width=True, key="overview_growth_ratios_chart")
            
            # 6. 자산 구조 시각화
            asset_structure = pd.DataFrame({
                "연도": [str(y) for y in financial_data["years"]],
                "유동자산": financial_data["current_assets"],
                "비유동자산": financial_data["non_current_assets"]
            })
            
            fig6 = px.bar(
                asset_structure,
                x="연도",
                y=["유동자산", "비유동자산"],
                title="자산 구조 추이",
                labels={"value": "금액 (백만원)", "variable": "구분"},
                barmode="stack"
            )
            st.plotly_chart(fig6, use_container_width=True, key="overview_asset_structure_chart")
        
        # 7. 주요 재무비율 요약 테이블 (전체 너비 사용)
        st.subheader("주요 재무비율 요약")
        ratios_data = []
        for i, year in enumerate(financial_data["years"]):
            if financial_data["assets"][i] > 0:  # 0으로 나누기 방지
                current_ratio = (financial_data["current_assets"][i] / financial_data["current_liabilities"][i] * 100) if financial_data["current_liabilities"][i] > 0 else 0
                debt_ratio = (financial_data["liabilities"][i] / financial_data["assets"][i] * 100)
                equity_ratio = (financial_data["equity"][i] / financial_data["assets"][i] * 100)
                
                ratios_data.append({
                    "연도": str(year),
                    "유동비율": f"{current_ratio:.1f}%",
                    "부채비율": f"{debt_ratio:.1f}%",
                    "자기자본비율": f"{equity_ratio:.1f}%",
                    "영업이익률": ratios["영업이익률"][i],
                    "순이익률": ratios["순이익률"][i],
                    "ROE": ratios["ROE"][i],
                    "매출 성장률": ratios["매출 성장률"][i]
                })
        
        ratios_df = pd.DataFrame(ratios_data)
        st.dataframe(ratios_df, hide_index=True, use_container_width=True, key="overview_ratios_table")