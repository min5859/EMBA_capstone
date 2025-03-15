import streamlit as st
import pandas as pd

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
        # 디버깅 정보는 접혀진 expander에 넣기
        with st.expander("디버깅 정보 (클릭하여 펼치기)", expanded=False):
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

        # 처리 결과 요약 (디버깅 정보 expander에 포함)
        with st.expander("처리 결과 요약", expanded=False):
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