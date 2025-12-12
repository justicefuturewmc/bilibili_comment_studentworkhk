import pandas as pd
import torch
from transformers import BertTokenizer, BertForSequenceClassification

# =========================
# 0. 基本配置（按需修改）
# =========================
INPUT_CSV  = "merged_comments_with_labels.csv"            # 输入文件
OUTPUT_CSV = "merged_comments_with_model_sentiment.csv"   # 输出文件
TEXT_COL   = "content"                                    # 评论文本列名

MODEL_NAME = "IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment"
BATCH_SIZE = 1024           # 批大小
MAX_LEN    = 128          # 最大序列长度

POS_THRESH_HIGH = 0.65    # > 0.65 判定为正向
POS_THRESH_LOW  = 0.35    # < 0.35 判定为负向

# =========================
# 1. 载入模型
# =========================
print(">>> 正在加载模型和分词器...")
tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
model = BertForSequenceClassification.from_pretrained(MODEL_NAME)

num_labels = model.config.num_labels
print(f">>> 模型标签数 num_labels = {num_labels}")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()
print(f">>> 模型已加载，使用设备：{device}")

# =========================
# 2. 读取数据
# =========================
df = pd.read_csv(INPUT_CSV, dtype=str, low_memory=False)
if TEXT_COL not in df.columns:
    raise ValueError(f"找不到文本列 '{TEXT_COL}'，当前列有：{list(df.columns)}")

df[TEXT_COL] = df[TEXT_COL].fillna("").astype(str)

positive_probs = [None] * len(df)
sentiments = [None] * len(df)

# =========================
# 3. 批量推理
# =========================
print(f">>> 开始情感推理，共 {len(df)} 条评论...")

for start in range(0, len(df), BATCH_SIZE):
    end = min(start + BATCH_SIZE, len(df))
    batch_texts = df[TEXT_COL].iloc[start:end].tolist()

    # 分词编码
    encoded = tokenizer(
        batch_texts,
        padding=True,
        truncation=True,
        max_length=MAX_LEN,
        return_tensors="pt"
    )

    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits              # [batch, num_labels]
        probs = torch.softmax(logits, dim=-1)

        if num_labels == 2:
            # 二分类：假设 index 0 = negative, index 1 = positive
            pos_tensor = probs[:, 1]        # 正向概率
            pos_list = pos_tensor.cpu().tolist()

            # 根据概率手动映射到 0/1/2
            batch_positive_prob = []
            batch_sentiment = []
            for p in pos_list:
                batch_positive_prob.append(float(p))
                if p >= POS_THRESH_HIGH:
                    s = 2   # 正面
                elif p <= POS_THRESH_LOW:
                    s = 0   # 负面
                else:
                    s = 1   # 中性
                batch_sentiment.append(s)

        elif num_labels == 3:
            # 三分类：假设 0=负面,1=中性,2=正面
            pos_tensor = probs[:, 2]
            batch_positive_prob = pos_tensor.cpu().tolist()
            batch_sentiment = torch.argmax(probs, dim=-1).cpu().tolist()
        else:
            raise ValueError(f"不支持的 num_labels={num_labels}，目前只处理 2 类或 3 类情感模型。")

    # 写回结果
    for i, idx in enumerate(range(start, end)):
        positive_probs[idx] = float(batch_positive_prob[i])
        sentiments[idx] = int(batch_sentiment[i])

    if (start // BATCH_SIZE) % 50 == 0 or end == len(df):
        print(f"    已处理 {end}/{len(df)} 条")

print(">>> 推理完成，正在写入新列...")

# =========================
# 4. 保存结果
# =========================
df["positive_prob"] = positive_probs   # 0.0 ~ 1.0
df["sentiment"] = sentiments          # 0=负面,1=中性,2=正面

df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
print(f">>> 已生成新文件：{OUTPUT_CSV}")
