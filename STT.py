import whisper

# 모델 로드
model = whisper.load_model("medium")

# 음성 파일 변환
result = model.transcribe(".m4a", language="ko")

# 결과 출력
print(result["text"])
