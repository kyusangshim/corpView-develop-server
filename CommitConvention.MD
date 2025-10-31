1. type: 커밋의 종류 (필수)
가장 중요합니다. 이 커밋이 어떤 종류의 작업인지 나타냅니다.

feat: (Feature) 새로운 기능 추가

fix: (Bug fix) 버그 수정

refactor: (Refactor) 코드 리팩토링 (기능 변경 없이 코드 구조만 개선)

style: (Style) 코드 스타일 변경 (세미콜론 추가, 공백 수정 등)

docs: (Documentation) 문서 수정 (README.md, 주석 등)

test: (Test) 테스트 코드 추가 또는 수정

chore: (Chores) 빌드 설정, 패키지 매니저 설정, .gitignore 수정 등 기타 잡일

2. scope: 커밋의 범위 (선택)
이 커밋이 영향을 주는 코드의 범위나 위치를 나타냅니다. (선택 사항)

예: feat(login): ..., fix(user-api): ..., docs(readme): ...

프로젝트 구조에 맞게 정하면 됩니다. (예: user, auth, payment 등)

3. subject: 커밋 제목 (필수)
무엇을 했는지 50자 이내로 명확하게 요약합니다.

[규칙 1] 문장의 첫 글자는 대문자로 (영어의 경우)

[규칙 2] 문장 끝에 마침표(.)를 찍지 않습니다.

[규칙 3] 가장 중요: 영어로는 동사 원형으로 시작하고, 한글로는 '~함', '~ 수정', '~ 추가' 처럼 명사형으로 끝냅니다.

(O) feat: Add login feature (영어)

(O) feat: 로그인 기능 추가 (한글)

(X) feat: Log in feature added (X)

(X) feat: 로그인 기능을 추가했습니다. (X)