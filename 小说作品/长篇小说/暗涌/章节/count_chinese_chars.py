#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说章节字数统计脚本
统计纯中文字符数量（不包括标点符号、空格、英文等）
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

# 中文字符Unicode范围
# 包括基本汉字、扩展A区、扩展B区等
CHINESE_PATTERN = re.compile(
    r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf'
    r'\U0002f800-\U0002fa1f]'
)

# 超虐章节
ANGSTY_CHAPTERS = [15, 18, 23, 40, 53]

# 目标字数
TARGET_TOTAL = 310000
TARGET_PER_CHAPTER = 3750


def count_chinese_chars(text):
    """统计纯中文字符数量"""
    matches = CHINESE_PATTERN.findall(text)
    return len(matches)


def extract_chapter_number(filename):
    """从文件名中提取章节号"""
    # 匹配 "第XX章" 格式
    match = re.search(r'第(\d+)章', filename)
    if match:
        return int(match.group(1))
    return None


def count_chapters(directory):
    """统计目录下所有章节的字数"""
    chapter_dir = Path(directory)

    if not chapter_dir.exists():
        print(f"错误: 目录不存在 - {directory}")
        return None

    # 存储同一章节号的多个版本
    chapter_versions = defaultdict(list)

    # 遍历目录下的所有文件
    for file_path in chapter_dir.glob("*.md"):
        # 跳过索引文件
        if "索引" in file_path.name or "字数统计" in file_path.name:
            continue

        chapter_num = extract_chapter_number(file_path.name)
        if chapter_num is None:
            continue

        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 统计中文字符数
            char_count = count_chinese_chars(content)
            chapter_versions[chapter_num].append({
                'filename': file_path.name,
                'count': char_count,
                'path': file_path
            })
        except Exception as e:
            print(f"错误: 读取文件 {file_path.name} 失败: {e}")

    # 对每个章节，选择字数最多的版本
    chapters = {}
    for chapter_num, versions in chapter_versions.items():
        # 按字数排序，选择最多的
        versions.sort(key=lambda x: x['count'], reverse=True)
        chapters[chapter_num] = versions[0]
        # 如果有多个版本，输出提示
        if len(versions) > 1:
            print(f"第{chapter_num}章有{len(versions)}个版本，选择字数最多的: {versions[0]['filename']} ({versions[0]['count']}字)")

    return chapters


def generate_report(chapters):
    """生成统计报告"""
    if not chapters:
        print("错误: 没有找到章节文件")
        return

    # 按章节号排序
    sorted_chapters = sorted(chapters.items())

    total_count = sum(info['count'] for info in chapters.values())
    chapter_count = len(chapters)
    avg_count = total_count / chapter_count if chapter_count > 0 else 0

    # 找出未达到目标的章节
    below_target = [(num, info) for num, info in sorted_chapters if info['count'] < TARGET_PER_CHAPTER]
    below_target.sort(key=lambda x: x[1]['count'])

    # 找出超虐章节
    angsty_chapters_found = [(num, info) for num, info in sorted_chapters if num in ANGSTY_CHAPTERS]

    # 差距和百分比
    gap = TARGET_TOTAL - total_count
    percentage = (total_count / TARGET_TOTAL) * 100

    # 生成报告
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("                        小说章节字数统计报告")
    report_lines.append("=" * 80)
    report_lines.append("")

    # 总体统计
    report_lines.append("【总体统计】")
    report_lines.append(f"  总章节数:    {chapter_count} 章")
    report_lines.append(f"  总字数:      {total_count:,} 字")
    report_lines.append(f"  平均每章:    {avg_count:.1f} 字")
    report_lines.append(f"  目标字数:    {TARGET_TOTAL:,} 字")
    report_lines.append("")
    report_lines.append("【目标完成情况】")
    if total_count >= TARGET_TOTAL:
        report_lines.append(f"  状态:        已达标 ✓")
        report_lines.append(f"  超出:        {total_count - TARGET_TOTAL:,} 字")
    else:
        report_lines.append(f"  状态:        未达标")
        report_lines.append(f"  差距:        {gap:,} 字")
    report_lines.append(f"  完成度:      {percentage:.2f}%")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")

    # 每章详细统计
    report_lines.append("【各章节字数明细】")
    report_lines.append("")

    # 按卷分组
    volumes = {
        1: list(range(1, 21)),    # 第1卷: 1-20章
        2: list(range(21, 45)),   # 第2卷: 21-44章
        3: list(range(45, 66)),   # 第3卷: 45-65章
        4: list(range(66, 81)),   # 第4卷: 66-80章
    }

    for vol_num, vol_chapters in volumes.items():
        report_lines.append(f"--- 第{vol_num}卷 ---")
        vol_total = 0
        vol_count = 0
        for ch_num in vol_chapters:
            if ch_num in chapters:
                info = chapters[ch_num]
                vol_total += info['count']
                vol_count += 1
                status = "  !" if info['count'] < TARGET_PER_CHAPTER else "   "
                report_lines.append(f"  第{ch_num:3d}章: {info['count']:5d} 字{status} {info['filename']}")
        if vol_count > 0:
            report_lines.append(f"  第{vol_num}卷小计: {vol_total:,} 字 ({vol_count}章)")
        report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("")

    # 超虐章节统计
    report_lines.append("【超虐章节字数统计】")
    report_lines.append("(第15、18、23、40、53章)")
    report_lines.append("")
    angsty_total = 0
    for num, info in angsty_chapters_found:
        angsty_total += info['count']
        report_lines.append(f"  第{num:3d}章: {info['count']:5d} 字 - {info['filename']}")
    report_lines.append(f"  超虐章节合计: {angsty_total:,} 字")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("")

    # 未达标章节
    if below_target:
        report_lines.append("【未达到3,750字目标的章节】")
        report_lines.append("")
        for num, info in below_target:
            deficit = TARGET_PER_CHAPTER - info['count']
            report_lines.append(f"  第{num:3d}章: {info['count']:5d} 字 (缺 {deficit:4d}字) - {info['filename']}")
        report_lines.append("")
        report_lines.append(f"  共 {len(below_target)} 章未达标，需补充 {sum(TARGET_PER_CHAPTER - info['count'] for _, info in below_target):,} 字")
        report_lines.append("")
    else:
        report_lines.append("【所有章节均已达到3,750字目标】")
        report_lines.append("")

    report_lines.append("=" * 80)

    # 完成报告
    if total_count >= TARGET_TOTAL:
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("                    *** 恭喜达成目标 ***")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("《小说作品》已完成310,000字目标！")
        report_lines.append("")
        report_lines.append(f"最终字数: {total_count:,} 字")
        report_lines.append(f"完成度:   {percentage:.2f}%")
        report_lines.append(f"超出目标: {total_count - TARGET_TOTAL:,} 字")
        report_lines.append("")
        report_lines.append("感谢您的坚持与努力，作品圆满完成！")
        report_lines.append("")
        report_lines.append("=" * 80)
    else:
        report_lines.append("")
        report_lines.append("【继续加油】")
        report_lines.append("")
        remaining = TARGET_TOTAL - total_count
        chapters_needed = remaining / TARGET_PER_CHAPTER
        report_lines.append(f"  距离目标还需 {remaining:,} 字")
        report_lines.append(f"  约需 {chapters_needed:.1f} 章内容")
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
        report_path = Path(directory) / "字数统计报告.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"报告已保存到: {report_path}")

        # 另外保存一个markdown版本
        report_md_path = Path(directory) / "字数统计报告.md"
        with open(report_md_path, 'w', encoding='utf-8') as f:
            f.write("# 小说章节字数统计报告\n\n")
            f.write(report)
            f.write("\n")

        print(f"Markdown报告已保存到: {report_md_path}")

    else:
        print("错误: 未找到任何章节文件")


if __name__ == "__main__":
    main()
