import pandas as pd
import json

# 读取JSON数据
with open('bilibili_comments_all.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 准备存储所有评论的列表
all_comments = []

# 处理每个主评论及其回复
for main_comment in data:
    # 添加主评论
    main_comment_data = {
        'comment_id': len(all_comments) + 1,
        'type': '主评论',
        'user_name': main_comment.get('user_name', ''),
        'user_level': main_comment.get('user_level', ''),
        'content': main_comment.get('content', ''),
        'like_count': main_comment.get('like_count', '0'),
        'publish_time': main_comment.get('publish_time', ''),
        'reply_to': '',
        'parent_comment_id': ''
    }
    all_comments.append(main_comment_data)

    parent_id = main_comment_data['comment_id']

    # 添加回复
    for reply in main_comment.get('replies', []):
        reply_data = {
            'comment_id': len(all_comments) + 1,
            'type': '回复',
            'user_name': reply.get('user_name', ''),
            'user_level': '',  # 回复通常没有用户等级
            'content': reply.get('content', ''),
            'like_count': reply.get('like_count', '0'),
            'publish_time': reply.get('publish_time', ''),
            'reply_to': '',  # 可以从内容中提取，但需要额外处理
            'parent_comment_id': parent_id
        }
        all_comments.append(reply_data)

# 创建DataFrame
df = pd.DataFrame(all_comments)

# 保存为Excel文件
df.to_excel('bilibili_comments.xlsx', index=False, engine='openpyxl')

print(f"已成功转换 {len(all_comments)} 条评论到Excel文件")
print(f"包含 {len(data)} 条主评论和 {len(all_comments) - len(data)} 条回复")

# 读取JSON数据
with open('repeatedcomment.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 准备存储所有评论的列表
all_comments = []

# 处理每个主评论及其回复
for main_comment in data:
    # 添加主评论
    main_comment_data = {
        'comment_id': len(all_comments) + 1,
        'type': '主评论',
        'user_name': main_comment.get('user_name', ''),
        'user_level': main_comment.get('user_level', ''),
        'content': main_comment.get('content', ''),
        'like_count': main_comment.get('like_count', '0'),
        'publish_time': main_comment.get('publish_time', ''),
        'reply_to': '',
        'parent_comment_id': ''
    }
    all_comments.append(main_comment_data)

    parent_id = main_comment_data['comment_id']

    # 添加回复
    for reply in main_comment.get('replies', []):
        reply_data = {
            'comment_id': len(all_comments) + 1,
            'type': '回复',
            'user_name': reply.get('user_name', ''),
            'user_level': '',  # 回复通常没有用户等级
            'content': reply.get('content', ''),
            'like_count': reply.get('like_count', '0'),
            'publish_time': reply.get('publish_time', ''),
            'reply_to': '',  # 可以从内容中提取，但需要额外处理
            'parent_comment_id': parent_id
        }
        all_comments.append(reply_data)

# 创建DataFrame
df = pd.DataFrame(all_comments)

# 保存为Excel文件
df.to_excel('repeatedcomment.xlsx', index=False, engine='openpyxl')

print(f"已成功转换 {len(all_comments)} 条评论到Excel文件")
print(f"包含 {len(data)} 条主评论和 {len(all_comments) - len(data)} 条回复")