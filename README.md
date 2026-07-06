# smart-pot

AI 스마트 화분 프로토타입

## 시작하기

```bash
# 1. 환경 세팅 (최초 1회)
uv sync

# 2. 실행
uv run python main.py
```

## 라즈베리파이 실환경

라즈베리파이에서는 모든 하드웨어 라이브러리가 자동으로 활성화됩니다.
일반 PC에서는 시뮬레이션 모드로 동작합니다.

## config.py 필수 설정

- `OPENAI_API_KEY` — OpenAI API 키 입력
