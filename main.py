import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

# 페이지 설정
st.set_page_config(
    page_title="Bridge - 기업 정보 조회 시스템",
    page_icon="📊",
    layout="wide"
)

# API 키 설정 (실제 사용 시 환경 변수나 st.secrets에서 불러오는 것이 좋습니다)
# Open DART API 키를 발급받아야 합니다: https://opendart.fss.or.kr/
API_KEY = st.sidebar.text_input("OPEN DART API KEY를 입력하세요", type="password")

# 사이드바에 앱 소개 추가
st.sidebar.title("Bridge POC")
st.sidebar.markdown("""
이 애플리케이션은 Open DART API를 활용하여 기업 정보를 조회하는 POC입니다.
""")

# 메인 타이틀
st.title("Bridge - 기업 정보 조회 시스템 POC")

# DART API 관련 함수들
def search_companies(keyword):
    """키워드로 기업 검색"""
    url = f"https://opendart.fss.or.kr/api/corpCode.xml"
    params = {
        "crtfc_key": API_KEY
    }
    
    # 실제 API 호출 대신 에러 처리를 위한 예시
    if not API_KEY:
        st.error("API 키를 입력해주세요.")
        return []
    
    # 기업 목록 샘플 데이터 (실제로는 API에서 가져옴)
    # 실제 구현 시에는 API 호출 결과를 파싱하여 처리해야 합니다
    sample_companies = [
        {"corp_code": "00126380", "corp_name": "삼성전자", "stock_code": "005930"},
        {"corp_code": "00164742", "corp_name": "현대자동차", "stock_code": "005380"},
        {"corp_code": "00164779", "corp_name": "LG전자", "stock_code": "066570"},
        {"corp_code": "00126186", "corp_name": "SK하이닉스", "stock_code": "000660"},
        {"corp_code": "00155863", "corp_name": "NAVER", "stock_code": "035420"},
        {"corp_code": "00261861", "corp_name": "카카오", "stock_code": "035720"},
        {"corp_code": "00113410", "corp_name": "포스코", "stock_code": "005490"},
        {"corp_code": "00120030", "corp_name": "KB금융", "stock_code": "105560"},
        {"corp_code": "00104237", "corp_name": "신한지주", "stock_code": "055550"},
        {"corp_code": "00361411", "corp_name": "카카오뱅크", "stock_code": "323410"}
    ]
    
    if keyword:
        filtered_companies = [comp for comp in sample_companies if keyword.lower() in comp["corp_name"].lower()]
        return filtered_companies
    return sample_companies

def get_company_info(corp_code):
    """기업 기본 정보 조회"""
    url = f"https://opendart.fss.or.kr/api/company.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code
    }
    
    # API 호출 대신 샘플 데이터 반환
    sample_info = {
        "corp_name": "삼성전자",
        "corp_name_eng": "Samsung Electronics Co.,Ltd.",
        "stock_name": "삼성전자",
        "stock_code": "005930",
        "ceo_nm": "김기남, 김현석, 고동진",
        "corp_cls": "Y",
        "jurir_no": "1301110006246",
        "bizr_no": "1248100998",
        "adres": "경기도 수원시 영통구 삼성로 129 (매탄동)",
        "hm_url": "www.samsung.com/sec",
        "ir_url": "https://www.samsung.com/sec/ir/",
        "phn_no": "031-200-1114",
        "fax_no": "031-200-7538",
        "induty_code": "264",
        "est_dt": "19690113",
        "acc_mt": "12"
    }
    
    if corp_code == "00126380":  # 삼성전자
        return sample_info
    elif corp_code == "00164742":  # 현대자동차
        sample_info.update({
            "corp_name": "현대자동차",
            "corp_name_eng": "Hyundai Motor Company",
            "stock_name": "현대차",
            "stock_code": "005380",
            "ceo_nm": "정의선",
            "adres": "서울특별시 서초구 헌릉로 12 (양재동)",
            "hm_url": "www.hyundai.com",
            "est_dt": "19670329"
        })
        return sample_info
    # 기타 회사들에 대한 정보도 유사하게 추가할 수 있습니다
    
    # 임시 응답 (일반적인 경우)
    sample_info.update({
        "corp_name": f"회사{corp_code}",
        "corp_name_eng": f"Company {corp_code}",
        "stock_name": f"회사{corp_code}",
        "stock_code": "000000",
        "ceo_nm": "홍길동",
        "adres": "서울특별시 중구 세종대로 123",
        "hm_url": "www.company.com",
        "est_dt": "20000101"
    })
    return sample_info

def get_financial_statements(corp_code, year, report_code="11011"):
    """재무제표 정보 조회"""
    # 샘플 재무 데이터 반환
    if corp_code == "00126380":  # 삼성전자
        return {
            "assets": [365768324, 426621158, 457880613],  # 단위: 백만원
            "liabilities": [89213233, 121721170, 123146744],
            "equity": [276555091, 304899988, 334733869],
            "revenue": [279604796, 301864466, 302231472],
            "operating_profit": [51633856, 51633123, 43764749],
            "net_income": [39907450, 39907123, 39907890],
            "years": [year-2, year-1, year]
        }
    else:
        # 다른 회사들에 대한 임의의 재무 데이터
        import random
        base_assets = random.randint(10000000, 100000000)
        base_revenue = random.randint(5000000, 50000000)
        
        return {
            "assets": [int(base_assets * 0.8), int(base_assets * 0.9), base_assets],
            "liabilities": [int(base_assets * 0.3), int(base_assets * 0.35), int(base_assets * 0.4)],
            "equity": [int(base_assets * 0.5), int(base_assets * 0.55), int(base_assets * 0.6)],
            "revenue": [int(base_revenue * 0.8), int(base_revenue * 0.9), base_revenue],
            "operating_profit": [int(base_revenue * 0.1), int(base_revenue * 0.12), int(base_revenue * 0.15)],
            "net_income": [int(base_revenue * 0.07), int(base_revenue * 0.08), int(base_revenue * 0.1)],
            "years": [year-2, year-1, year]
        }

# 메인 애플리케이션 로직
def main():
    # 기업 검색
    search_keyword = st.text_input("기업명을 입력하세요:")
    companies = search_companies(search_keyword)
    
    if companies:
        company_names = [f"{comp['corp_name']} ({comp['stock_code']})" for comp in companies]
        selected_company_idx = st.selectbox("기업을 선택하세요:", range(len(company_names)), format_func=lambda x: company_names[x])
        
        if st.button("기업 정보 조회"):
            selected_company = companies[selected_company_idx]
            corp_code = selected_company["corp_code"]
            
            # 기본 정보와 재무 정보를 나란히 표시하기 위한 레이아웃
            col1, col2 = st.columns([1, 2])
            
            # 기업 기본 정보 표시
            with col1:
                st.subheader("기업 기본 정보")
                company_info = get_company_info(corp_code)
                
                # 기업 로고 (실제로는 API에서 로고를 가져오거나 URL을 구성해야 함)
                st.image(f"https://via.placeholder.com/150x150.png?text={company_info['corp_name']}", width=150)
                
                info_df = pd.DataFrame([
                    {"항목": "기업명", "내용": company_info["corp_name"]},
                    {"항목": "영문명", "내용": company_info["corp_name_eng"]},
                    {"항목": "종목코드", "내용": company_info["stock_code"]},
                    {"항목": "대표이사", "내용": company_info["ceo_nm"]},
                    {"항목": "설립일", "내용": f"{company_info['est_dt'][:4]}년 {company_info['est_dt'][4:6]}월 {company_info['est_dt'][6:]}일" if len(company_info.get('est_dt', '')) >= 8 else company_info.get('est_dt', '')},
                    {"항목": "주소", "내용": company_info["adres"]},
                    {"항목": "홈페이지", "내용": company_info["hm_url"]},
                    {"항목": "전화번호", "내용": company_info.get("phn_no", "")},
                ])
                
                st.dataframe(info_df, hide_index=True)
                
                # 회사 평가 점수 (예시)
                st.subheader("M&A 적합성 평가")
                
                # 점수 시각화
                scores = {
                    "성장성": 85,
                    "수익성": 75,
                    "안정성": 90,
                    "매각 가능성": 80,
                    "업계 경쟁력": 85
                }
                
                for metric, score in scores.items():
                    st.metric(label=metric, value=f"{score}/100")
            
            # 재무 정보 표시
            with col2:
                st.subheader("재무 정보")
                
                # 연도 선택
                current_year = datetime.now().year
                year = st.selectbox("기준 연도:", list(range(current_year-5, current_year)), index=4)
                
                # 재무제표 데이터 가져오기
                financial_data = get_financial_statements(corp_code, year)
                
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
                
                # 최신 연도 기준 비율 계산
                current_revenue = financial_data["revenue"][-1]
                current_assets = financial_data["assets"][-1]
                current_equity = financial_data["equity"][-1]
                current_liabilities = financial_data["liabilities"][-1]
                current_op_profit = financial_data["operating_profit"][-1]
                current_net_income = financial_data["net_income"][-1]
                
                # 3개년 비율 계산
                years = financial_data["years"]
                revenue_growth = ["-"] + [f"{(financial_data['revenue'][i] / financial_data['revenue'][i-1] - 1) * 100:.2f}%" for i in range(1, len(financial_data['revenue']))]
                profit_margin = [f"{(financial_data['operating_profit'][i] / financial_data['revenue'][i]) * 100:.2f}%" for i in range(len(financial_data['revenue']))]
                net_margin = [f"{(financial_data['net_income'][i] / financial_data['revenue'][i]) * 100:.2f}%" for i in range(len(financial_data['revenue']))]
                roe = [f"{(financial_data['net_income'][i] / financial_data['equity'][i]) * 100:.2f}%" for i in range(len(financial_data['equity']))]
                debt_ratio = [f"{(financial_data['liabilities'][i] / financial_data['assets'][i]) * 100:.2f}%" for i in range(len(financial_data['assets']))]
                
                ratio_df = pd.DataFrame({
                    "연도": [str(y) for y in years],
                    "매출 성장률": revenue_growth,
                    "영업이익률": profit_margin,
                    "순이익률": net_margin,
                    "ROE": roe,
                    "부채비율": debt_ratio
                })
                
                st.dataframe(ratio_df, hide_index=True)
                
                # 가치 평가 (간단한 예시)
                st.subheader("간단 가치 평가")
                
                # PER 기반 가치 평가 (예시)
                avg_industry_per = 15
                st.write(f"업종 평균 PER: {avg_industry_per}")
                
                # 최근 순이익 기준 PER 계산
                estimated_value_per = current_net_income * avg_industry_per
                
                # EBITDA Multiple 기반 가치 평가 (가정: EBITDA ≈ 영업이익 * 1.2)
                avg_industry_ebitda_multiple = 8
                estimated_ebitda = current_op_profit * 1.2  # 간단하게 영업이익의 1.2배로 EBITDA 추정
                estimated_value_ebitda = estimated_ebitda * avg_industry_ebitda_multiple
                
                # 순자산 가치
                estimated_value_nav = current_equity
                
                # 가치 평가 결과 표시
                valuation_df = pd.DataFrame([
                    {"평가 방법": "PER 기준 가치", "추정 가치 (백만원)": f"{estimated_value_per:,.0f}"},
                    {"평가 방법": "EBITDA Multiple 기준 가치", "추정 가치 (백만원)": f"{estimated_value_ebitda:,.0f}"},
                    {"평가 방법": "순자산 가치", "추정 가치 (백만원)": f"{estimated_value_nav:,.0f}"}
                ])
                
                st.dataframe(valuation_df, hide_index=True)
                
                # 가치 평가 범위 (최솟값과 최댓값 사이)
                min_value = min(estimated_value_per, estimated_value_ebitda, estimated_value_nav)
                max_value = max(estimated_value_per, estimated_value_ebitda, estimated_value_nav)
                
                st.write(f"**추정 기업 가치 범위: {min_value:,.0f}백만원 ~ {max_value:,.0f}백만원**")
    else:
        st.info("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")

if __name__ == "__main__":
    main()