#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说章节字数统计脚本（增强版）
统计每章的字数（字符数）和词数（中文分词）
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 尝试导入jieba分词库
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("警告: 未安装jieba分词库，词数统计功能将不可用")
    print("安装命令: pip install jieba")

# 中文字符Unicode范围
CHINESE_PATTERN = re.compile(
    r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf'
    r'\U0002f800-\U0002fa1f]'
)

# 标点符号模式（包括中文和英文标点）
PUNCTUATION_PATTERN = re.compile(
    r'[\s\u3000-\u303f\uff00-\uffef\u2000-\u206f\uff01-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65!,.?:;\'\"(){}\[\]<>@#$%&*+-=|\\/`~^]'
)

# 目标字数
TARGET_TOTAL = 300000
TARGET_PER_CHAPTER = 3750


def count_chinese_chars(text):
    """统计纯中文字符数量（不含标点和空格）"""
    matches = CHINESE_PATTERN.findall(text)
    return len(matches)


def count_words(text):
    """统计中文词数"""
    if not JIEBA_AVAILABLE:
        return 0

    # 移除标点符号和空格
    cleaned_text = PUNCTUATION_PATTERN.sub('', text)
    # 使用jieba分词
    words = jieba.lcut(cleaned_text)
    # 过滤掉空字符串和单个字符
    words = [w for w in words if len(w) > 1 or (w and CHINESE_PATTERN.match(w))]
    return len(words)


def extract_chapter_number(filename):
    """从文件名中提取章节号"""
    match = re.search(r'第(\d+)章', filename)
    if match:
        return int(match.group(1))
    return None


def count_chapters(directory):
    """统计目录下所有章节的字数和词数"""
    chapter_dir = Path(directory)

    if not chapter_dir.exists():
        print(f"错误: 目录不存在 - {directory}")
        return None

    chapters = {}

    # 遍历目录下的所有文件
    for file_path in chapter_dir.glob("*.md"):
        # 跳过索引文件和统计报告
        if "索引" in file_path.name or "字数统计" in file_path.name:
            continue

        chapter_num = extract_chapter_number(file_path.name)
        if chapter_num is None:
            continue

        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 统计中文字符数和词数
            char_count = count_chinese_chars(content)
            word_count = count_words(content)

            # 如果同一章节有多个文件，保留字数最多的
            if chapter_num not in chapters or char_count > chapters[chapter_num]['char_count']:
                chapters[chapter_num] = {
                    'filename': file_path.name,
                    'char_count': char_count,
                    'word_count': word_count,
                    'path': file_path
                }
        except Exception as e:
            print(f"错误: 读取文件 {file_path.name} 失败: {e}")

    return chapters


def generate_report(chapters):
    """生成详细统计报告"""
    if not chapters:
        print("错误: 没有找到章节文件")
        return

    # 按章节号排序
    sorted_chapters = sorted(chapters.items())

    total_chars = sum(info['char_count'] for info in chapters.values())
    total_words = sum(info['word_count'] for info in chapters.values())
    chapter_count = len(chapters)
    avg_chars = total_chars / chapter_count if chapter_count > 0 else 0
    avg_words = total_words / chapter_count if chapter_count > 0 else 0

    # 按卷分组（根据用户要求）
    volumes = {
        1: list(range(1, 21)),     # 第一卷: 1-20章
        2: list(range(21, 26)),    # 第二卷: 21-25章
        3: list(range(26, 46)),    # 第三卷: 26-45章
        4: list(range(46, 66)),    # 第四卷: 46-65章
        5: list(range(66, 81)),    # 第五卷: 66-80章
    }

    # 统计各卷字数
    volume_stats = {}
    for vol_num, vol_chapters in volumes.items():
        vol_chars = sum(chapters[ch]['char_count'] for ch in vol_chapters if ch in chapters)
        vol_count = sum(1 for ch in vol_chapters if ch in chapters)
        volume_stats[vol_num] = {
            'chars': vol_chars,
            'count': vol_count,
            'avg': vol_chars / vol_count if vol_count > 0 else 0
        }

    # 最长和最短的章节
    sorted_by_chars = sorted(chapters.items(), key=lambda x: x[1]['char_count'], reverse=True)
    longest = sorted_by_chars[:5]
    shortest = sorted_by_chars[-5:]

    # 完成度
    percentage = (total_chars / TARGET_TOTAL) * 100
    gap = TARGET_TOTAL - total_chars

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("                    小说章节字数统计报告（详细版）")
    report_lines.append("=" * 80)
    report_lines.append("")

    # 总体统计
    report_lines.append("【总体统计】")
    report_lines.append(f"  总章节数:    {chapter_count} 章")
    report_lines.append(f"  总字数:      {total_chars:,} 字（中文字符，不含标点）")
    if JIEBA_AVAILABLE:
        report_lines.append(f"  总词数:      {total_words:,} 词")
    report_lines.append(f"  平均每章:    {avg_chars:.1f} 字")
    if JIEBA_AVAILABLE:
        report_lines.append(f"  平均每章:    {avg_words:.1f} 词")
    report_lines.append(f"  目标字数:    {TARGET_TOTAL:,} 字")
    report_lines.append("")

    # 目标完成情况
    report_lines.append("【目标完成情况】")
    report_lines.append(f"  目标字数:    {TARGET_TOTAL:,} 字")
    report_lines.append(f"  完成度:      {percentage:.2f}%")
    if total_chars >= TARGET_TOTAL:
        report_lines.append(f"  状态:        ✓ 已达标")
        report_lines.append(f"  超出:        {total_chars - TARGET_TOTAL:,} 字")
    else:
        report_lines.append(f"  状态:        未达标")
        report_lines.append(f"  差距:        {gap:,} 字")
        report_lines.append(f"  约需:        {gap / TARGET_PER_CHAPTER:.1f} 章内容")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("")

    # 各卷统计
    report_lines.append("【各卷字数统计】")
    report_lines.append("")
    for vol_num in sorted(volumes.keys()):
        stats = volume_stats[vol_num]
        report_lines.append(f"第{vol_num}卷（{volumes[vol_num][0]}-{volumes[vol_num][-1]}章）:")
        report_lines.append(f"  章节数:     {stats['count']} 章")
        report_lines.append(f"  总字数:     {stats['chars']:,} 字")
        report_lines.append(f"  平均每章:   {stats['avg']:.1f} 字")
        report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("")

    # 最长的章节
    report_lines.append("【最长的章节（前5章）】")
    report_lines.append("")
    for i, (num, info) in enumerate(longest, 1):
        report_lines.append(f"  {i}. 第{num:3d}章: {info['char_count']:5d} 字 - {info['filename']}")
    report_lines.append("")

    # 最短的章节
    report_lines.append("【最短的章节（前5章）】")
    report_lines.append("")
    for i, (num, info) in enumerate(reversed(shortest), 1):
        report_lines.append(f"  {i}. 第{num:3d}章: {info['char_count']:5d} 字 - {info['filename']}")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("")

    # 每章详细统计
    report_lines.append("【各章节字数明细】")
    report_lines.append("")

    for vol_num, vol_chapters in volumes.items():
        report_lines.append(f"--- 第{vol_num}卷 ---")
        for ch_num in vol_chapters:
            if ch_num in chapters:
                info = chapters[ch_num]
                word_str = f" / {info['word_count']}词" if JIEBA_AVAILABLE else ""
                report_lines.append(f"  第{ch_num:3d}章: {info['char_count']:5d} 字{word_str} - {info['filename']}")
        report_lines.append("")

    report_lines.append("=" * 80)

    # 完成提示
    if total_chars >= TARGET_TOTAL:
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("                    *** 恭喜达成目标 ***")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("《小说作品》已完成300,000字目标！")
        report_lines.append("")
        report_lines.append(f"最终字数: {total_chars:,} 字")
        report_lines.append(f"完成度:   {percentage:.2f}%")
        report_lines.append(f"超出目标: {total_chars - TARGET_TOTAL:,} 字")
        report_lines.append("")
        report_lines.append("感谢您的坚持与努力，作品圆满完成！")
        report_lines.append("")
        report_lines.append("=" * 80)
    else:
        report_lines.append("")
        report_lines.append("【继续加油】")
        report_lines.append("")
        report_lines.append(f"  距离目标还需 {gap:,} 字")
        report_lines.append(f"  约需 {gap / TARGET_PER_CHAPTER:.1f} 章内容")
        report_lines.append("")
        report_lines.append("  坚持就是胜利，继续创作！")
        report_lines.append("")

    return "\n".join(report_lines)


def main():
    directory = r"D:\软件\Obsidian项目\test\小说作品\修改后章节"

    print("开始统计章节字数...")
    print(f"目录: {directory}")
    print("")

    chapters = count_chapters(directory)

    if chapters:
        report = generate_report(chapters)

        # 打印报告
        print(report)
        print("")

        # 保存报告到文件
        report_path = Path(directory) / "字数统计报告_详细.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"报告已保存到: {report_path}")

        # 另外保存一个markdown版本
        report_md_path = Path(directory) / "字数统计报告_详细.md"
        with open(report_md_path, 'w', encoding='utf-8') as f:
            f.write("# 小说章节字数统计报告（详细版）\n\n")
            f.write(report)
            f.write("\n")

        print(f"Markdown报告已保存到: {report_md_path}")

    else:
        print("错误: 未找到任何章节文件")


if __name__ == "__main__":
    main()
