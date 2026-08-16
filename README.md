# smart-pot

AI 스마트 화분 프로토타입

> 프로젝트 배경(왜 만들었는지, 지금까지의 결정사항)은 [PROJECT.md](./PROJECT.md) 참고.

## 시작하기

```bash
# 1. 환경 세팅 (최초 1회)
uv sync

# 2. Ollama 로컬 LLM 서버 실행 (AI 스피커 기능용)
ollama serve
ollama pull gemma4   # config.py의 OLLAMA_MODEL과 동일한 모델

# 3. 실행
uv run python main.py
```

## 라즈베리파이 실환경

라즈베리파이에서는 모든 하드웨어 라이브러리가 자동으로 활성화됩니다.
일반 PC에서는 시뮬레이션 모드로 동작합니다.

## config.py 필수 설정

- `OLLAMA_HOST` — Ollama 서버 주소 (기본값 `http://localhost:11434`)
- `OLLAMA_MODEL` — 사용할 로컬 모델명 (기본값 `gemma4`)
- OpenAI API 키는 필요하지 않습니다 (AI 스피커는 로컬 Ollama + Whisper + Piper로 동작)
