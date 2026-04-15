#!/usr/bin/env python3
"""
小说封面生成脚本
用于生成网文封面图片
"""

import argparse
import os
from PIL import Image, ImageDraw, ImageFont

def generate_cover(title, author, background=None, style='auto', output=None):
    """
    生成小说封面
    
    Args:
        title: 书名
        author: 作者名
        background: 背景图路径（可选）
        style: 风格（male/female/auto）
        output: 输出路径（可选）
    
    Returns:
        生成的封面图片路径
    """
    
    # 尺寸设置（番茄小说标准）
    WIDTH = 600
    HEIGHT = 800
    
    # 判断风格
    if style == 'auto':
        # 根据书名关键词判断
        male_keywords = ['重生', '系统', '修仙', '战神', '狂', '霸', '王', '帝']
        style = 'male' if any(kw in title for kw in male_keywords) else 'female'
    
    # 创建画布
    if background and os.path.exists(background):
        # 使用背景图
        img = Image.open(background)
        img = img.resize((WIDTH, HEIGHT))
    else:
        # 使用默认背景
        if style == 'male':
            # 男频：深蓝色渐变
            img = Image.new('RGB', (WIDTH, HEIGHT), '#1a1a2e')
            draw = ImageDraw.Draw(img)
            for i in range(HEIGHT):
                color = f'#{hex(26 + i//20)[2:]}1a2e'
                draw.line([(0, i), (WIDTH, i)], fill=color)
        else:
            # 女频：浅粉色渐变
            img = Image.new('RGB', (WIDTH, HEIGHT), '#fff0f5')
            draw = ImageDraw.Draw(img)
            for i in range(HEIGHT):
                r = min(255, 255 - i//10)
                g = min(255, 240 - i//20)
                b = min(255, 245 - i//15)
                draw.line([(0, i), (WIDTH, i)], fill=(r, g, b))
    
    draw = ImageDraw.Draw(img)
    
    # 字体设置（使用默认字体，实际使用时可替换为自定义字体）
    try:
        # 尝试使用系统字体
        title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 60)
        author_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    except:
        # 使用默认字体
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    
    # 书名颜色
    title_color = '#FFD700' if style == 'male' else '#FF69B4'  # 金色或粉色
    
    # 计算书名位置（居中）
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (WIDTH - title_width) // 2
    title_y = HEIGHT // 4  # 上方1/4处
    
    # 绘制书名（带描边效果）
    # 描边
    for adj_x in range(-2, 3):
        for adj_y in range(-2, 3):
            draw.text((title_x + adj_x, title_y + adj_y), title, 
                     font=title_font, fill='#000000')
    # 正文
    draw.text((title_x, title_y), title, font=title_font, fill=title_color)
    
    # 计算作者名位置（居中，底部）
    author_bbox = draw.textbbox((0, 0), f'作者：{author}', font=author_font)
    author_width = author_bbox[2] - author_bbox[0]
    author_x = (WIDTH - author_width) // 2
    author_y = HEIGHT - 80  # 底部留白
    
    # 绘制作者名
    draw.text((author_x, author_y), f'作者：{author}', 
             font=author_font, fill='#FFFFFF' if style == 'male' else '#8B4513')
    
    # 保存
    if output is None:
        output = f'assets/novels/{title}_cover.jpg'
    
    # 确保目录存在
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    img.save(output, quality=90)
    print(f'封面已生成：{output}')
    
    return output

def main():
    parser = argparse.ArgumentParser(description='生成小说封面')
    parser.add_argument('--title', required=True, help='书名')
    parser.add_argument('--author', required=True, help='作者名')
    parser.add_argument('--background', help='背景图路径')
    parser.add_argument('--style', choices=['male', 'female', 'auto'], 
                       default='auto', help='风格')
    parser.add_argument('--output', help='输出路径')
    
    args = parser.parse_args()
    
    generate_cover(
        title=args.title,
        author=args.author,
        background=args.background,
        style=args.style,
        output=args.output
    )

if __name__ == '__main__':
    main()
