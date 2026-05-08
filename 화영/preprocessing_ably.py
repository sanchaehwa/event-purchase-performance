import pandas as pd

#원본 데이터 파일 (에이블리)
file_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/평강/data/result/ably_products_final.csv"

df = pd.read_csv(file_path)

# 컬럼 삭제

df = df.drop(columns=[
    "sub_category",
    "tags",
    "description"
])

#저장 경로
output_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/ably_data.csv"

df.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)

print("에이블리 전처리 데이터 저장",output_path)