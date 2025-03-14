import streamlit as st
import logging
from bridge_app import BridgeApp

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bridge")

# 애플리케이션 실행
if __name__ == "__main__":
    app = BridgeApp()
    app.run()