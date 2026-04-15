#!/usr/bin/env python3
"""
小说封面生成脚本
用于生成网文封面图片（600x800 番茄小说标准尺寸）

依赖：Pillow
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# 字体加载
# ---------------------------------------------------------------------------

def _load_fonts():
    """尝试加载系统字体，失败则回退到默认字体"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]
    title_font = ImageFont.load_default()
    author_font = ImageFont.load_default()

    for bold_path in font_paths:
        if "Bold" in bold_path and os.path.exists(bold_path):
            try:
                title_font = ImageFont.truetype(bold_path, 60)
                break
            except Exception:
                continue

    for regular_path in font_paths:
        if "Bold" not in regular_path and os.path.exists(regular_path):
            try:
                author_font = ImageFont.truetype(regular_path, 24)
                break
            except Exception:
                continue

    return title_font, author_font


# ---------------------------------------------------------------------------
# 核心生成逻辑
# ---------------------------------------------------------------------------

def generate_cover(title: str, author: str, background: str = None,
                   style: str = 'auto', output: str = None) -> str:
    """
    生成小说封面

    Args:
        title: 书名
        author: 作者名
        background: 背景图路径（可选）
        style: 风格（male/female/auto）
        output: 输出路径（可选，默认 cover_<title>.png）

    Returns:
        生成的封面图片路径
    """
    # 参数验证
    if not title or not title.strip():
        raise ValueError("书名不能为空")
    if not author or not author.strip():
        raise ValueError("作者名不能为空")
    if background and not os.path.exists(background):
        raise FileNotFoundError(f"背景图不存在: {background}")

    # 尺寸设置（番茄小说标准）
    WIDTH = 600
    HEIGHT = 800

    # 自动判断风格
    if style == 'auto':
        male_keywords = ['重生', '系统', '修仙', '战神', '狂', '霸', '王', '帝']
        style = 'male' if any(kw in title for kw in male_keywords) else 'female'

    # 创建画布
    if background and os.path.exists(background):
        img = Image.open(background).resize((WIDTH, HEIGHT))
    else:
        if style == 'male':
            img = Image.new('RGB', (WIDTH, HEIGHT), '#1a1a2e')
            draw = ImageDraw.Draw(img)
            for i in range(HEIGHT):
                color = f'#{hex(26 + i // 20)[2:]}1a2e'
                draw.line([(0, i), (WIDTH, i)], fill=color)
        else:
            img = Image.new('RGB', (WIDTH, HEIGHT), '#fff0f5')
            draw = ImageDraw.Draw(img)
            for i in range(HEIGHT):
                r = min(255, 255 - i // 10)
                g = min(255, 240 - i // 20)
                b = min(255, 245 - i // 15)
                draw.line([(0, i), (WIDTH, i)], fill=(r, g, b))

    draw = ImageDraw.Draw(img)
    title_font, author_font = _load_fonts()

    # 书名颜色
    title_color = '#FFD700' if style == 'male' else '#FF69B4'

    # 绘制书名（带描边）
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (WIDTH - title_width) // 2
    title_y = HEIGHT // 4

    for adj_x in range(-2, 3):
        for adj_y in range(-2, 3):
            draw.text((title_x + adj_x, title_y + adj_y), title,
                      font=title_font, fill='#000000')
    draw.text((title_x, title_y), title, font=title_font, fill=title_color)

    # 绘制作者名
    author_text = f'作者：{author}'
    author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
    author_width = author_bbox[2] - author_bbox[0]
    author_x = (WIDTH - author_width) // 2
    author_y = HEIGHT - 80
    draw.text((author_x, author_y), author_text,
              font=author_font, fill='#FFFFFF' if style == 'male' else '#8B4513')

    # 保存
    if output is None:
        safe_name = "".join(c for c in title if c.isalnum() or c in "._- ")[:30]
        output = f'cover_{safe_name}.png'

    output_dir = os.path.dirname(output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    img.save(output, quality=90)
    return output


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='生成小说封面')
    parser.add_argument('--title', required=True, help='书名')
    parser.add_argument('--author', required=True, help='作者名')
    parser.add_argument('--background', help='背景图路径')
    parser.add_argument('--style', choices=['male', 'female', 'auto'],
                        default='auto', help='风格')
    parser.add_argument('--output', help='输出路径')

    args = parser.parse_args()

    try:
        path = generate_cover(
            title=args.title,
            author=args.author,
            background=args.background,
            style=args.style,
            output=args.output
        )
        print(json.dumps({"status": "success", "output": path}, ensure_ascii=False))
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


# 需要导入 json 用于输出
import json

if __name__ == '__main__':
    main()
