import pandas as pd

# CSV 파일 읽기
df = pd.read_csv("29cm_products.csv")

# 제거할 컬럼 삭제
drop_columns = ["tags", "description"]

for col in drop_columns:
    if col in df.columns:
        df = df.drop(columns=[col])

# 숫자 컬럼 결측값 0 처리
numeric_columns = [
    "discount_rate",
    "rating",
    "review_count"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].fillna(0)
        df[col] = df[col].replace("", 0)
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# int 변환
for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].astype(int)

# 원하는 컬럼 순서
ordered_columns = [
    "product_name",
    "brand",
    "category",
    "price",
    "discount_rate",
    "rating",
    "review_count",
    "image_url",
    "source",
    "source_url"
]

# 존재하는 컬럼만 선택
existing_columns = [col for col in ordered_columns if col in df.columns]

df = df[existing_columns]

# 저장
output_file = "29cm_products_processed.csv"

df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

print("전처리 완료")
print(f"저장 파일: {output_file}")
print(df.head())