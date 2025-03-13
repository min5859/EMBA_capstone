import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import zipfile
import io
import xml.etree.ElementTree as ET
import tempfile

# 페이지 설정
st.set_page_config(
    page_title="Bridge - 기업 정보 조회 시스템",
    page_icon="📊",
    layout="wide"
)

# API 키 설정 (세션 스테이트에 저장)
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

API_KEY = st.sidebar.text_input("OPEN DART API KEY를 입력하세요", type="password", key="dart_api_key")
if API_KEY:
    st.session_state.api_key = API_KEY

# 사이드바에 앱 소개 추가
st.sidebar.title("Bridge POC")
st.sidebar.markdown("""
이 애플리케이션은 Open DART API를 활용하여 기업 정보를 조회하는 POC입니다.
""")

# API 키 상태 표시
if st.session_state.api_key:
    st.sidebar.success("API 키가 입력되었습니다.")
else:
    st.sidebar.warning("API 키를 입력해주세요.")

# 메인 타이틀
st.title("Bridge - 기업 정보 조회 시스템 POC")

# 기업 코드 정보를 저장할 변수
corp_code_data = None

# DART API 관련 함수들
@st.cache_data(ttl=3600)
def get_corp_codes(api_key):
    """기업 코드 목록 조회 및 캐싱"""
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {
        "crtfc_key": api_key
    }
    
    if not api_key:
        st.error("API 키를 입력해주세요.")
        return None
    
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            st.error(f"API 호출 에러: {response.status_code}")
            return None
        
        # zip 파일을 메모리에서 처리
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            xml_data = zip_file.read(zip_file.namelist()[0])
        
        # XML 파싱
        root = ET.fromstring(xml_data)
        corp_list = []
        
        for company in root.findall('list'):
            corp_code = company.findtext('corp_code')
            corp_name = company.findtext('corp_name')
            stock_code = company.findtext('stock_code')
            modify_date = company.findtext('modify_date')
            
            if stock_code and stock_code.strip():  # 상장 기업만 필터링
                corp_list.append({
                    'corp_code': corp_code,
                    'corp_name': corp_name,
                    'stock_code': stock_code,
                    'modify_date': modify_date
                })
        
        return corp_list
    except Exception as e:
        st.error(f"기업 코드 조회 오류: {str(e)}")
        return None

def search_companies(keyword, api_key):
    """키워드로 기업 검색"""
    global corp_code_data
    
    if corp_code_data is None:
        corp_code_data = get_corp_codes(api_key)
        
    if corp_code_data is None:
        return []
    
    if keyword:
        filtered_companies = [comp for comp in corp_code_data if keyword.lower() in comp["corp_name"].lower()]
        return filtered_companies[:10]  # 최대 10개만 반환
    return corp_code_data[:10]  # 최대 10개만 반환

@st.cache_data(ttl=3600)
def get_company_info(corp_code, api_key):
    """기업 기본 정보 조회"""
    url = "https://opendart.fss.or.kr/api/company.json"
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            st.error(f"기업 정보 조회 에러: {response.status_code}")
            return None
        
        data = response.json()
        if data.get('status') != '000':
            st.error(f"기업 정보 API 오류: {data.get('message')}")
            return None
        
        return data
    except Exception as e:
        st.error(f"기업 정보 조회 오류: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_financial_statements(corp_code, bsns_year, api_key, reprt_code="11011"):
    """사업보고서 재무제표 정보 조회"""
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code,  # 사업보고서
        "fs_div": "CFS"  # 연결재무제표
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            st.error(f"재무제표 조회 에러: {response.status_code}")
            return None
        
        data = response.json()
        if data.get('status') != '000':
            st.error(f"재무제표 API 오류: {data.get('message')}")
            return None
        
        return data
    except Exception as e:
        st.error(f"재무제표 조회 오류: {str(e)}")
        return None

def process_financial_data(financial_data_list, years):
    """여러 연도의 재무 데이터를 처리하여 필요한 정보 추출"""
    # 관심 있는 계정과목
    accounts = {
        "자산": ["ifrs-full_Assets", "ifrs_Assets", "Assets"],
        "부채": ["ifrs-full_Liabilities", "ifrs_Liabilities", "Liabilities"],
        "자본": ["ifrs-full_Equity", "ifrs_Equity", "Equity", "EquityAttributableToOwnersOfParent"],
        "매출액": ["ifrs-full_Revenue", "ifrs_Revenue", "Revenue", "ifrs_GrossOperatingProfit", "GrossOperatingProfit"],
        "영업이익": ["ifrs-full_OperatingIncome", "ifrs_OperatingIncome", "OperatingIncome", "ifrs_ProfitLossFromOperatingActivities"],
        "당기순이익": ["ifrs-full_ProfitLoss", "ifrs_ProfitLoss", "ProfitLoss", "ifrs_ProfitLossAttributableToOwnersOfParent"]
    }
    
    # 결과 데이터 초기화
    result = {
        "assets": [],
        "liabilities": [],
        "equity": [],
        "revenue": [],
        "operating_profit": [],
        "net_income": [],
        "years": years
    }
    
    # 연도별 데이터 처리
    for idx, year_data in enumerate(financial_data_list):
        if year_data is None or 'list' not in year_data:
            # 빈 데이터 처리
            result["assets"].append(0)
            result["liabilities"].append(0)
            result["equity"].append(0)
            result["revenue"].append(0)
            result["operating_profit"].append(0)
            result["net_income"].append(0)
            continue
        
        # 각 계정 찾기
        fin_data = year_data['list']
        
        # 각 계정별로 값 찾기
        for fin_item in fin_data:
            account_id = fin_item.get('account_id')
            if account_id:
                for key, id_list in accounts.items():
                    if account_id in id_list and fin_item.get('sj_div') == 'BS' and key in ["자산", "부채", "자본"]:
                        try:
                            value = int(fin_item.get('thstrm_amount', '0').replace(',', ''))
                            if key == "자산" and (not result["assets"] or result["assets"][-1] == 0):
                                result["assets"].append(value // 1000000)  # 백만원 단위로 변환
                            elif key == "부채" and (not result["liabilities"] or result["liabilities"][-1] == 0):
                                result["liabilities"].append(value // 1000000)
                            elif key == "자본" and (not result["equity"] or result["equity"][-1] == 0):
                                result["equity"].append(value // 1000000)
                        except (ValueError, TypeError):
                            pass
                    elif account_id in id_list and fin_item.get('sj_div') == 'CIS' and key in ["매출액", "영업이익", "당기순이익"]:
                        try:
                            value = int(fin_item.get('thstrm_amount', '0').replace(',', ''))
                            if key == "매출액" and (not result["revenue"] or result["revenue"][-1] == 0):
                                result["revenue"].append(value // 1000000)
                            elif key == "영업이익" and (not result["operating_profit"] or result["operating_profit"][-1] == 0):
                                result["operating_profit"].append(value // 1000000)
                            elif key == "당기순이익" and (not result["net_income"] or result["net_income"][-1] == 0):
                                result["net_income"].append(value // 1000000)
                        except (ValueError, TypeError):
                            pass
    
    # 부족한 데이터 채우기
    for key in ["assets", "liabilities", "equity", "revenue", "operating_profit", "net_income"]:
        while len(result[key]) < len(years):
            result[key].append(0)
    
    return result

# 메인 애플리케이션 로직
def main():
    # API 키 확인
    if not st.session_state.api_key:
        st.warning("사이드바에 Open DART API 키를 입력해주세요.")
        return
        
    # 기업 검색
    search_keyword = st.text_input("기업명을 입력하세요:")
    companies = search_companies(search_keyword, st.session_state.api_key)
    
    if companies:
        company_names = [f"{comp['corp_name']} ({comp['stock_code']})" for comp in companies]
        selected_company_idx = st.selectbox("기업을 선택하세요:", range(len(company_names)), format_func=lambda x: company_names[x])
        
        if st.button("기업 정보 조회"):
            selected_company = companies[selected_company_idx]
            corp_code = selected_company["corp_code"]
            
            # 기업 정보 로딩 표시
            with st.spinner("기업 정보를 조회 중입니다..."):
                company_info = get_company_info(corp_code, st.session_state.api_key)
            
            if company_info:
                # 기본 정보와 재무 정보를 나란히 표시하기 위한 레이아웃
                col1, col2 = st.columns([1, 2])
                
                # 기업 기본 정보 표시
                with col1:
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
                    
                    # 회사 평가 점수 (샘플 - 실제로는 다른 데이터 소스나 알고리즘으로 대체 필요)
                    st.subheader("M&A 적합성 평가 (샘플)")
                    
                    # 점수 시각화
                    import random
                    scores = {
                        "성장성": random.randint(60, 95),
                        "수익성": random.randint(60, 95),
                        "안정성": random.randint(60, 95),
                        "매각 가능성": random.randint(60, 95),
                        "업계 경쟁력": random.randint(60, 95)
                    }
                    
                    for metric, score in scores.items():
                        st.metric(label=metric, value=f"{score}/100")
                
                # 재무 정보 표시
                with col2:
                    st.subheader("재무 정보")
                    
                    # 연도 선택
                    current_year = datetime.now().year
                    year = st.selectbox("기준 연도:", list(range(current_year-5, current_year)), index=4)
                    
                    # 3개년 재무제표 데이터 가져오기
                    years = [year-2, year-1, year]
                    financial_data_list = []
                    
                    for yr in years:
                        with st.spinner(f"{yr}년 재무제표 조회 중..."):
                            fin_data = get_financial_statements(corp_code, str(yr), st.session_state.api_key)
                            financial_data_list.append(fin_data)
                    
                    # 재무 데이터 처리
                    financial_data = process_financial_data(financial_data_list, years)
                    
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
                    
                    # 3개년 비율 계산
                    years = financial_data["years"]
                    
                    # 매출 성장률
                    revenue_growth = ["-"]
                    for i in range(1, len(financial_data['revenue'])):
                        if financial_data['revenue'][i-1] > 0:
                            growth = (financial_data['revenue'][i] / financial_data['revenue'][i-1] - 1) * 100
                            revenue_growth.append(f"{growth:.2f}%")
                        else:
                            revenue_growth.append("-")
                    
                    # 영업이익률
                    profit_margin = []
                    for i in range(len(financial_data['revenue'])):
                        if financial_data['revenue'][i] > 0:
                            margin = (financial_data['operating_profit'][i] / financial_data['revenue'][i]) * 100
                            profit_margin.append(f"{margin:.2f}%")
                        else:
                            profit_margin.append("-")
                    
                    # 순이익률
                    net_margin = []
                    for i in range(len(financial_data['revenue'])):
                        if financial_data['revenue'][i] > 0:
                            margin = (financial_data['net_income'][i] / financial_data['revenue'][i]) * 100
                            net_margin.append(f"{margin:.2f}%")
                        else:
                            net_margin.append("-")
                    
                    # ROE
                    roe = []
                    for i in range(len(financial_data['equity'])):
                        if financial_data['equity'][i] > 0:
                            return_on_equity = (financial_data['net_income'][i] / financial_data['equity'][i]) * 100
                            roe.append(f"{return_on_equity:.2f}%")
                        else:
                            roe.append("-")
                    
                    # 부채비율
                    debt_ratio = []
                    for i in range(len(financial_data['assets'])):
                        if financial_data['assets'][i] > 0:
                            ratio = (financial_data['liabilities'][i] / financial_data['assets'][i]) * 100
                            debt_ratio.append(f"{ratio:.2f}%")
                        else:
                            debt_ratio.append("-")
                    
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
                    
                    # 최근 재무 데이터
                    current_revenue = financial_data["revenue"][-1]
                    current_op_profit = financial_data["operating_profit"][-1]
                    current_net_income = financial_data["net_income"][-1]
                    current_equity = financial_data["equity"][-1]
                    
                    # PER 기반 가치 평가 (예시)
                    avg_industry_per = 15  # 업종 평균 PER 예시
                    st.write(f"업종 평균 PER: {avg_industry_per} (샘플)")
                    
                    # 최근 순이익 기준 PER 계산
                    estimated_value_per = current_net_income * avg_industry_per if current_net_income > 0 else 0
                    
                    # EBITDA Multiple 기반 가치 평가 (가정: EBITDA ≈ 영업이익 * 1.2)
                    avg_industry_ebitda_multiple = 8  # 업종 평균 EBITDA Multiple 예시
                    estimated_ebitda = current_op_profit * 1.2  # 간단하게 영업이익의 1.2배로 EBITDA 추정
                    estimated_value_ebitda = estimated_ebitda * avg_industry_ebitda_multiple if estimated_ebitda > 0 else 0
                    
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
                    values = [v for v in [estimated_value_per, estimated_value_ebitda, estimated_value_nav] if v > 0]
                    if values:
                        min_value = min(values)
                        max_value = max(values)
                        st.write(f"**추정 기업 가치 범위: {min_value:,.0f}백만원 ~ {max_value:,.0f}백만원**")
                    else:
                        st.warning("가치 평가에 필요한 재무 데이터가 충분하지 않습니다.")
            else:
                st.error("기업 정보를 조회할 수 없습니다.")
    else:
        if search_keyword:
            st.info("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")
        else:
            st.info("기업명을 입력하여 검색하세요.")

if __name__ == "__main__":
    main()