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
        # 관심 있는 계정과목
        accounts = {
            # 자산 계정
            "자산": ["ifrs-full_Assets", "ifrs_Assets", "Assets", 
                     "ifrs-full_TotalAssets", "ifrs_TotalAssets", "TotalAssets"],
            "유동자산": ["ifrs-full_CurrentAssets", "ifrs_CurrentAssets", "CurrentAssets"],
            "당기자산": ["ifrs-full_CashAndCashEquivalents", "ifrs_CashAndCashEquivalents", "CashAndCashEquivalents"],
            "매출채권": ["ifrs-full_TradeAndOtherCurrentReceivables", "ifrs_TradeAndOtherCurrentReceivables",
                      "TradeAndOtherCurrentReceivables", "ifrs-full_TradeReceivables", "ifrs_TradeReceivables"],
            "재고자산": ["ifrs-full_Inventories", "ifrs_Inventories", "Inventories"],
            "비유동자산": ["ifrs-full_NoncurrentAssets", "ifrs_NoncurrentAssets", "NoncurrentAssets"],
            
            # 부채 계정
            "부채": ["ifrs-full_Liabilities", "ifrs_Liabilities", "Liabilities", 
                     "ifrs-full_TotalLiabilities", "ifrs_TotalLiabilities", "TotalLiabilities"],
            "유동부채": ["ifrs-full_CurrentLiabilities", "ifrs_CurrentLiabilities", "CurrentLiabilities"],
            "매입채무": ["ifrs-full_TradeAndOtherCurrentPayables", "ifrs_TradeAndOtherCurrentPayables",
                      "TradeAndOtherCurrentPayables", "ifrs-full_TradePayables", "ifrs_TradePayables"],
            "단기차입금": ["ifrs-full_ShorttermBorrowings", "ifrs_ShorttermBorrowings", "ShorttermBorrowings"],
            "비유동부채": ["ifrs-full_NoncurrentLiabilities", "ifrs_NoncurrentLiabilities", "NoncurrentLiabilities"],
            
            # 자본 계정
            "자본": ["ifrs-full_Equity", "ifrs_Equity", "Equity", 
                     "EquityAttributableToOwnersOfParent", "ifrs-full_EquityAttributableToOwnersOfParent",
                     "ifrs-full_TotalEquity", "ifrs_TotalEquity", "TotalEquity"],
            
            # 손익계산서 계정
            "매출액": ["ifrs-full_Revenue", "ifrs_Revenue", "Revenue", 
                      "ifrs-full_OperatingRevenue", "ifrs_OperatingRevenue", "OperatingRevenue", 
                      "ifrs-full_GrossOperatingProfit", "ifrs_GrossOperatingProfit", "GrossOperatingProfit",
                      "ifrs-full_Sales", "ifrs_Sales", "Sales"],
            "영업이익": ["ifrs-full_OperatingIncome", "ifrs_OperatingIncome", "OperatingIncome", 
                        "ifrs-full_ProfitLossFromOperatingActivities", "ifrs_ProfitLossFromOperatingActivities",
                        "ProfitLossFromOperatingActivities", "dart_OperatingIncomeLoss"],
            "당기순이익": ["ifrs-full_ProfitLoss", "ifrs_ProfitLoss", "ProfitLoss", 
                         "ifrs-full_ProfitLossAttributableToOwnersOfParent", "ifrs_ProfitLossAttributableToOwnersOfParent", 
                         "ProfitLossAttributableToOwnersOfParent", "ifrs-full_NetIncome", "ifrs_NetIncome", "NetIncome"]
        }

        # 결과 데이터 초기화
        result = {
            # 자산 항목
            "assets": [],
            "current_assets": [],
            "cash_and_equivalents": [],
            "trade_receivables": [],
            "inventories": [],
            "non_current_assets": [],
            
            # 부채 항목
            "liabilities": [],
            "current_liabilities": [],
            "trade_payables": [],
            "short_term_borrowings": [],
            "non_current_liabilities": [],
            
            # 자본 항목
            "equity": [],
            
            # 손익계산서 항목
            "revenue": [],
            "operating_profit": [],
            "net_income": [],
            "years": years
        }

        # 연도별 데이터 처리
        for idx, year_data in enumerate(financial_data_list):
            year_result = {
                # 자산 항목
                "assets": 0,
                "current_assets": 0,
                "cash_and_equivalents": 0,
                "trade_receivables": 0,
                "inventories": 0,
                "non_current_assets": 0,
                
                # 부채 항목
                "liabilities": 0,
                "current_liabilities": 0,
                "trade_payables": 0,
                "short_term_borrowings": 0,
                "non_current_liabilities": 0,
                
                # 자본 항목
                "equity": 0,
                
                # 손익계산서 항목
                "revenue": 0,
                "operating_profit": 0,
                "net_income": 0
            }

            if year_data is None or 'list' not in year_data:
                for key in year_result.keys():
                    result[key].append(0)
                continue

            fin_data = year_data['list']
            
            # 각 계정별로 값 찾기
            for fin_item in fin_data:
                account_id = fin_item.get('account_id')
                if account_id:
                    for key, id_list in accounts.items():
                        if account_id in id_list:
                            sj_div = fin_item.get('sj_div', '')
                            
                            # 재무상태표 항목
                            if sj_div == 'BS':
                                try:
                                    value = int(fin_item.get('thstrm_amount', '0').replace(',', ''))
                                    value_in_millions = value // 1000000  # 백만원 단위로 변환
                                    
                                    # 자산 항목
                                    if key == "자산" and year_result["assets"] == 0:
                                        year_result["assets"] = value_in_millions
                                    elif key == "유동자산" and year_result["current_assets"] == 0:
                                        year_result["current_assets"] = value_in_millions
                                    elif key == "당기자산" and year_result["cash_and_equivalents"] == 0:
                                        year_result["cash_and_equivalents"] = value_in_millions
                                    elif key == "매출채권" and year_result["trade_receivables"] == 0:
                                        year_result["trade_receivables"] = value_in_millions
                                    elif key == "재고자산" and year_result["inventories"] == 0:
                                        year_result["inventories"] = value_in_millions
                                    elif key == "비유동자산" and year_result["non_current_assets"] == 0:
                                        year_result["non_current_assets"] = value_in_millions
                                    
                                    # 부채 항목
                                    elif key == "부채" and year_result["liabilities"] == 0:
                                        year_result["liabilities"] = value_in_millions
                                    elif key == "유동부채" and year_result["current_liabilities"] == 0:
                                        year_result["current_liabilities"] = value_in_millions
                                    elif key == "매입채무" and year_result["trade_payables"] == 0:
                                        year_result["trade_payables"] = value_in_millions
                                    elif key == "단기차입금" and year_result["short_term_borrowings"] == 0:
                                        year_result["short_term_borrowings"] = value_in_millions
                                    elif key == "비유동부채" and year_result["non_current_liabilities"] == 0:
                                        year_result["non_current_liabilities"] = value_in_millions
                                    
                                    # 자본 항목
                                    elif key == "자본" and year_result["equity"] == 0:
                                        year_result["equity"] = value_in_millions
                                        
                                except (ValueError, TypeError):
                                    pass
                            
                            # 손익계산서 항목
                            elif sj_div == 'CIS' or sj_div == 'IS':
                                try:
                                    value = int(fin_item.get('thstrm_amount', '0').replace(',', ''))
                                    value_in_millions = value // 1000000
                                    
                                    if key == "매출액" and year_result["revenue"] == 0:
                                        year_result["revenue"] = value_in_millions
                                    elif key == "영업이익" and year_result["operating_profit"] == 0:
                                        year_result["operating_profit"] = value_in_millions
                                    elif key == "당기순이익" and year_result["net_income"] == 0:
                                        year_result["net_income"] = value_in_millions
                                except (ValueError, TypeError):
                                    pass

            # 연도별 결과 추가
            for key, value in year_result.items():
                result[key].append(value)

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