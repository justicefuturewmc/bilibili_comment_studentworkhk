import matplotlib.pyplot as plt
import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')
from wordcloud import WordCloud

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def complete_working_wordcloud():
    """完整可工作的词云生成"""
    
    print("=== 完整词云生成 ===")
    
    try:
        # 1. 读取数据
        csv_file = "./词频.csv"
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"数据读取成功: {len(df)} 行")
        
        # 2. 创建词频字典
        word_freq = {}
        for i, (word, freq) in enumerate(zip(df['词语'], df['频次'])):
            if pd.notna(word) and pd.notna(freq):
                word_freq[str(word)] = int(freq)
            
            if i % 50 == 0 and i > 0:
                print(f"已处理 {i} 行数据...")
        
        print(f"有效词语: {len(word_freq)} 个")
        
        # 3. 显示前10个高频词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        print("前10个高频词:")
        for i, (word, freq) in enumerate(sorted_words, 1):
            print(f"  {i:2d}. {word}: {freq}")
        
        # 4. 配置WordCloud（使用最稳定的配置）
        wc = WordCloud(
            font_path='simhei.ttf',
            width=1200,
            height=800,
            max_words=100,           # 限制词语数量
            background_color='white',
            colormap='viridis',      # 使用viridis配色
            prefer_horizontal=0.9,   # 90%水平排列
            relative_scaling=0.3,    # 较小的相对缩放
            min_font_size=10,
            max_font_size=120,
            collocations=False,      # 禁用词语搭配
            normalize_plurals=False,
            repeat=False,
            include_numbers=False,
            min_word_length=1,
            mode='RGB',
            random_state=42,         # 固定随机种子
            scale=1
        )
        
        print("开始生成词云...")
        
        # 5. 使用 fit_words 方法（最稳定）
        wc.fit_words(word_freq)
        print("✅ 词云生成成功！")
        
        # 6. 保存图像
        save_dir = "./词云图结果"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        output_path = os.path.join(save_dir, '完整词云图.png')
        wc.to_file(output_path)
        print(f"✅ 词云图已保存: {output_path}")
        
        # 7. 显示文件信息
        file_size = os.path.getsize(output_path)
        print(f"文件大小: {file_size} 字节")
        
        print("🎉 词云生成完成！")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()

# 运行完整方案
complete_working_wordcloud()