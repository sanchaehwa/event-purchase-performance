import pandas as pd

# 각 쇼핑몰 CSV 파일 경로
ably_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/ably_data.csv"
musinsa_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/musinsa_data.csv"
zigzag_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/zigzag_data.csv"
cm29_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/29cm_data.csv"
kream_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/kream_data.csv"


# CSV 읽기
df_ably = pd.read_csv(ably_path)
df_musinsa = pd.read_csv(musinsa_path)
df_zigzag = pd.read_csv(zigzag_path)
df_29cm = pd.read_csv(cm29_path)
df_kream = pd.read_csv(kream_path)

# 하나로 합치기
merged_df = pd.concat(
    [
        df_ably,
        df_musinsa,
        df_zigzag,
        df_29cm,
        df_kream
    ],
    ignore_index=True
)

# 저장
output_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/fashion_products.csv"

merged_df.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)

print("전체 데이터 병합 완료")
print("총 데이터 수:", len(merged_df))