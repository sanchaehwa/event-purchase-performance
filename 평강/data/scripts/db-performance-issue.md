---
name: DB 성능 비교 분석
about: 이슈 템플릿
title: '[Feature] MariaDB / PostgreSQL / MySQL / MongoDB 쇼핑몰 데이터 성능 비교'
labels: feature
assignees: ''
---

## 구현할 기능

각자 담당 쇼핑몰 데이터를 적재 후 MariaDB / PostgreSQL / MySQL / MongoDB 4개 DB 쿼리 성능 비교 및 적합 DB 판단 근거 도출

## 목적

1만건 쇼핑몰 데이터 기준으로 RDB 간 성능 차이 및 RDB vs NoSQL 성능 차이를 측정하고,
쿼리 패턴별 어떤 DB가 적합한지 데이터 기반으로 판단한다

## 세부 작업

### [ 환경 세팅 ]

- [ ] Docker Compose로 MariaDB / PostgreSQL / MySQL / MongoDB 환경 구성
- [ ] RDB 3개 동일 테이블 스키마 설계 및 적용
- [ ] MongoDB 컬렉션 구조 설계
- [ ] 1만건 bulk insert 스크립트 작성 및 적재
- [ ] 매 테스트 전 DB 캐시 초기화 스크립트 작성
- [ ] 적재 완료 확인 및 환경 검수

### [ 성능 테스트 ]

**측정 기준**

| 항목 | 기준 |
|---|---|
| 워밍업 | 10회 실행 후 결과 제외 |
| 본 측정 | 100회 실행 |
| 측정 지표 | 평균 / 최솟값 / 최댓값 / 표준편차 (ms) |
| 캐시 | 매 테스트 전 DB 캐시 초기화 |

**테스트 항목**

- [ ] 단순 조회 - 상품 ID 단건 조회
- [ ] 필터 조회 - 카테고리 + 가격 범위
- [ ] 정렬 조회 - 가격 낮은순 / 리뷰 많은순
- [ ] 집계 쿼리 - 브랜드별 평균가격 / 카테고리별 상품 수
- [ ] 복합 조건 - 카테고리 + 브랜드 + 가격 + 정렬 동시
- [ ] 인덱스 적용 전후 성능 비교
- [ ] JOIN vs Lookup 성능 비교 (RDB vs MongoDB)
- [ ] 트랜잭션 처리 비교 (RDB vs MongoDB)

### [ 결과 정리 ]

- [ ] DB별 쿼리 유형별 응답시간 비교표 작성 (평균 / 최솟값 / 최댓값 / 표준편차)
- [ ] 인덱스 전후 성능 변화 정리
- [ ] RDB 간 성능 비교 결과 정리 (MariaDB / PostgreSQL / MySQL)
- [ ] RDB vs MongoDB 성능 및 정합성 비교 결과 정리
- [ ] 쿼리 패턴별 적합 DB 선택 근거 정리
- [ ] 최종 발표 자료 작성
