import requests
import json
import pandas as pd
from datetime import datetime


def get_bilibili_weekly_videos(series_number):
    """
    获取指定期数的B站每周必看视频数据

    Args:
        series_number (int): 期数（如346期）

    Returns:
        pd.DataFrame: 包含视频基础信息的DataFrame
    """
    # 1. 构建API URL
    url = f"https://api.bilibili.com/x/web-interface/popular/series/one?number={series_number}"

    # 2. 设置请求头，模拟浏览器访问
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    cookies_dict = {
        "SESSDATA": "",
        "bili_jct": "",
        "buvid3": ""
    }

    try:
        # 3. 发送GET请求
        response = requests.get(url, headers=headers, timeout=20, cookies=cookies_dict)
        response.raise_for_status()  # 检查请求是否成功

        # 4. 解析JSON响应
        data = response.json()

        # 5. 检查API返回状态
        if data.get("code") != 0:
            print(f"API返回错误: {data.get('message')}")
            return None

        # 6. 提取视频列表
        videos = data["data"]["list"]

        # 7. 提取所需信息
        video_list = []
        for video in videos:
            video_info = {
                # 视频基础信息
                "期数": series_number,
                "标题": video.get("title", ""),
                "BV号": video.get("bvid", ""),
                "AV号": f"AV{video.get('aid', '')}",
                "视频链接": f"https://www.bilibili.com/video/{video.get('bvid', '')}",
                "时长": format_duration(video.get("duration", 0)),

                # UP主信息
                "UP主": video.get("owner", {}).get("name", ""),
                "UP主UID": video.get("owner", {}).get("mid", ""),
                "UP主主页": f"https://space.bilibili.com/{video.get('owner', {}).get('mid', '')}",

                # 统计信息
                "播放量": video.get("stat", {}).get("view", 0),
                "弹幕数": video.get("stat", {}).get("danmaku", 0),
                "评论数": video.get("stat", {}).get("reply", 0),
                "点赞数": video.get("stat", {}).get("like", 0),
                "收藏数": video.get("stat", {}).get("favorite", 0),
                "投币数": video.get("stat", {}).get("coin", 0),
                "分享数": video.get("stat", {}).get("share", 0),

                # 其他信息
                "封面图": video.get("pic", ""),
                "分区": video.get("tname", ""),
                "发布时间": format_timestamp(video.get("pubdate", 0))
            }
            video_list.append(video_info)

        # 8. 转换为DataFrame并保存
        df = pd.DataFrame(video_list)
        return df

    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None
    except KeyError as e:
        print(f"数据格式错误，缺少键: {e}")
        return None


def format_duration(seconds):
    """将秒数格式化为时:分:秒"""
    if seconds <= 0:
        return "00:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_timestamp(timestamp):
    """将时间戳格式化为可读时间"""
    if timestamp <= 0:
        return ""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def save_to_excel(df, series_number):
    """将数据保存到Excel文件"""
    filename = f"bilibili_weekly_{series_number}.xlsx"

    # 设置Excel写入选项
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    df.to_excel(writer, sheet_name=f'第{series_number}期', index=False)

    # 调整列宽
    worksheet = writer.sheets[f'第{series_number}期']
    for column in df:
        column_width = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)

    writer.close()
    print(f"数据已保存到文件: {filename}")
    return filename


def save_to_csv(df, series_number):
    """将数据保存到CSV文件"""
    filename = f"bilibili_weekly_{series_number}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"数据已保存到文件: {filename}")
    return filename


# 主程序
if __name__ == "__main__":
    # 获取第346期每周必看
    series_number = 346

    print(f"正在获取B站第{series_number}期每周必看数据...")
    df = get_bilibili_weekly_videos(series_number)

    if df is not None and not df.empty:
        # 显示基本信息
        print(f"成功获取第{series_number}期数据，共{len(df)}个视频")
        print("\n前5个视频信息：")
        print(df[["标题", "UP主", "播放量", "点赞数"]].head().to_string(index=False))

        # 显示统计摘要
        print(f"\n数据统计摘要：")
        print(f"总播放量: {df['播放量'].sum():,}")
        print(f"平均播放量: {df['播放量'].mean():,.0f}")
        print(f"最高播放量: {df['播放量'].max():,}")
        print(f"视频分区分布:")
        print(df["分区"].value_counts().head())

        # 保存数据
        save_option = input("\n是否保存数据？(1: Excel, 2: CSV, 其他: 不保存): ").strip()
        if save_option == "1":
            save_to_excel(df, series_number)
        elif save_option == "2":
            save_to_csv(df, series_number)
    else:
        print("获取数据失败")