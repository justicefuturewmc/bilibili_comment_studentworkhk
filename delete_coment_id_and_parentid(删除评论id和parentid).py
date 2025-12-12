import os
import pandas as pd

# === 配置你的 CSV 文件夹路径 ===
folder_path = r"./csv"   # ← 记得改成你的路径

# === 需要删除的列 ===
cols_to_drop = ["comment_id", "parent_id", "user_level"]

for file in os.listdir(folder_path):
    if file.lower().endswith(".csv"):
        file_path = os.path.join(folder_path, file)
        print(f"Processing: {file}")

        try:
            # 读取CSV
            df = pd.read_csv(file_path, dtype=str, encoding="utf-8", low_memory=False)

            # 删除列（如果存在）
            df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors="ignore")

            # 处理 like_count 列：填充空值为0
            if "like_count" in df.columns:
                df["like_count"] = df["like_count"].fillna("0")   # 填补 NaN
                df["like_count"] = df["like_count"].replace("", "0")  # 填补空字符串

            # 覆盖保存
            df.to_csv(file_path, index=False, encoding="utf-8")
            print(f" → Done\n")

        except Exception as e:
            print(f"!!! Error processing {file}: {e}\n")

print("✔ All files processed.")
