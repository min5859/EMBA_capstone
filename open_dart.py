import streamlit as st
import requests
import pandas as pd
import os
import json

# API 키
DART_API_KEY = "a8c255f6ca79fa1027b047a35cdafe326360bddd"

# 기본 URL
BASE_URL = "https://opendart.fss.or.kr/api/"

def fetch_financial_statement(corp_code, year, report_code):
    """
    재무제표 데이터를 DART API에서 가져오기
    """
    endpoint = f"{BASE_URL}fnlttSinglAcnt.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": report_code
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "000":
            return data
        else:
            st.error(f"Error: {data['message']}")
    else:
        st.error("API 호출 실패")
    return None

def save_json(data, filename):
    """
    JSON 데이터를 로컬 파일로 저장
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    st.title("DART 재무제표 조회 및 저장")

    # 사용자 입력
    st.sidebar.header("옵션")
    corp_code = st.sidebar.text_input("기업 코드 (DART)", value="00126380")  # 삼성전자 예시
    year = st.sidebar.number_input("조회 연도", min_value=2000, max_value=2025, value=2023)
    report_code = st.sidebar.selectbox("보고서 종류", options=["1분기", "반기", "3분기", "사업보고서"], index=3)

    report_map = {
        "1분기": "11013",
        "반기": "11012",
        "3분기": "11014",
        "사업보고서": "11011"
    }

    report_code = report_map[report_code]

    # 데이터 조회
    if st.sidebar.button("조회"):
        st.write("재무제표 데이터를 불러오는 중...")
        data = fetch_financial_statement(corp_code, year, report_code)
        if data:
            st.write(f"{year}년 {corp_code} 재무제표 데이터")

            # JSON 데이터 표시
            st.json(data)

            # Pandas DataFrame 변환 및 표시
            if "list" in data:
                df = pd.DataFrame(data["list"])
                st.dataframe(df)

                # 데이터 시각화 예제 (매출액과 당기순이익)
                try:
                    df["thstrm_amount"] = pd.to_numeric(df["thstrm_amount"], errors="coerce")
                    df_filtered = df[df["account_nm"].isin(["매출액", "당기순이익"])]
                    st.bar_chart(df_filtered[["account_nm", "thstrm_amount"]].set_index("account_nm"))
                except Exception as e:
                    st.error(f"시각화 중 오류 발생: {e}")

            # 데이터 저장 기능
            st.markdown("### 데이터 저장")
            filename = f"{corp_code}_{year}_{report_code}.json"
            save_json(data, filename)  # 로컬 저장
            st.success(f"JSON 데이터가 로컬 파일로 저장되었습니다: {filename}")

            # 다운로드 버튼 제공
            st.download_button(
                label="JSON 파일 다운로드",
                data=json.dumps(data, ensure_ascii=False, indent=4),
                file_name=filename,
                mime="application/json"
            )

if __name__ == "__main__":
    main()
