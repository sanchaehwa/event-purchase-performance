import pandas as pd

# 기존 CSV 파일 읽기
df = pd.read_csv("29cm_products.csv")

# category 컬럼이 비어있는 행 제거
df = df.dropna(subset=["category"])

# 공백 문자열도 제거
df = df[df["category"].astype(str).str.strip() != ""]

# 새로운 CSV 저장
df.to_csv(
    "29cm_products_filtered.csv",
    index=False,
    encoding="utf-8-sig"
)

print("빈 category 제거 완료")
print(f"남은 데이터 개수: {len(df)}")