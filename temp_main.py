import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from llm_analyzer import LLMAnalyzer
import json
from typing import Dict, Any

st.set_page_config(
    page_title="기업 가치 평가 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 추가
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-top: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin-bottom: 1rem;
    }
    .highlight {
        color: #1E88E5;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<p class="main-header">기업 가치 평가 시스템</p>', unsafe_allow_html=True)
    st.markdown('기업의 재무 데이터를 바탕으로 EBITDA와 DCF 방식으로 기업 가치를 평가합니다.')
    
    # 사이드바 설정
    with st.sidebar:
        st.header("설정")
        api_key = st.text_input("OpenAI API 키", type="password")
        
        st.markdown("---")
        st.header("분석 모드")
        analysis_mode = st.radio(
            "분석 모드 선택", 
            ["샘플 데이터 사용", "직접 데이터 입력"]
        )

    # 데이터 입력 (샘플 또는 직접 입력)
    if analysis_mode == "샘플 데이터 사용":
        company_info, financial_data, industry_info = load_sample_data()
    else:
        company_info, financial_data, industry_info = input_company_data()
    
    # 회사 정보 요약 표시
    display_company_summary(company_info, financial_data, industry_info)
    
    # 분석 버튼
    col1, col2 = st.columns([3, 1])
    with col2:
        analyze_button = st.button("기업 가치 평가 실행", type="primary", use_container_width=True)
    
    # 분석 실행
    if analyze_button:
        if not api_key:
            st.error("OpenAI API 키를 입력해주세요.")
        else:
            with st.spinner("기업 가치를 평가 중입니다..."):
                analyzer = LLMAnalyzer()
                analyzer.set_api_key(api_key)
                
                result = analyzer.analyze_company_value(company_info, financial_data, industry_info)
                
                if result["status"] == "success":
                    valuation_data = result.get("valuation_data")
                    
                    # 시각화 함수 호출
                    if valuation_data:
                        LLMAnalyzer.display_valuation_results(valuation_data)
                        
                        # 결과 다운로드 버튼 추가
                        st.download_button(
                            label="결과 JSON 다운로드",
                            data=json.dumps(valuation_data, indent=2, ensure_ascii=False),
                            file_name=f"{company_info['corp_name']}_valuation.json",
                            mime="application/json"
                        )
                    else:
                        st.error("기업 가치 평가 결과를 가져오지 못했습니다.")
                else:
                    st.error(result["message"])
                    if "raw_content" in result:
                        with st.expander("LLM 응답 (JSON 파싱 불가)"):
                            st.text(result["raw_content"])

def load_sample_data():
    """샘플 데이터 로드"""
    company_info = {
        "corp_name": "삼성전자(주)",
        "induty_code": "264",
        "induty": "반도체 및 전자부품 제조"
    }
    
    financial_data = {
        "years": [2022, 2023, 2024],
        "assets": [448424507, 455905980, 514531948],
        "liabilities": [93674903, 92228115, 112339878],
        "equity": [345186142, 363677865, 402192070],
        "revenue": [302231360, 258935494, 300870903],
        "operating_profit": [43376630, 6566976, 32725961],
        "net_income": [55654077, 15487100, 34451351]
    }
    
    industry_info = {
        "sector": "전자/반도체",
        "avg_per": 15.2,
        "avg_pbr": 1.8
    }
    
    return company_info, financial_data, industry_info

def input_company_data():
    """사용자 입력 데이터 처리"""
    st.markdown('<p class="sub-header">기업 정보 입력</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("기업명", "삼성전자(주)")
    with col2:
        industry_code = st.text_input("업종 코드", "264")
    
    business_area = st.text_input("사업 영역", "반도체 및 전자부품 제조")
    
    company_info = {
        "corp_name": company_name,
        "induty_code": industry_code,
        "induty": business_area
    }
    
    st.markdown('<p class="sub-header">재무 정보 입력 (단위: 백만원)</p>', unsafe_allow_html=True)
    
    # 재무 데이터를 위한 빈 데이터 구조
    years = []
    assets = []
    liabilities = []
    equity = []
    revenue = []
    operating_profit = []
    net_income = []
    
    # 3개년 데이터 입력
    num_years = 3
    col_year, col_asset, col_liability, col_equity = st.columns(4)
    col_revenue, col_op_profit, col_net_income = st.columns(3)
    
    with col_year:
        st.markdown("<b>연도</b>", unsafe_allow_html=True)
    with col_asset:
        st.markdown("<b>자산</b>", unsafe_allow_html=True) 
    with col_liability:
        st.markdown("<b>부채</b>", unsafe_allow_html=True)
    with col_equity:
        st.markdown("<b>자본</b>", unsafe_allow_html=True)
    with col_revenue:
        st.markdown("<b>매출액</b>", unsafe_allow_html=True)
    with col_op_profit:
        st.markdown("<b>영업이익</b>", unsafe_allow_html=True)
    with col_net_income:
        st.markdown("<b>당기순이익</b>", unsafe_allow_html=True)
    
    for i in range(num_years):
        with col_year:
            year = st.number_input(f"연도 {i+1}", value=2022+i, key=f"year_{i}")
            years.append(year)
        
        with col_asset:
            asset = st.number_input(f"자산 {i+1}", value=[448424507, 455905980, 514531948][i], key=f"asset_{i}")
            assets.append(asset)
        
        with col_liability:
            liability = st.number_input(f"부채 {i+1}", value=[93674903, 92228115, 112339878][i], key=f"liability_{i}")
            liabilities.append(liability)
        
        with col_equity:
            equity_val = st.number_input(f"자본 {i+1}", value=[345186142, 363677865, 402192070][i], key=f"equity_{i}")
            equity.append(equity_val)
        
        with col_revenue:
            rev = st.number_input(f"매출액 {i+1}", value=[302231360, 258935494, 300870903][i], key=f"revenue_{i}")
            revenue.append(rev)
        
        with col_op_profit:
            op_profit = st.number_input(f"영업이익 {i+1}", value=[43376630, 6566976, 32725961][i], key=f"op_profit_{i}")
            operating_profit.append(op_profit)
        
        with col_net_income:
            net = st.number_input(f"당기순이익 {i+1}", value=[55654077, 15487100, 34451351][i], key=f"net_income_{i}")
            net_income.append(net)
    
    financial_data = {
        "years": years,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "revenue": revenue,
        "operating_profit": operating_profit,
        "net_income": net_income
    }
    
    st.markdown('<p class="sub-header">산업 정보 입력</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        sector = st.text_input("산업군", "전자/반도체")
    with col2:
        avg_per = st.number_input("경쟁사 평균 PER", value=15.2)
    with col3:
        avg_pbr = st.number_input("경쟁사 평균 PBR", value=1.8)
    
    industry_info = {
        "sector": sector,
        "avg_per": avg_per,
        "avg_pbr": avg_pbr
    }
    
    return company_info, financial_data, industry_info

def display_company_summary(company_info: Dict[str, Any], financial_data: Dict[str, Any], industry_info: Dict[str, Any]):
    """회사 정보 요약"""
    st.markdown('<p class="sub-header">기업 정보 요약</p>', unsafe_allow_html=True)
    
    with st.expander("기업 정보 보기", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**기업명**: {company_info['corp_name']}")
            st.markdown(f"**업종 코드**: {company_info['induty_code']}")
            st.markdown(f"**사업 영역**: {company_info['induty']}")
        
        with col2:
            st.markdown(f"**산업군**: {industry_info['sector']}")
            st.markdown(f"**경쟁사 평균 PER**: {industry_info['avg_per']}")
            st.markdown(f"**경쟁사 평균 PBR**: {industry_info['avg_pbr']}")
        
        # 재무 데이터 시각화
        st.markdown("### 재무 데이터 추이")
        
        # 재무 데이터를 데이터프레임으로 변환
        df_financials = pd.DataFrame({
            "연도": financial_data["years"],
            "자산": financial_data["assets"],
            "부채": financial_data["liabilities"],
            "자본": financial_data["equity"],
            "매출액": financial_data["revenue"],
            "영업이익": financial_data["operating_profit"],
            "당기순이익": financial_data["net_income"]
        })
        
        # 영업이익과 당기순이익 추이 차트
        fig_profit = px.line(
            df_financials, 
            x="연도", 
            y=["영업이익", "당기순이익"],
            title="영업이익 및 당기순이익 추이 (백만원)",
            markers=True,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_profit, use_container_width=True)
        
        # 부채비율 및 수익성 지표 계산
        df_financials["부채비율"] = (df_financials["부채"] / df_financials["자본"]) * 100
        df_financials["영업이익률"] = (df_financials["영업이익"] / df_financials["매출액"]) * 100
        df_financials["순이익률"] = (df_financials["당기순이익"] / df_financials["매출액"]) * 100
        df_financials["ROE"] = (df_financials["당기순이익"] / df_financials["자본"]) * 100
        df_financials["ROA"] = (df_financials["당기순이익"] / df_financials["자산"]) * 100
        
        # 비율 데이터 정리
        df_ratios = pd.DataFrame({
            "연도": df_financials["연도"],
            "영업이익률(%)": df_financials["영업이익률"].round(2),
            "순이익률(%)": df_financials["순이익률"].round(2),
            "ROE(%)": df_financials["ROE"].round(2),
            "ROA(%)": df_financials["ROA"].round(2),
            "부채비율(%)": df_financials["부채비율"].round(2)
        })
        
        # 표로 표시
        st.markdown("### 재무 비율")
        st.dataframe(df_ratios, use_container_width=True)

if __name__ == "__main__":
    main()