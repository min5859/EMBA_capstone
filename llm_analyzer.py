import os
import json
import logging
import re
import openai
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bridge.llm")

class LLMAnalyzer:
    """LLM을 이용한 기업 가치 분석을 위한 클래스"""
    
    def __init__(self):
        """LLM 분석기 클래스 초기화"""
        # OpenAI API 키 설정
        self.api_key = st.secrets["OPENAI_API_KEY"]
        if not self.api_key:
            logger.warning("OPENAI_API_KEY가 설정되지 않았습니다. 환경변수 또는 직접 입력이 필요합니다.")
        
        # OpenAI 클라이언트 설정
        if self.api_key:
            openai.api_key = self.api_key
    
    def set_api_key(self, api_key):
        """OpenAI API 키 설정
        
        Args:
            api_key (str): OpenAI API 키
        """
        self.api_key = api_key
        openai.api_key = api_key
    
    @staticmethod
    def get_api_key_from_env():
        """환경변수에서 OpenAI API 키 가져오기
        
        Returns:
            str: 환경변수에서 가져온 API 키, 없으면 빈 문자열
        """
        return st.secrets["OPENAI_API_KEY"]
    
    def analyze_company_value(self, company_info, financial_data, industry_info=None):
        """LLM을 이용한 기업 가치 분석
        
        Args:
            company_info (dict): 기업 기본 정보
            financial_data (dict): 재무 데이터
            industry_info (dict, optional): 산업 정보
            
        Returns:
            dict: LLM 분석 결과
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "OpenAI API 키가 설정되지 않았습니다."
            }
        
        try:
            # 회사 정보 추출
            company_name = company_info.get('corp_name', '알 수 없음')
            company_type = company_info.get('induty_code', '')
            company_business = company_info.get('induty', '알 수 없음')
            
            # 재무 데이터를 LLM에게 전달할 형태로 변환
            years = financial_data["years"]
            assets = financial_data["assets"]
            liabilities = financial_data["liabilities"]
            equity = financial_data["equity"]
            revenue = financial_data["revenue"]
            operating_profit = financial_data["operating_profit"]
            net_income = financial_data["net_income"]
            
            # 재무 정보 요약
            finances = []
            for i in range(len(years)):
                finances.append({
                    "연도": years[i],
                    "자산": assets[i],
                    "부채": liabilities[i],
                    "자본": equity[i],
                    "매출액": revenue[i],
                    "영업이익": operating_profit[i],
                    "당기순이익": net_income[i]
                })
            
            # 재무비율 계산에 필요한 데이터 준비
            ratios = []
            for i in range(len(years)):
                ratio = {}
                ratio["연도"] = years[i]
                
                # 부채비율
                if equity[i] > 0:
                    ratio["부채비율"] = round((liabilities[i] / equity[i]) * 100, 2)
                else:
                    ratio["부채비율"] = None
                
                # 영업이익률
                if revenue[i] > 0:
                    ratio["영업이익률"] = round((operating_profit[i] / revenue[i]) * 100, 2)
                else:
                    ratio["영업이익률"] = None
                
                # 순이익률
                if revenue[i] > 0:
                    ratio["순이익률"] = round((net_income[i] / revenue[i]) * 100, 2)
                else:
                    ratio["순이익률"] = None
                
                # ROE
                if equity[i] > 0:
                    ratio["ROE"] = round((net_income[i] / equity[i]) * 100, 2)
                else:
                    ratio["ROE"] = None
                
                # ROA
                if assets[i] > 0:
                    ratio["ROA"] = round((net_income[i] / assets[i]) * 100, 2)
                else:
                    ratio["ROA"] = None
                
                ratios.append(ratio)
            
            # 산업 정보
            sector_info = ""
            if industry_info:
                sector_info = f"""
                산업 관련 정보:
                산업군: {industry_info.get('sector', '알 수 없음')}
                경쟁사 평균 PER: {industry_info.get('avg_per', '알 수 없음')}
                경쟁사 평균 PBR: {industry_info.get('avg_pbr', '알 수 없음')}
                """
            
            # LLM 프롬프트 구성 - 설명이 포함된 JSON 응답 요청
            prompt = f"""
            # 기업 정보
            기업명: {company_name}
            업종 코드: {company_type}
            사업 영역: {company_business}
            
            # 재무 정보 (단위: 백만원)
            {json.dumps(finances, ensure_ascii=False, indent=2)}
            
            # 재무 비율
            {json.dumps(ratios, ensure_ascii=False, indent=2)}
            
            {sector_info}
            
            다음 형식으로 분석해주세요:
            
            1. EBITDA와 DCF 두가지 방식으로 보수적, 기본, 낙관적 3가지로 기업가치를 평가
            2. 결과는 다음 JSON 구조로 출력하되, 계산 과정과 가정에 대한 설명도 포함할 것:
            
            {{
              "company": "{company_name}",
              "ebitda_valuation": {{
                "conservative": 숫자값,
                "base": 숫자값,
                "optimistic": 숫자값
              }},
              "dcf_valuation": {{
                "conservative": 숫자값,
                "base": 숫자값,
                "optimistic": 숫자값
              }},
              "assumptions": {{
                "ebitda_multipliers": {{
                  "conservative": 숫자값,
                  "base": 숫자값,
                  "optimistic": 숫자값
                }},
                "discount_rates": {{
                  "conservative": 숫자값,
                  "base": 숫자값,
                  "optimistic": 숫자값
                }},
                "growth_rates": {{
                  "conservative": 숫자값,
                  "base": 숫자값,
                  "optimistic": 숫자값
                }},
                "terminal_growth_rates": {{
                  "conservative": 숫자값,
                  "base": 숫자값,
                  "optimistic": 숫자값
                }}
              }},
              "calculations": {{
                "average_ebitda": 숫자값,
                "ebitda_description": "EBITDA 계산 방식에 대한 설명",
                "dcf_description": "DCF 계산 방식에 대한 간략한 설명"
              }},
              "summary": "기업 가치 평가에 대한 종합적인 분석 및 설명"
            }}
            
            중요:
            1. 각 시나리오별 계산에 사용된 가정(EBITDA 승수, 할인율, 성장률 등)을 명확히 포함할 것
            2. EBITDA와 DCF 계산 방식에 대한 간략한 설명 포함
            3. JSON 구조는 유지하되, 각 항목에 대한 설명을 포함하여 결과의 신뢰성 제공
            4. 값은 단위 없이 숫자만 출력(예: 1000000, 275000000)
            """
            
            # OpenAI API 호출
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 기업 가치 평가와 M&A 분석을 전문으로 하는 금융 애널리스트입니다. JSON 형식으로 정확한 값만 출력합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            # 응답에서 JSON 결과 추출
            content = response.choices[0].message.content.strip()
            
            # JSON 형식 추출
            try:
                # 텍스트에서 JSON 부분만 추출
                json_pattern = r'({[\s\S]*})'
                match = re.search(json_pattern, content)
                
                if match:
                    json_str = match.group(1)
                    valuation_data = json.loads(json_str)
                else:
                    # 응답이 이미 JSON 형식이면 바로 로드
                    valuation_data = json.loads(content)
                
                return {
                    "status": "success",
                    "valuation_data": valuation_data
                }
            
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {str(e)}")
                return {
                    "status": "error",
                    "message": f"JSON 파싱 오류: {str(e)}",
                    "raw_content": content
                }
            
        except Exception as e:
            logger.error(f"LLM 분석 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"분석 중 오류가 발생했습니다: {str(e)}"
            }
    
    def analyze_investment_potential(self, company_info, financial_data, specific_question):
        """특정 질문에 대한 투자 잠재력 분석
        
        Args:
            company_info (dict): 기업 기본 정보
            financial_data (dict): 재무 데이터
            specific_question (str): 분석할 특정 질문
            
        Returns:
            dict: LLM 분석 결과
        """
        if not self.api_key:
            return {
                "status": "error",
                "message": "OpenAI API 키가 설정되지 않았습니다."
            }
        
        try:
            # 회사 정보 추출
            company_name = company_info.get('corp_name', '알 수 없음')
            
            # 재무 데이터를 LLM에게 전달할 형태로 변환
            years = financial_data["years"]
            assets = financial_data["assets"]
            liabilities = financial_data["liabilities"]
            equity = financial_data["equity"]
            revenue = financial_data["revenue"]
            operating_profit = financial_data["operating_profit"]
            net_income = financial_data["net_income"]
            
            # 재무 정보 요약
            finances = []
            for i in range(len(years)):
                finances.append({
                    "연도": years[i],
                    "자산": assets[i],
                    "부채": liabilities[i],
                    "자본": equity[i],
                    "매출액": revenue[i],
                    "영업이익": operating_profit[i],
                    "당기순이익": net_income[i]
                })
            
            # LLM 프롬프트 구성
            prompt = f"""
            다음은 {company_name} 기업의 재무 정보입니다:
            
            {json.dumps(finances, ensure_ascii=False, indent=2)}
            
            위 정보를 바탕으로 다음 질문에 답변해주세요:
            
            {specific_question}
            
            객관적인 데이터를 바탕으로 명확하게 답변해주세요.
            """
            
            # OpenAI API 호출
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 기업 재무 및 투자 분석을 전문으로 하는 애널리스트입니다. 데이터에 기반한 객관적인 답변을 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            # 응답에서 분석 결과 추출
            analysis = response.choices[0].message.content
            
            return {
                "status": "success",
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"LLM 분석 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"분석 중 오류가 발생했습니다: {str(e)}"
            }
