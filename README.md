# Teams Chat RAG System

팀즈 채팅방의 과거 대화 내용을 활용하여 질문에 자동으로 답변하는 RAG (Retrieval-Augmented Generation) 시스템입니다.

## 기능

- 📁 CSV 파일 업로드: Teams 채팅 내용을 CSV 형식으로 업로드
- 🔍 유사 대화 검색: 벡터 임베딩을 사용한 과거 대화 내용 검색
- 💬 자동 답변 생성: Ollama를 사용한 로컬 LLM 기반 답변 생성
- 🎨 직관적인 채팅 UI: 웹 기반 채팅 인터페이스

## 요구사항

- Python 3.8 이상
- Ollama 설치 및 실행 중인 LLM 모델 (기본: llama3.2)

## 설치 방법

1. 의존성 패키지 설치:
```bash
pip install -r requirements.txt
```

2. Ollama 설치 및 모델 다운로드:
```bash
# Ollama 설치 (macOS)
brew install ollama

# Ollama 서비스 시작
ollama serve

# 모델 다운로드 (별도 터미널에서)
ollama pull llama3.2
```

## 실행 방법

```bash
python main.py
```

서버가 시작되면 브라우저에서 `http://localhost:8000`으로 접속하세요.

## CSV 파일 형식

CSV 파일은 다음 컬럼을 포함해야 합니다:

- `time`: 대화 시간
- `user`: 사용자 이름
- `question`: 질문 내용
- `answer`: 답변 내용

예시:
```csv
time,user,question,answer
2024-01-01 10:00:00,김철수,"프로젝트 일정은?",다음 주 월요일까지 완료 예정입니다.
2024-01-01 10:05:00,이영희,"회의 시간은?",오후 2시에 회의실에서 진행합니다.
```

## 사용 방법

1. 웹 인터페이스에 접속
2. "CSV 업로드" 버튼을 클릭하여 Teams 채팅 CSV 파일 업로드
3. 질문 입력 후 전송
4. 시스템이 과거 대화 내용을 검색하여 자동으로 답변 생성

## 프로젝트 구조

```
archive/
├── main.py              # FastAPI 백엔드 서버
├── requirements.txt     # Python 의존성
├── README.md           # 프로젝트 설명서
└── chroma_db/          # ChromaDB 데이터 저장 디렉토리 (자동 생성)
```

## 설정

Ollama 모델 변경:
`main.py` 파일에서 `OLLAMA_MODEL` 변수를 원하는 모델명으로 변경하세요.

```python
OLLAMA_MODEL = "llama3.2"  # 원하는 모델명으로 변경
```

## 기술 스택

- **백엔드**: FastAPI
- **벡터 DB**: ChromaDB
- **임베딩**: Sentence Transformers (한국어 모델)
- **LLM**: Ollama (로컬 실행)
- **프론트엔드**: HTML/CSS/JavaScript

## 라이선스

MIT License

