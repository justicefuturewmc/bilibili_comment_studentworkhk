import os
import pandas as pd
import re

# === CSV 文件夹路径 ===
folder_path = r"D:\workplace\csv"  # ← 修改为你的路径

# === 输出文件 ===
output_path = r"D:\workplace\merged_comments.csv"

# 视频ID的正则（匹配 BV 开头 + 任意字符）
video_id_pattern = re.compile(r"BV[a-zA-Z0-9]+")

all_data = []  # 用来存放所有文件的数据

for file in os.listdir(folder_path):
    if file.lower().endswith(".csv"):

        # 提取视频ID
        match = video_id_pattern.search(file)
        video_id = match.group(0) if match else "UNKNOWN"

        file_path = os.path.join(folder_path, file)
        print(f"Processing: {file} | video_id = {video_id}")

        try:
            # 读取 CSV
            df = pd.read_csv(file_path, dtype=str, encoding="utf-8", low_memory=False)

            # 新增 video_id 字段
            df["video_id"] = video_id

            # 加入列表
            all_data.append(df)

        except Exception as e:
            print(f"!!! Error reading {file}: {e}")

# === 合并所有文件 ===
if all_data:
    merged_df = pd.concat(all_data, ignore_index=True)
    merged_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n✔ All files merged successfully!")
    print(f"✔ Output saved to: {output_path}")
else:
    print("No CSV files found.")
