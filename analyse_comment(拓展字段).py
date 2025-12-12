import pandas as pd
import re
from itertools import chain

# ================== 1. 配置路径 ==================
input_path = r"D:\workplace\merged_comments.csv"               # 原始数据
output_path = r"D:\workplace\merged_comments_with_labels.csv"  # 输出结果

# ================== 2. 词典定义 ==================
# 正向情感关键词表
positive_praise = [
    '好', '棒', '优秀', '精彩', '完美', '厉害', '强大', '牛逼', '牛批', '给力',
    '绝了', '神作', '经典', '顶级', '巅峰', '无敌', '超神', '惊艳', '震撼', '炸裂',
    '高质量', '高水平', '上乘', '精品', '佳作', '力作', '代表作', '封神', '天花板'
]

positive_love = [
    '喜欢', '爱', '热爱', '钟爱', '痴迷', '沉迷', '入迷', '着迷', '迷恋', '心水',
    '种草', '拔草', '宝藏', '心头好', '本命', '真爱', '最爱', '大爱', '超爱', '太爱了'
]

positive_support = [
    '支持', '鼓励', '加油', '坚持', '努力', '奋斗', '进步', '成长', '提升', '突破',
    '期待', '盼望', '希望', '祝福', '祝愿', '恭喜', '祝贺', '感谢', '感激', '感恩'
]

positive_emotion = [
    '开心', '快乐', '高兴', '喜悦', '愉快', '欢乐', '幸福', '满足', '舒服', '舒适',
    '轻松', '愉悦', '兴奋', '激动', '惊喜', '感动', '温暖', '温馨', '治愈', '解压'
]

positive_approval = [
    '可以', '不错', '挺好', '很好', '非常好', '特别好', '极好', '最好', '确实', '确实不错',
    '名副其实', '实至名归', '名不虚传', '不负众望', '值得', '划算', '实惠', '良心', '厚道'
]

positive_bilibili = [
    '一键三连', '素质三连', '收藏了', '投币了', '点赞了', '关注了', '追番', '追更',
    '打卡', '签到', '报道', '前排', '沙发', '板凳', '合影', '留念', '考古', '文艺复兴'
]

# 正向网络语
positive_internet = [
    'yyds', '绝绝子', '暴击', '杀疯了', '破防了', '泪目', '泪崩', '破大防',
    '磕到了', '嗑死了', '入股不亏', '神仙', '天选', '宝藏', '绝配'
]

# 正向表情
positive_emojis = [
    '😂', '😊', '😄', '😍', '🤣', '❤', '💕', '👍', '👏', '🎉',
    '🔥', '⭐', '🌟', '💯', '🙏', '🥰', '😘', '🤩', '🥳', '🙌'
]

# 负向情感关键词表
negative_criticism = [
    '差', '烂', '垃圾', '糟糕', '差劲', '不行', '不好', '不合格', '不及格', '失败',
    '失望', '绝望', '无语', '无奈', '气愤', '愤怒', '生气', '恼火', '恶心', '反感'
]

negative_quality = [
    '粗糙', '简陋', '廉价', '低质', '劣质', '山寨', '抄袭', '盗版', '侵权', '注水',
    '敷衍', '糊弄', '马虎', '粗糙', '简陋', '廉价感', '塑料感', '五毛特效'
]

negative_content = [
    '无聊', '枯燥', '乏味', '单调', '重复', '老套', '套路', '俗套', '狗血', '雷人',
    '尴尬', '违和', '突兀', '生硬', '牵强', '硬伤', 'bug', '漏洞', '穿帮'
]

negative_emotion = [
    '难过', '伤心', '悲伤', '痛苦', '难受', '郁闷', '压抑', '沉重', '焦虑', '担心',
    '害怕', '恐惧', '恐慌', '紧张', '烦躁', '急躁', '着急', '纠结', '矛盾', '困惑'
]

negative_rejection = [
    '反对', '抵制', '拒绝', '排斥', '讨厌', '厌恶', '嫌弃', '鄙视', '看不起', '不屑',
    '取消关注', '取关', '拉黑', '屏蔽', '举报', '投诉', '差评', '踩', '不推荐'
]

negative_bilibili = [
    '恰饭', '广告', '营销', '水视频', '拖更', '断更', '鸽', '太监', '烂尾', '腰斩',
    '限流', '下架', '删减', '和谐', '圣光', '暗牧', '马赛克', '打码'
]

# 负向网络语
negative_internet = [
    '就这', '就这？', '不会吧', '就离谱', '离大谱', '大无语', '栓Q', '芭比Q',
    '摆烂', '开摆', '寄', '凉凉', '翻车', '塌房', '雷', '避雷', '拔草'
]

# 负向表情
negative_emojis = [
    '😭', '😔', '😡', '🤮', '💔', '👎', '💢', '😤', '😫', '😩',
    '🙄', '😒', '🤢', '💩', '☹', '😠', '🤬', '😾', '💀', '🖕'
]

# 汇总正向/负向关键词（包含文字 + 网络语 + emoji）
positive_keywords = list({
    kw for kw in chain(
        positive_praise,
        positive_love,
        positive_support,
        positive_emotion,
        positive_approval,
        positive_bilibili,
        positive_internet,
        positive_emojis
    )
})

negative_keywords = list({
    kw for kw in chain(
        negative_criticism,
        negative_quality,
        negative_content,
        negative_emotion,
        negative_rejection,
        negative_bilibili,
        negative_internet,
        negative_emojis
    )
})

# emoji 总表（用于“是否含emoji”）
all_emoji_list = list(set(positive_emojis + negative_emojis))

# ================== 3. 工具函数 ==================
# 去掉 "回复 @xxx :" 前缀
reply_prefix_pattern = re.compile(r"^回复\s*@.*?[:：]\s*")

def clean_reply_prefix(text: str) -> str:
    cleaned = reply_prefix_pattern.sub("", text)
    return cleaned.strip()

def is_question(text: str) -> bool:
    if re.search(r"[？?]", text):
        return True
    for q in ['吗', '么', '嘛']:
        if q in text:
            return True
    return False

def is_strong(text: str) -> bool:
    return bool(re.search(r"[！!]", text))

# 是否含 emoji（用 unicode 范围 + 自定义表情表）
emoji_range_pattern = re.compile(
    r"[\U0001F300-\U0001F6FF\U0001F900-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]"
)

def has_emoji_func(text: str) -> bool:
    if emoji_range_pattern.search(text):
        return True
    return any(e in text for e in all_emoji_list)

def count_keywords(text: str, keywords) -> int:
    return sum(text.count(k) for k in keywords)

def list_keywords(text: str, keywords):
    """返回该文本中命中的关键词列表（去重，按原词排序后再拼接）。"""
    hits = [kw for kw in keywords if kw in text]
    # 去重并保持一个稳定顺序
    unique_hits = []
    for h in hits:
        if h not in unique_hits:
            unique_hits.append(h)
    return "、".join(unique_hits) if unique_hits else ""

# ================== 4. 读入数据 ==================
df = pd.read_csv(input_path, dtype=str, low_memory=False, encoding="utf-8")

if "content" not in df.columns:
    raise ValueError("当前表中没有 'content' 列，请检查输入文件。")

# 找 user_link 列（兼容 userlink）
if "user_link" in df.columns:
    user_col = "user_link"
elif "userlink" in df.columns:
    user_col = "userlink"
else:
    raise ValueError("当前表中没有 'user_link' 或 'userlink' 列，用于统计单用户评论次数。")

# ================== 5. 清洗 content ==================
df["content"] = df["content"].fillna("").astype(str)
df["content"] = df["content"].apply(clean_reply_prefix)

# ================== 6. 文本维度特征 ==================
# 1. 是否提问
df["is_question"] = df["content"].apply(is_question)

# 2. 是否强烈（感叹号）
df["is_strong"] = df["content"].apply(is_strong)

# 3. 是否含 emoji
df["has_emoji"] = df["content"].apply(has_emoji_func)

# 4 & 5. 正向关键词 & 次数 + 命中列表
df["pos_kw_count"] = df["content"].apply(lambda x: count_keywords(x, positive_keywords))
df["has_pos_kw"] = df["pos_kw_count"] > 0
df["pos_kw_list"] = df["content"].apply(lambda x: list_keywords(x, positive_keywords))

# 6 & 7. 负向关键词 & 次数 + 命中列表
df["neg_kw_count"] = df["content"].apply(lambda x: count_keywords(x, negative_keywords))
df["has_neg_kw"] = df["neg_kw_count"] > 0
df["neg_kw_list"] = df["content"].apply(lambda x: list_keywords(x, negative_keywords))

# 8. 是否长评（清洗后字数 ≥ 50）
LONG_THRESHOLD = 50
df["content_len"] = df["content"].str.len()
df["is_long_comment"] = df["content_len"] >= LONG_THRESHOLD

# ================== 7. 单用户评论次数分析（userlink >= 3） ==================
df[user_col] = df[user_col].fillna("").astype(str)

user_counts = df[user_col].value_counts(dropna=False)

df["user_comment_count"] = df[user_col].map(user_counts).fillna(0).astype(int)
# 一定是 >= 3 才算重复量用户
df["is_heavy_user_3plus"] = (df["user_comment_count"] >= 3).astype(int)

# ================== 8. 保存结果 ==================
df.to_csv(output_path, index=False, encoding="utf-8")
print("✅ 处理完成，结果已保存到：", output_path)
