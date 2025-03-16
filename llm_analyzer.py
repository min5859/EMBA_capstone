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
        self.api_key = os.getenv("OPENAI_API_KEY", "")
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
        return os.getenv("OPENAI_API_KEY", "")
    
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
            
            # LLM 프롬프트 구성 - JSON 응답 요청
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
            2. 결과는 반드시 다음 JSON 구조로만 출력할 것:
            
            {{
              "company": "{company_name}",
              "ebitda_valuation": {{
                "conservative": 값(숫자만),
                "base": 값(숫자만),
                "optimistic": 값(숫자만)
              }},
              "dcf_valuation": {{
                "conservative": 값(숫자만),
                "base": 값(숫자만),
                "optimistic": 값(숫자만)
              }}
            }}
            
            중요: 결과는 반드시 위와 같은 JSON 구조로만 출력하세요. 설명이나 다른 텍스트는 포함하지 마세요.
            값은 단위 없이 숫자만 출력하세요.
            """
            
            # OpenAI API 호출
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
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
                model="gpt-4-turbo",
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
    
    @staticmethod
    def display_valuation_results(valuation_data):
        """Streamlit에서 기업가치 평가 결과 시각화
        
        Args:
            valuation_data (dict): 기업가치 평가 결과
        """
        if not valuation_data:
            st.error("기업가치 평가 데이터가 없습니다.")
            return
        
        company_name = valuation_data.get("company", "기업명 없음")
        ebitda_valuation = valuation_data.get("ebitda_valuation", {})
        dcf_valuation = valuation_data.get("dcf_valuation", {})
        
        st.subheader(f"{company_name} 기업가치 평가 결과")
        
        # 데이터 준비
        scenarios = ["보수적", "기본", "낙관적"]
        ebitda_values = [
            ebitda_valuation.get("conservative", 0) / 1000000,
            ebitda_valuation.get("base", 0) / 1000000,
            ebitda_valuation.get("optimistic", 0) / 1000000
        ]
        dcf_values = [
            dcf_valuation.get("conservative", 0) / 1000000,
            dcf_valuation.get("base", 0) / 1000000,
            dcf_valuation.get("optimistic", 0) / 1000000
        ]
        
        # 데이터프레임 생성
        df = pd.DataFrame({
            "시나리오": scenarios * 2,
            "평가방식": ["EBITDA"] * 3 + ["DCF"] * 3,
            "기업가치(조원)": ebitda_values + dcf_values
        })
        
        # 1. Plotly 차트 - 막대 그래프
        st.subheader("기업가치 평가 비교")
        
        fig = px.bar(
            df, 
            x="시나리오", 
            y="기업가치(조원)", 
            color="평가방식", 
            barmode="group",
            text_auto='.1f',
            color_discrete_map={"EBITDA": "#4472C4", "DCF": "#ED7D31"},
            title=f"{company_name} 기업가치 평가 (단위: 조원)"
        )
        
        fig.update_layout(
            font=dict(family="Arial", size=14),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. 평가 결과 테이블
        st.subheader("평가 방식별 기업가치 (단위: 백만원)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### EBITDA 방식")
            st.dataframe({
                "시나리오": scenarios,
                "기업가치": [
                    f"{ebitda_valuation.get('conservative', 0):,}",
                    f"{ebitda_valuation.get('base', 0):,}",
                    f"{ebitda_valuation.get('optimistic', 0):,}"
                ]
            })
        
        with col2:
            st.markdown("### DCF 방식")
            st.dataframe({
                "시나리오": scenarios,
                "기업가치": [
                    f"{dcf_valuation.get('conservative', 0):,}",
                    f"{dcf_valuation.get('base', 0):,}",
                    f"{dcf_valuation.get('optimistic', 0):,}"
                ]
            })
        
        # 3. 방사형 차트 - 시나리오별 평가 비교
        st.subheader("시나리오별 평가 비교")
        
        # 데이터 정규화 (최대값 기준)
        max_value = max(max(ebitda_values), max(dcf_values))
        ebitda_norm = [val / max_value for val in ebitda_values]
        dcf_norm = [val / max_value for val in dcf_values]
        
        # 방사형 차트 생성
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=ebitda_norm + [ebitda_norm[0]],
            theta=scenarios + [scenarios[0]],
            fill='toself',
            name='EBITDA 방식',
            line_color='#4472C4'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=dcf_norm + [dcf_norm[0]],
            theta=scenarios + [scenarios[0]],
            fill='toself',
            name='DCF 방식',
            line_color='#ED7D31'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 4. 요약 메트릭
        st.subheader("기업가치 평가 요약")
        
        col1, col2, col3 = st.columns(3)
        
        # 기본 시나리오 평균값
        avg_base = (ebitda_valuation.get("base", 0) + dcf_valuation.get("base", 0)) / 2
        
        with col1:
            st.metric(
                label="EBITDA 평균 기업가치", 
                value=f"{sum(ebitda_values) / 3:.2f} 조원",
                delta=f"{(ebitda_valuation.get('base', 0) - avg_base) / 1000000:.2f} 조원"
            )
        
        with col2:
            st.metric(
                label="DCF 평균 기업가치", 
                value=f"{sum(dcf_values) / 3:.2f} 조원",
                delta=f"{(dcf_valuation.get('base', 0) - avg_base) / 1000000:.2f} 조원"
            )
        
        with col3:
            st.metric(
                label="종합 평균 기업가치", 
                value=f"{(sum(ebitda_values) + sum(dcf_values)) / 6:.2f} 조원"
            )
        
        # 5. 원본 JSON 데이터 (접은 상태로 표시)
        with st.expander("원본 JSON 데이터"):
            st.json(valuation_data)


# Streamlit 애플리케이션 예시 코드
def streamlit_example():
    st.title("기업 가치 평가 시스템")
    
    # API 키 설정
    api_key = st.sidebar.text_input("OpenAI API 키", type="password")
    
    # 업로드된 파일이나 샘플 데이터로 분석
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
    
    if st.sidebar.button("기업가치 평가 실행"):
        with st.spinner("기업가치를 평가 중입니다..."):
            analyzer = LLMAnalyzer()
            if api_key:
                analyzer.set_api_key(api_key)
            
            result = analyzer.analyze_company_value(company_info, financial_data, industry_info)
            
            if result["status"] == "success":
                valuation_data = result.get("valuation_data")
                LLMAnalyzer.display_valuation_results(valuation_data)
            else:
                st.error(result["message"])
                if "raw_content" in result:
                    st.warning("LLM 응답 (JSON 파싱 불가):")
                    st.text(result["raw_content"])

if __name__ == "__main__":
    streamlit_example()