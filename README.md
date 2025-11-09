# GLEC AI Hub - Digital Tachograph AI Platform

## 🚨 중요 공지: 구현 무결성 표준

**본 프로젝트는 엄격한 구현 무결성 표준을 적용합니다. 모든 AI 어시스턴트와 개발자는 허위 구현 주장을 절대 금지하며, 실제 파일 존재 확인 후 참조, 실제 실행 후 결과 보고 원칙을 준수해야 합니다.**

**상세 내용**: [IMPLEMENTATION_INTEGRITY_STANDARDS.md](./IMPLEMENTATION_INTEGRITY_STANDARDS.md) 및 [CLAUDE.md](./CLAUDE.md) 필독

---

## 🚀 프로젝트 개요

**GLEC AI Hub**는 OpenAI GPT-OSS 기반의 차세대 디지털운행기록장치(DTG) AI 플랫폼입니다. 이 프로젝트는 AI 네이티브 개발 환경을 통해 최고의 생산성과 품질을 달성하기 위해 설계되었습니다.

## 🏗️ 프로젝트 구조

```
GLEC AI Hub/
├── .vscode/                    # Cursor IDE 설정
├── src/                        # 핵심 소스 코드
│   ├── core/                   # 핵심 모듈
│   ├── ai/                     # AI 모델 관련
│   ├── data/                   # 데이터 처리
│   └── utils/                  # 유틸리티
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── api/               # API 엔드포인트
│   │   ├── core/              # 백엔드 핵심
│   │   ├── models/            # 데이터 모델
│   │   └── services/          # 비즈니스 로직
│   ├── tests/                 # 백엔드 테스트
│   └── requirements.txt       # Python 의존성
├── frontend/                   # Next.js 프론트엔드
│   ├── src/
│   │   ├── components/        # React 컴포넌트
│   │   ├── pages/            # 페이지 컴포넌트
│   │   ├── hooks/            # 커스텀 훅
│   │   └── utils/            # 프론트엔드 유틸리티
│   ├── public/               # 정적 파일
│   └── package.json          # Node.js 의존성
├── docs/                      # 문서
├── scripts/                   # 빌드 스크립트
├── config/                    # 설정 파일
├── tests/                     # 통합 테스트
└── .github/                   # CI/CD 워크플로우
```

## 🛠️ 개발 환경 설정

### 필수 요구사항
- Python 3.9+
- Node.js 18+
- Cursor IDE (권장)

### 설치 및 실행

1. **백엔드 설정**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

2. **프론트엔드 설정**
```bash
cd frontend
npm install
npm run dev
```

## 🤖 AI 개발 워크플로우

이 프로젝트는 '바이브 코딩' 철학을 따르며, AI와 인간 개발자가 협업하여 최고의 결과를 달성합니다.

### AI 협업 8대 행동 강령
1. **AI는 당신의 '페어 프로그래머'이다**
2. **AI는 당신의 '첫 번째 코드 리뷰어'이다**
3. **AI는 당신의 '성실한 기록 사원'이다**
4. **AI는 당신의 '디지털 집사(Butler)'이다**
5. **AI는 당신의 '수석 기술 컨설턴트'이다**
6. **AI는 당신의 '무결점 태스크 매니저'이다**
7. **AI는 당신의 '영구적인 프로젝트 메모리'이다**
8. **인간은 '최종 결정권자'이자 '오케스트라 지휘자'이다**

## 📊 주요 기능

- **실시간 안전 추론**: <50ms 추론 시간, >94% 정확도
- **INT8 양자화**: 엣지 디바이스 최적화
- **OpenAI GPT-OSS 기반 AI**: 검증된 오픈소스 언어 모델 활용
- **자동화된 CI/CD**: GitHub Actions 기반
- **실시간 모니터링**: 성능 및 안전 지표 추적

## 🔒 보안 및 규정 준수

- 디지털운행기록장치 규정 준수
- 실시간 보안 검사
- 데이터 암호화 및 보호
- 감사 로그 자동화

## 📞 지원 및 연락처

- **프로젝트 소유자**: 프로젝트 아키텍트
- **문서 버전**: 1.0
- **최종 수정일**: 2025년 1월 7일

---

*이 프로젝트는 GLEC AI Hub의 차세대 디지털운행기록장치 AI 플랫폼을 위한 엔터프라이즈급 개발 환경입니다.*