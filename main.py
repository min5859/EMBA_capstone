import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import zipfile
import io
import xml.etree.ElementTree as ET
import tempfile
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bridge")

class DartAPI:
    """DART OpenAPI와 상호작용하는 클래스"""
    
    def __init__(self, api_key):
        """DART API 클래스 초기화
        
        Args:
            api_key (str): DART OpenAPI 키
        """
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"
    
    def get_corp_codes(self):
        """기업 코드 목록 조회
        
        Returns:
            list: 기업 코드, 이름, 주식 코드 정보 목록
        """
        url = f"{self.base_url}/corpCode.xml"
        params = {
            "crtfc_key": self.api_key
        }
        
        if not self.api_key:
            logger.error("API 키가 없습니다.")
            return None
        
        try:
            logger.info("기업 코드 목록 조회 API 호출")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"API 호출 에러: {response.status_code}")
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
            
            logger.info(f"총 {len(corp_list)}개의 기업 코드를 검색했습니다.")
            return corp_list
        except Exception as e:
            logger.error(f"기업 코드 조회 오류: {str(e)}")
            return None
    
    def get_company_info(self, corp_code):
        """기업 기본 정보 조회
        
        Args:
            corp_code (str): 기업 고유 코드
            
        Returns:
            dict: 기업 기본 정보
        """
        url = f"{self.base_url}/company.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code
        }
        
        try:
            logger.info(f"기업 정보 API 호출: {corp_code}")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"기업 정보 조회 에러: {response.status_code}")
                return None
            
            data = response.json()
            if data.get('status') != '000':
                logger.error(f"기업 정보 API 오류: {data.get('message')}")
                return None
            
            return data
        except Exception as e:
            logger.error(f"기업 정보 조회 오류: {str(e)}")
            return None
    
    def get_financial_statements(self, corp_code, bsns_year, reprt_code="11011"):
        """사업보고서 재무제표 정보 조회
        
        Args:
            corp_code (str): 기업 고유 코드
            bsns_year (str): 사업연도
            reprt_code (str, optional): 보고서 코드. 기본값은 "11011" (사업보고서)
            
        Returns:
            dict: 재무제표 정보
        """
        url = f"{self.base_url}/fnlttSinglAcntAll.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
            "fs_div": "CFS"  # 연결재무제표
        }
        
        try:
            logger.info(f"재무제표 API 호출: {corp_code} {bsns_year}")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"재무제표 조회 에러: {response.status_code}")
                return None
            
            data = response.json()
            if data.get('status') != '000':
                logger.error(f"재무제표 API 오류: {data.get('message')}")
                return None
            
            return data
        except Exception as e:
            logger.error(f"재무제표 조회 오류: {str(e)}")
            return None


class FinancialAnalyzer:
    """재무 데이터 분석 및 처리를 위한 클래스"""
    
    @staticmethod
    def process_financial_data(financial_data_list, years):
        """여러 연도의 재무 데이터를 처리하여 필요한 정보 추출

        Args:
            financial_data_list (list): 각 연도별 재무제표 데이터 목록
            years (list): 연도 목록

        Returns:
            dict: 처리된 재무 데이터
        """
        # 디버깅 정보 출력
        st.write("## 디버깅 정보")
        st.write(f"요청 연도: {years}")
        st.write(f"데이터 목록 길이: {len(financial_data_list)}")

        # 각 데이터셋의 기본 정보 확인
        for i, data in enumerate(financial_data_list):
            if data is None:
                st.write(f"{years[i]}년 데이터: None")
            elif 'status' in data and data['status'] != '000':
                st.write(f"{years[i]}년 데이터: API 오류 - {data.get('message', '알 수 없는 오류')}")
            elif 'list' not in data:
                st.write(f"{years[i]}년 데이터: 'list' 키 없음")
            else:
                st.write(f"{years[i]}년 데이터: {len(data['list'])}개 항목")

                # 첫 5개 항목 샘플 출력
                if len(data['list']) > 0:
                    st.write(f"{years[i]}년 데이터 샘플:")
                    sample_data = pd.DataFrame(data['list'][:5])[['account_nm', 'account_id', 'thstrm_amount']]
                    st.dataframe(sample_data)

        # 관심 있는 계정과목
        accounts = {
            "자산": ["ifrs-full_Assets", "ifrs_Assets", "Assets", 
                     "ifrs-full_TotalAssets", "ifrs_TotalAssets", "TotalAssets"],
            "부채": ["ifrs-full_Liabilities", "ifrs_Liabilities", "Liabilities", 
                     "ifrs-full_TotalLiabilities", "ifrs_TotalLiabilities", "TotalLiabilities"],
            "자본": ["ifrs-full_Equity", "ifrs_Equity", "Equity", 
                     "EquityAttributableToOwnersOfParent", "ifrs-full_EquityAttributableToOwnersOfParent",
                     "ifrs-full_TotalEquity", "ifrs_TotalEquity", "TotalEquity"],
            "매출액": ["ifrs-full_Revenue", "ifrs_Revenue", "Revenue", 
                      "ifrs-full_OperatingRevenue", "ifrs_OperatingRevenue", "OperatingRevenue", 
                      "ifrs-full_GrossOperatingProfit", "ifrs_GrossOperatingProfit", "GrossOperatingProfit",
                      "ifrs-full_Sales", "ifrs_Sales", "Sales"],
            "영업이익": ["ifrs-full_OperatingIncome", "ifrs_OperatingIncome", "OperatingIncome", 
                        "ifrs-full_ProfitLossFromOperatingActivities", "ifrs_ProfitLossFromOperatingActivities",
                        "ProfitLossFromOperatingActivities"],
            "당기순이익": ["ifrs-full_ProfitLoss", "ifrs_ProfitLoss", "ProfitLoss", 
                         "ifrs-full_ProfitLossAttributableToOwnersOfParent", "ifrs_ProfitLossAttributableToOwnersOfParent", 
                         "ProfitLossAttributableToOwnersOfParent", "ifrs-full_NetIncome", "ifrs_NetIncome", "NetIncome"]
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
            st.write(f"### {years[idx]}년 데이터 처리")

            year_result = {
                "assets": 0,
                "liabilities": 0,
                "equity": 0,
                "revenue": 0,
                "operating_profit": 0,
                "net_income": 0
            }

            if year_data is None or 'list' not in year_data:
                st.write(f"{years[idx]}년: 데이터 없음")
                for key in year_result.keys():
                    result[key].append(0)
                continue
            
            # 각 계정 찾기
            fin_data = year_data['list']

            # 계정과목 목록 확인
            unique_accounts = {}
            for item in fin_data:
                if 'account_id' in item and 'account_nm' in item:
                    unique_accounts[item['account_id']] = item['account_nm']

            st.write(f"발견된 계정과목 수: {len(unique_accounts)}")

            # 주요 계정과목 찾기
            found_accounts = {key: False for key in accounts.keys()}

            # 각 계정별로 값 찾기
            for fin_item in fin_data:
                account_id = fin_item.get('account_id')
                if account_id:
                    for key, id_list in accounts.items():
                        if account_id in id_list:
                            sj_div = fin_item.get('sj_div', '')

                            # 대차대조표 항목 (자산, 부채, 자본)
                            if key in ["자산", "부채", "자본"] and sj_div == 'BS':
                                try:
                                    value = int(fin_item.get('thstrm_amount', '0').replace(',', ''))
                                    if key == "자산" and year_result["assets"] == 0:
                                        year_result["assets"] = value // 1000000  # 백만원 단위로 변환
                                        found_accounts[key] = True
                                        st.write(f"✅ {key} 찾음: {fin_item.get('account_nm')} = {value // 1000000}백만원")
                                    elif key == "부채" and year_result["liabilities"] == 0:
                                        year_result["liabilities"] = value // 1000000
                                        found_accounts[key] = True
                                        st.write(f"✅ {key} 찾음: {fin_item.get('account_nm')} = {value // 1000000}백만원")
                                    elif key == "자본" and year_result["equity"] == 0:
                                        year_result["equity"] = value // 1000000
                                        found_accounts[key] = True
                                        st.write(f"✅ {key} 찾음: {fin_item.get('account_nm')} = {value // 1000000}백만원")
                                except (ValueError, TypeError) as e:
                                    st.write(f"❌ {key} 처리 오류: {e}")

                            # 손익계산서 항목 (매출액, 영업이익, 당기순이익)
                            elif key in ["매출액", "영업이익", "당기순이익"] and (sj_div == 'CIS' or sj_div == 'IS'):
                                try:
                                    value = int(fin_item.get('thstrm_amount', '0').replace(',', ''))
                                    if key == "매출액" and year_result["revenue"] == 0:
                                        year_result["revenue"] = value // 1000000
                                        found_accounts[key] = True
                                        st.write(f"✅ {key} 찾음: {fin_item.get('account_nm')} = {value // 1000000}백만원")
                                    elif key == "영업이익" and year_result["operating_profit"] == 0:
                                        year_result["operating_profit"] = value // 1000000
                                        found_accounts[key] = True
                                        st.write(f"✅ {key} 찾음: {fin_item.get('account_nm')} = {value // 1000000}백만원")
                                    elif key == "당기순이익" and year_result["net_income"] == 0:
                                        year_result["net_income"] = value // 1000000
                                        found_accounts[key] = True
                                        st.write(f"✅ {key} 찾음: {fin_item.get('account_nm')} = {value // 1000000}백만원")
                                except (ValueError, TypeError) as e:
                                    st.write(f"❌ {key} 처리 오류: {e}")

            # 찾지 못한 계정과목 표시
            for key, found in found_accounts.items():
                if not found:
                    st.write(f"❌ {key} 찾지 못함")
                    # 찾고자 하는 계정과목 ID 표시
                    st.write(f"    찾을 ID: {accounts[key]}")
                    # 유사한 계정과목 찾기
                    similar_accounts = []
                    for act_id, act_nm in unique_accounts.items():
                        for pattern in accounts[key]:
                            if pattern.lower() in act_id.lower():
                                similar_accounts.append(f"{act_id} ({act_nm})")
                    if similar_accounts:
                        st.write(f"    유사 계정과목: {', '.join(similar_accounts[:5])}")

            # 연도별 결과 추가
            for key, value in year_result.items():
                result[key].append(value)

        # 처리 결과 요약
        st.write("### 처리 결과 요약")
        result_df = pd.DataFrame({
            "연도": years,
            "자산": result["assets"],
            "부채": result["liabilities"],
            "자본": result["equity"],
            "매출액": result["revenue"],
            "영업이익": result["operating_profit"],
            "당기순이익": result["net_income"]
        })
        st.dataframe(result_df)

        # 유효 데이터 확인
        valid_data_count = sum(1 for i in range(len(years)) 
                              if result["revenue"][i] > 0 or result["operating_profit"][i] > 0)

        if valid_data_count > 0:
            st.write(f"유효한 재무 데이터가 있는 연도 수: {valid_data_count}")
        else:
            st.warning("유효한 재무 데이터가 없습니다!")

        # 계정과목 ID를 좀 더 확인하기 위한 정보
        st.write("### 모든 계정과목 목록")
        all_accounts = {}
        for data in financial_data_list:
            if data and 'list' in data:
                for item in data['list']:
                    if 'account_id' in item and 'account_nm' in item:
                        all_accounts[item['account_id']] = item['account_nm']

        if all_accounts:
            st.write(f"총 계정과목 수: {len(all_accounts)}")
            account_df = pd.DataFrame([
                {"계정ID": k, "계정명": v} for k, v in all_accounts.items()
            ])
            st.dataframe(account_df)

        return result
    
    @staticmethod
    def calculate_financial_ratios(financial_data):
        """재무 비율 계산
        
        Args:
            financial_data (dict): 처리된 재무 데이터
            
        Returns:
            dict: 계산된 재무 비율
        """
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
        
        return {
            "연도": [str(y) for y in years],
            "매출 성장률": revenue_growth,
            "영업이익률": profit_margin,
            "순이익률": net_margin,
            "ROE": roe,
            "부채비율": debt_ratio
        }
    
    @staticmethod
    def calculate_valuation(financial_data):
        """간단한 기업 가치 평가
        
        Args:
            financial_data (dict): 처리된 재무 데이터
            
        Returns:
            dict: 가치 평가 결과
        """
        #current_revenue = financial_data["revenue"][-1]

        # 유효한 데이터가 없는 경우 처리
        if not any(financial_data["net_income"]) and not any(financial_data["operating_profit"]):
            return {
                "valuations": [
                    {"평가 방법": "데이터 부족", "추정 가치 (백만원)": "N/A"}
                ],
                "range": (0, 0)
            }

        # 가장 최근 유효 데이터 찾기
        for i in range(len(financial_data["years"])-1, -1, -1):
            if financial_data["net_income"][i] > 0 or financial_data["operating_profit"][i] > 0:
                current_net_income = financial_data["net_income"][i]
                current_op_profit = financial_data["operating_profit"][i]
                current_equity = financial_data["equity"][i]
                year = financial_data["years"][i]

                st.info(f"가치평가에 {year}년 데이터를 사용합니다.")
                break
        else:
            # 유효한 데이터를 찾지 못한 경우
            return {
                "valuations": [
                    {"평가 방법": "데이터 부족", "추정 가치 (백만원)": "N/A"}
                ],
                "range": (0, 0)
            }

        # PER 기반 가치 평가
        avg_industry_per = 15  # 업종 평균 PER (예시)
        estimated_value_per = current_net_income * avg_industry_per if current_net_income > 0 else 0
        
        # EBITDA Multiple 기반 가치 평가
        avg_industry_ebitda_multiple = 8  # 업종 평균 EBITDA Multiple (예시)
        estimated_ebitda = current_op_profit * 1.2  # 간단하게 영업이익의 1.2배로 EBITDA 추정
        estimated_value_ebitda = estimated_ebitda * avg_industry_ebitda_multiple if estimated_ebitda > 0 else 0
        
        # 순자산 가치
        estimated_value_nav = current_equity
        
        valuations = [
            {"평가 방법": "PER 기준 가치", "추정 가치 (백만원)": f"{estimated_value_per:,.0f}"},
            {"평가 방법": "EBITDA Multiple 기준 가치", "추정 가치 (백만원)": f"{estimated_value_ebitda:,.0f}"},
            {"평가 방법": "순자산 가치", "추정 가치 (백만원)": f"{estimated_value_nav:,.0f}"}
        ]
        
        # 가치 평가 범위
        values = [v for v in [estimated_value_per, estimated_value_ebitda, estimated_value_nav] if v > 0]
        if values:
            min_value = min(values)
            max_value = max(values)
            valuation_range = (min_value, max_value)
        else:
            valuation_range = (0, 0)
        
        return {
            "valuations": valuations,
            "range": valuation_range
        }


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
    
    def display_financial_info(self, corp_code):
        """재무 정보 표시
        
        Args:
            corp_code (str): 기업 고유 코드
        """
        st.subheader("재무 정보")

        # 연도 선택
        current_year = datetime.now().year
        year = st.selectbox("기준 연도:", list(range(current_year-7, current_year)), index=4)

        # 탐색할 연도 범위 확장
        st.write("탐색할 연도 범위:")
        year_range = st.slider("연도 범위", 1, 5, 3)
        years = list(range(year-year_range+1, year+1))

        # 3개년 재무제표 데이터 가져오기
        years = [year-2, year-1, year]
        financial_data_list = []
        valid_years = []
        valid_financial_data_list = []

        for idx, yr in enumerate(years):
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
        
        # 기업 검색
        search_keyword = st.text_input("기업명을 입력하세요:")
        companies = self.search_companies(search_keyword)
        
        if companies:
            company_names = [f"{comp['corp_name']} ({comp['stock_code']})" for comp in companies]
            selected_company_idx = st.selectbox("기업을 선택하세요:", range(len(company_names)), format_func=lambda x: company_names[x])
            
            if st.button("기업 정보 조회"):
                selected_company = companies[selected_company_idx]
                corp_code = selected_company["corp_code"]
                
                # 기업 정보 로딩 표시
                with st.spinner("기업 정보를 조회 중입니다..."):
                    company_info = self.dart_api.get_company_info(corp_code)
                
                if company_info:
                    # 기본 정보와 재무 정보를 나란히 표시
                    col1, col2 = st.columns([1, 2])
                    
                    # 기업 기본 정보 표시
                    with col1:
                        self.display_company_info(company_info)
                    
                    # 재무 정보 표시
                    with col2:
                        self.display_financial_info(corp_code)
                else:
                    st.error("기업 정보를 조회할 수 없습니다.")
        else:
            if search_keyword:
                st.info("검색 결과가 없습니다. 다른 키워드로 검색해보세요.")
            else:
                st.info("기업명을 입력하여 검색하세요.")


# 애플리케이션 실행
if __name__ == "__main__":
    app = BridgeApp()
    app.run()