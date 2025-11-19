from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import chromadb
import ollama
from sentence_transformers import SentenceTransformer
import os
import json
from typing import List, Dict
from datetime import datetime
import uvicorn

app = FastAPI(title="LGIT Archive")

# 임베딩 모델 초기화
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# ChromaDB 설정
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# 컬렉션 생성 또는 가져오기
try:
    collection = chroma_client.get_collection(name="teams_chat")
except:
    collection = chroma_client.create_collection(name="teams_chat")

# Ollama 모델 설정
OLLAMA_MODEL = "llama3.2:3b"  # 가볍고 성능 좋은 3B 모델


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """메인 페이지 - 채팅 UI"""
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LGIT Archive</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                width: 100%;
                max-width: 800px;
                height: 100vh;
                background: white;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .header {
                background: white;
                border-bottom: 1px solid #e0e0e0;
                padding: 20px 24px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .header h1 {
                font-size: 20px;
                font-weight: 500;
                color: #1a1a1a;
            }
            .upload-btn {
                background: #1a1a1a;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 400;
                transition: background 0.2s;
            }
            .upload-btn:hover {
                background: #333;
            }
            .chat-container {
                flex: 1;
                overflow-y: auto;
                padding: 24px;
                display: flex;
                flex-direction: column;
                gap: 16px;
                position: relative;
            }
            .message {
                max-width: 75%;
                padding: 12px 16px;
                border-radius: 4px;
                word-wrap: break-word;
                line-height: 1.5;
            }
            .user-message {
                align-self: flex-end;
                background: #1a1a1a;
                color: white;
            }
            .bot-message {
                align-self: flex-start;
                background: #f5f5f5;
                color: #1a1a1a;
            }
            .bot-message .source {
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid #e0e0e0;
                font-size: 12px;
                color: #666;
            }
            .input-container {
                padding: 16px 24px;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 8px;
            }
            .input-field {
                flex: 1;
                padding: 12px 16px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 15px;
                outline: none;
                transition: border-color 0.2s;
            }
            .input-field:focus {
                border-color: #1a1a1a;
            }
            .send-btn {
                padding: 12px 24px;
                background: #1a1a1a;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 400;
                transition: background 0.2s;
            }
            .send-btn:hover {
                background: #333;
            }
            .send-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .loading {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid #e0e0e0;
                border-top: 2px solid #1a1a1a;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            .loading-message {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .loading-dots {
                display: inline-flex;
                gap: 4px;
            }
            .loading-dots span {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #666;
                animation: bounce 1.4s ease-in-out infinite both;
            }
            .loading-dots span:nth-child(1) {
                animation-delay: -0.32s;
            }
            .loading-dots span:nth-child(2) {
                animation-delay: -0.16s;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes bounce {
                0%, 80%, 100% {
                    transform: scale(0);
                    opacity: 0.5;
                }
                40% {
                    transform: scale(1);
                    opacity: 1;
                }
            }
            #fileInput {
                display: none;
            }
            .chat-container.drag-over {
                background: #fafafa;
                border: 2px dashed #d0d0d0;
            }
            .drop-zone-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(250, 250, 250, 0.95);
                border: 2px dashed #666;
                display: none;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                font-weight: 400;
                color: #666;
                z-index: 10;
                pointer-events: none;
            }
            .chat-container.drag-over .drop-zone-overlay {
                display: flex;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>LGIT Archive</h1>
                <label class="upload-btn" for="fileInput">CSV 업로드</label>
                <input type="file" id="fileInput" accept=".csv" />
            </div>
            <div class="chat-container" id="chatContainer">
                <div class="drop-zone-overlay">CSV 파일을 여기에 드롭하세요</div>
                <div class="message bot-message">
                    CSV 파일을 업로드하여 시작하세요.
                </div>
            </div>
            <div class="input-container">
                <input type="text" class="input-field" id="userInput" placeholder="질문을 입력하세요..." />
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">전송</button>
            </div>
        </div>

        <script>
            const chatContainer = document.getElementById('chatContainer');
            const userInput = document.getElementById('userInput');
            const sendBtn = document.getElementById('sendBtn');
            const fileInput = document.getElementById('fileInput');

            // 엔터키로 전송
            userInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // 파일 업로드 함수
            async function uploadFile(file) {
                if (!file || !file.name.endsWith('.csv')) {
                    addMessage('CSV 파일만 업로드 가능합니다.', 'bot');
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);
                
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<div class="loading"></div>';
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    
                    if (response.ok) {
                        addMessage(`CSV 파일이 업로드되었습니다. (${result.total}개의 대화 저장됨)`, 'bot');
                    } else {
                        addMessage(`오류: ${result.detail}`, 'bot');
                    }
                } catch (error) {
                    addMessage(`오류: ${error.message}`, 'bot');
                } finally {
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = '전송';
                    fileInput.value = '';
                }
            }

            // 파일 입력 이벤트
            fileInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    await uploadFile(file);
                }
            });

            // 드래그 앤 드롭 이벤트
            chatContainer.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                chatContainer.classList.add('drag-over');
            });

            chatContainer.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                chatContainer.classList.remove('drag-over');
            });

            chatContainer.addEventListener('drop', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                chatContainer.classList.remove('drag-over');

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    await uploadFile(files[0]);
                }
            });

            // 페이지 전체에서 드래그 이벤트 방지 (기본 동작 방지)
            document.addEventListener('dragover', (e) => {
                e.preventDefault();
            });

            document.addEventListener('drop', (e) => {
                e.preventDefault();
            });

            async function sendMessage() {
                const question = userInput.value.trim();
                if (!question) return;

                addMessage(question, 'user');
                userInput.value = '';
                sendBtn.disabled = true;
                sendBtn.innerHTML = '<div class="loading"></div>';

                // 로딩 메시지 추가
                const loadingId = addLoadingMessage();

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ question: question })
                    });
                    const result = await response.json();
                    
                    // 로딩 메시지 제거
                    removeLoadingMessage(loadingId);
                    
                    if (response.ok) {
                        let messageHTML = result.answer;
                        if (result.sources && result.sources.length > 0) {
                            messageHTML += '<div class="source">';
                            messageHTML += '<strong>참조된 대화:</strong><br>';
                            result.sources.forEach((source, idx) => {
                                messageHTML += `${idx + 1}. ${source.question} (${source.user}, ${source.time})<br>`;
                            });
                            messageHTML += '</div>';
                        }
                        addMessage(messageHTML, 'bot');
                    } else {
                        addMessage(`오류: ${result.detail}`, 'bot');
                    }
                } catch (error) {
                    // 로딩 메시지 제거
                    removeLoadingMessage(loadingId);
                    addMessage(`오류: ${error.message}`, 'bot');
                } finally {
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = '전송';
                }
            }

            function addMessage(text, type) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}-message`;
                messageDiv.innerHTML = text;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                return messageDiv;
            }

            function addLoadingMessage() {
                const loadingId = 'loading-' + Date.now();
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message bot-message loading-message';
                messageDiv.id = loadingId;
                messageDiv.innerHTML = `
                    <div class="loading-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <span>답변을 생성하는 중...</span>
                `;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                return loadingId;
            }

            function removeLoadingMessage(loadingId) {
                const loadingMessage = document.getElementById(loadingId);
                if (loadingMessage) {
                    loadingMessage.remove();
                }
            }
        </script>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """CSV 파일 업로드 및 벡터 DB에 저장"""
    try:
        # CSV 파일 읽기
        contents = await file.read()
        df = pd.read_csv(
            pd.io.common.BytesIO(contents),
            encoding='utf-8',
            quotechar='"',
            escapechar='\\'
        )
        
        # 필수 컬럼 확인
        required_columns = ['time', 'user', 'question', 'answer']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400,
                detail=f"필수 컬럼이 없습니다. 필요한 컬럼: {required_columns}"
            )
        
        # 데이터 준비
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in df.iterrows():
            # 질문과 답변을 결합한 문서 생성
            combined_text = f"질문: {row['question']}\n답변: {row['answer']}"
            documents.append(combined_text)
            
            metadatas.append({
                "time": str(row['time']),
                "user": str(row['user']),
                "question": str(row['question']),
                "answer": str(row['answer'])
            })
            ids.append(f"chat_{idx}_{datetime.now().timestamp()}")
        
        # 임베딩 생성
        embeddings = embedding_model.encode(documents).tolist()
        
        # ChromaDB에 추가
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return JSONResponse({
            "message": "CSV 파일이 성공적으로 업로드되었습니다.",
            "total": len(documents)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: Dict):
    """질문에 대해 과거 대화 내용을 기반으로 답변 생성"""
    try:
        question = request.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="질문을 입력해주세요.")
        
        # 질문 임베딩
        query_embedding = embedding_model.encode([question]).tolist()[0]
        
        # 유사한 대화 검색 (상위 3개)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        # 검색된 대화 내용을 컨텍스트로 구성
        context = ""
        sources = []
        
        if results['documents'] and len(results['documents'][0]) > 0:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                context += f"과거 대화 {i+1}:\n질문: {metadata['question']}\n답변: {metadata['answer']}\n\n"
                sources.append({
                    "question": metadata['question'],
                    "answer": metadata['answer'],
                    "user": metadata['user'],
                    "time": metadata['time']
                })
        
        # Ollama를 사용한 답변 생성
        prompt = f"""다음은 과거 Teams 채팅방의 대화 내용입니다:

{context}

위의 과거 대화 내용을 참고하여 아래 질문에 대한 답변을 작성해주세요. 
과거 대화 내용에서 유사한 질문과 답변을 참고하되, 그대로 복사하지 말고 자연스럽게 재구성하여 답변해주세요.
만약 관련된 정보가 없다면, "과거 대화 내용에서 관련 정보를 찾을 수 없습니다."라고 답변해주세요.

질문: {question}

답변:"""

        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        
        answer = response['response'].strip()
        
        return JSONResponse({
            "answer": answer,
            "sources": sources
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

