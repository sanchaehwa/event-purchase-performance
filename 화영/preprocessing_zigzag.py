import re
import pandas as pd

#원본 파일
file_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/환희/likelion_data/zigzag_final_list.csv"
df = pd.read_csv(file_path)

#컬럼 순서 배치
columns_order = [
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

df = df[columns_order]

output_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/zigzag_data.csv"

df.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)

print("지그재그 전처리 데이터 저장 - 컬럼 순서 정렬 완료",output_path)
