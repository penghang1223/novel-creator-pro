#!/usr/bin/env python3
"""
小说质检脚本 v1.0
适配《重生之我在大唐当女皇》
基于企业级10维度评分框架

用法：
  python3 novel_check.py 第四十二章-崔善病重.md
  python3 novel_check.py --all          # 扫描全部章节
  python3 novel_check.py --batch ch42 ch43 ch44  # 批量检查
"""

import os
import re
import json
import glob
import sys
from pathlib import Path

# ============================================================
# 配置
# ============================================================

BASE_DIR = '/Users/narain/.openclaw/workspace-jinghong/重生之我在大唐当女皇/'

# 禁词表
FORBIDDEN_WORDS = {
    # 纪检术语
    '纪检': '改为"官府/朝堂"',
    '纪委': '改为"朝廷/官署"',
    '监察系统': '改为"政府办公室"',
    '纪律审查': '改为"文秘材料"',
    '机关单位': '改为"官府/衙门"',
    '工作审查': '改为"文秘材料"',
    # 历史错误
    '魏征': '改为"崔善"',
    '龙井': '唐代名茶：蒙顶黄芽/阳羡茶/顾渚紫笋',
    '妖术': '改为"巫蛊/厌胜/邪术"',
    # AI味词
    '说到底': '删除或改写',
    '顿时': '改为具体动作',
    '不知不觉': '删除',
    '不禁': '改为具体动作',
    '恍然大悟': '改为具体反应',
    '殊不知': '删除',
    '说来也巧': '删除',
    '可想而知': '删除',
    '不言而喻': '删除',
}

# 爽点关键词
PAYOFF_SIGNALS = ['赢了', '反转', '揭穿', '打脸', '没想到', '竟然', '原来',
                  '真相', '暴露', '崩溃', '落败', '失败', '废为庶人']
TENSION_SIGNALS = ['怎么办', '紧张', '危险', '死', '暴露', '来不及', '完了',
                   '败了', '逃', '躲', '藏', '杀']
BUILDUP_SIGNALS = ['暗中', '秘密', '计划', '布局', '准备', '安排', '谋划',
                   '等待', '忍耐', '克制']

# 角色行为白名单
CHARACTER_BEHAVIORS = {
    '李昭玥': ['冷静', '分析', '布局', '利用', '护短', '忍耐', '观察',
               '思考', '判断', '微笑', '沉默', '算计'],
    '萧景寒': ['沉默', '保护', '忠诚', '克制', '握刀', '站岗', '军',
               '铠甲', '眼神', '坚定'],
}

# 角色禁行（人设崩塌检测）——精确匹配，避免误报
CHARACTER_FORBIDDEN = {
    '李昭玥': ['大哭大闹', '歇斯底里', '跪下求饶', '放弃抵抗'],
    '萧景寒': ['背叛公主', '哈哈大笑', '油嘴滑舌'],
}

# 封号一致性（已知问题）
WRONG_TITLES = {
    '长乐': '第3章前→"十七公主"；第3章后→"昭玥公主"',
    '清河': '应为"萧景寒"或"萧将军"',
}

# ============================================================
# 工具函数
# ============================================================

def load_chapter(filepath):
    """读取章节内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def get_chapter_info(filepath):
    """获取章节编号和标题"""
    fname = os.path.basename(filepath)
    match = re.match(r'第(.+)章-(.+)\.md', fname)
    if match:
        return match.group(1), match.group(2)
    return None, fname

# ============================================================
# 8维度检测
# ============================================================

def check_forbidden_words(content):
    """维度8子项：禁词检测（影响可读性）"""
    issues = []
    lines = content.split('\n')
    for word, fix in FORBIDDEN_WORDS.items():
        for i, line in enumerate(lines, 1):
            if word in line:
                issues.append({
                    'type': 'forbidden_word',
                    'word': word,
                    'line': i,
                    'fix': fix,
                    'severity': 'high' if word in ['纪检','纪委','监察系统','魏征','龙井','妖术'] else 'medium'
                })
    return issues

def check_dash_density(content):
    """维度8子项：破折号密度"""
    dash_count = content.count('——')
    total = len(content)
    if total == 0:
        return []
    density = dash_count / total * 100
    if density > 5:
        return [{
            'type': 'dash_density',
            'value': round(density, 1),
            'limit': 5,
            'severity': 'high' if density > 10 else 'medium'
        }]
    return []

def check_time_place_opening(content):
    """维度8子项：时间+地点开头（150字定律）"""
    # Remove markdown header
    clean = re.sub(r'^# 第.*章.*\n', '', content).strip()
    first_150 = clean[:150]
    if re.search(r'贞观.{1,3}年.{1,8}月.{1,5}日.{0,20}。', first_150):
        return [{
            'type': 'time_place_opening',
            'severity': 'high',
            'fix': '前150字用动作/感官/悬念开场'
        }]
    return []

def check_payoff(content):
    """维度1：爽点达成度（30分）"""
    has_payoff = any(s in content for s in PAYOFF_SIGNALS)
    has_tension = any(s in content for s in TENSION_SIGNALS)
    has_buildup = any(s in content for s in BUILDUP_SIGNALS)

    if has_payoff and has_tension and has_buildup:
        score = 27  # 强烈爽感
    elif has_payoff and has_tension:
        score = 24
    elif has_payoff:
        score = 20
    elif has_tension:
        score = 15  # 只压抑不释放
    else:
        score = 8   # 无爽点

    issues = []
    if not has_payoff:
        issues.append({'type': 'no_payoff', 'severity': 'high', 'fix': '需要一个爽点时刻'})
    if has_tension and not has_payoff:
        issues.append({'type': 'tension_no_release', 'severity': 'high', 'fix': '有压抑但无释放'})

    return score, issues

def check_plot_progress(content):
    """维度2：情节推进（15分）"""
    new_info_signals = ['第一次', '新的', '从未', '突然', '发现', '得知',
                        '第一次被', '第一次见', '第一次做']
    world_change_signals = ['从此', '改变了', '决定', '放弃', '选择',
                           '死了', '离开了', '来了', '出现了']

    has_new = any(s in content for s in new_info_signals)
    has_change = any(s in content for s in world_change_signals)

    if has_new and has_change:
        score = 14
    elif has_change:
        score = 11
    elif has_new:
        score = 9
    else:
        score = 5

    issues = []
    if not has_new and not has_change:
        issues.append({'type': 'no_progress', 'severity': 'high', 'fix': '本章没有推进主线'})

    return score, issues

def check_character_consistency(content):
    """维度3：角色一致性（10分）"""
    issues = []
    score = 10

    # 检查人设崩塌
    for char, forbidden in CHARACTER_FORBIDDEN.items():
        for action in forbidden:
            if action in content:
                issues.append({
                    'type': 'character_violation',
                    'character': char,
                    'action': action,
                    'severity': 'high',
                    'fix': f'{char}不应{action}'
                })
                score -= 3

    # 检查封号错误
    for wrong, fix in WRONG_TITLES.items():
        if wrong in content:
            issues.append({
                'type': 'wrong_title',
                'title': wrong,
                'fix': fix,
                'severity': 'medium'
            })
            score -= 1

    return max(score, 0), issues

def check_logic(content, ch_num=0):
    """维度4：逻辑自洽（10分）"""
    issues = []
    score = 10

    # 检查已死角色复活
    if '崔善' in content:
        if ch_num > 45:  # 第46章及之后
            context_lines = [l for l in content.split('\n') if '崔善' in l]
            for line in context_lines:
                if re.search(r'崔善(站|走|说|笑|点头|摇头|拍|握|看)', line):
                    # 排除回忆/名册/玉佩/心里/历史语境
                    if not re.search(r'(回忆|名册|玉佩|想起|记得|当年|过去|心里|脑海|历史|文献|史书|曾经)', line):
                        issues.append({
                            'type': 'dead_character_alive',
                            'character': '崔善',
                            'severity': 'critical',
                            'fix': '崔善已在第45章去世，不可在非回忆场景中出现'
                        })
                        score = 0

    # 检查时间逻辑
    time_refs = re.findall(r'贞观(\d+)年', content)
    if time_refs:
        years = [int(y) for y in time_refs]
        if max(years) - min(years) > 3:
            issues.append({
                'type': 'time_jump',
                'severity': 'medium',
                'fix': '一章内时间跨度超过3年'
            })
            score -= 2

    return max(score, 0), issues

def check_rhythm(content):
    """维度5：节奏控制（10分）"""
    issues = []
    score = 10

    # 分割场景（以---分隔）
    scenes = re.split(r'\n---\n', content)
    scene_count = len(scenes)

    # 场景数检查
    if scene_count > 5:
        issues.append({
            'type': 'too_many_scenes',
            'count': scene_count,
            'severity': 'medium',
            'fix': '场景切换过快，考虑合并'
        })
        score -= 2

    if scene_count == 1 and len(content) > 3000:
        issues.append({
            'type': 'no_scene_change',
            'severity': 'low',
            'fix': '长文无场景切换，可能拖沓'
        })
        score -= 1

    # 段落长度检查
    paragraphs = [p for p in content.split('\n\n') if p.strip() and not p.startswith('#')]
    long_paras = [p for p in paragraphs if len(p) > 500]
    if len(long_paras) > 3:
        issues.append({
            'type': 'long_paragraphs',
            'count': len(long_paras),
            'severity': 'medium',
            'fix': '长段落过多，影响可读性'
        })
        score -= 1

    return max(score, 0), issues

def check_foreshadowing(content):
    """维度6：伏笔管理（10分）"""
    # 这个需要结合state.json，这里做基础检测
    score = 10
    issues = []

    # 检查是否有章末悬念
    last_200 = content[-200:] if len(content) > 200 else content
    has_cliffhanger = any(s in last_200 for s in ['？', '但', '然而', '可惜', '不知道', '没有说'])

    if not has_cliffhanger:
        issues.append({
            'type': 'no_cliffhanger',
            'severity': 'medium',
            'fix': '章末缺乏悬念或钩子'
        })
        score -= 2

    return score, issues

def check_readability(content):
    """维度7：可读性（10分）"""
    issues = []
    score = 10

    # 1. 禁词检测
    forbidden_issues = check_forbidden_words(content)
    for fi in forbidden_issues:
        issues.append(fi)
        score -= 1 if fi['severity'] == 'medium' else 2

    # 2. 破折号密度
    dash_issues = check_dash_density(content)
    for di in dash_issues:
        issues.append(di)
        score -= 1

    # 3. 时间+地点开头
    opening_issues = check_time_place_opening(content)
    for oi in opening_issues:
        issues.append(oi)
        score -= 2

    # 4. 句子平均长度
    sentences = re.split(r'[。！？]', content)
    sentences = [s for s in sentences if len(s.strip()) > 5]
    if sentences:
        avg_len = sum(len(s) for s in sentences) / len(sentences)
        if avg_len > 40:
            issues.append({
                'type': 'long_sentences',
                'avg': round(avg_len),
                'severity': 'medium',
                'fix': '句子过长，考虑拆分'
            })
            score -= 1

    # 5. 重复词检测
    words = re.findall(r'[\u4e00-\u9fff]{2}', content)
    if words:
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        top_repeat = sorted(word_freq.items(), key=lambda x: -x[1])[:5]
        # 只检查高频非功能词
        function_words = {'的', '了', '在', '是', '我', '他', '她', '你', '们', '不', '有', '和',
                         '就', '都', '而', '及', '与', '着', '一个', '上', '也', '到', '说', '要'}
        for word, count in top_repeat:
            if word not in function_words and count > 20:
                issues.append({
                    'type': 'word_repetition',
                    'word': word,
                    'count': count,
                    'severity': 'low',
                    'fix': f'"{word}"出现{count}次，考虑替换'
                })
                score -= 0.5

    return max(score, 0), issues

def check_commercial(content):
    """维度8：商业价值（5分）"""
    issues = []
    score = 5

    # 开头钩子
    first_100 = content[:100]
    has_hook = any(s in first_100 for s in TENSION_SIGNALS + ['。', '"', '！', '？'])
    if not has_hook:
        issues.append({
            'type': 'no_opening_hook',
            'severity': 'medium',
            'fix': '前100字没有钩子'
        })
        score -= 1

    # 章末钩子
    last_200 = content[-200:] if len(content) > 200 else content
    has_cliff = any(s in last_200 for s in ['？', '但', '然而', '不知道'])
    if not has_cliff:
        issues.append({
            'type': 'no_cliffhanger',
            'severity': 'medium',
            'fix': '章末缺乏悬念'
        })
        score -= 1

    return max(score, 0), issues

# ============================================================
# 主检测函数
# ============================================================

def check_chapter(filepath):
    """完整质检一个章节"""
    content = load_chapter(filepath)
    ch_num_str, ch_title = get_chapter_info(filepath)
    chapter_name = f"第{ch_num_str}章-{ch_title}" if ch_num_str else os.path.basename(filepath)
    
    # 提取数字章节号
    cn_to_num = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
                 '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18,'十九':19,
                 '二十':20,'二十一':21,'二十二':22,'二十三':23,'二十四':24,'二十五':25,
                 '二十六':26,'二十七':27,'二十八':28,'二十九':29,'三十':30,
                 '三十一':31,'三十二':32,'三十三':33,'三十四':34,'三十五':35,
                 '三十六':36,'三十七':37,'三十八':38,'三十九':39,'四十':40,
                 '四十一':41,'四十二':42,'四十三':43,'四十四':44,'四十五':45,
                 '四十六':46,'四十七':47,'四十八':48,'四十九':49,'五十':50,
                 '五十一':51,'五十二':52,'五十三':53,'五十四':54,'五十五':55,
                 '五十六':56,'五十七':57,'五十八':58,'五十九':59,'六十':60,
                 '六十一':61,'六十二':62,'六十三':63,'六十四':64,'六十五':65,
                 '六十六':66,'六十七':67,'六十八':68,'六十九':69,'七十':70,
                 '七十一':71,'七十二':72,'七十三':73,'七十四':74,'七十五':75,
                 '七十六':76,'七十七':77,'七十八':78,'七十九':79,'八十':80,
                 '八十一':81,'八十二':82,'八十三':83,'八十四':84,'八十五':85,
                 '八十六':86,'八十七':87,'八十八':88,'八十九':89,'九十':90,
                 '九十一':91,'九十二':92,'九十三':93,'九十四':94,'九十五':95,
                 '九十六':96,'九十七':97,'九十八':98,'九十九':99,'一百':100}
    ch_num = cn_to_num.get(ch_num_str, 0)
    if ch_num == 0:
        try:
            ch_num = int(ch_num_str)
        except:
            ch_num = 0

    results = {
        'chapter': chapter_name,
        'file': filepath,
        'total_score': 0,
        'breakdown': {},
        'issues': [],
        'verdict': 'PASS'
    }

    # 8维度检测
    dimensions = [
        ('爽点达成', 30, check_payoff),
        ('情节推进', 15, check_plot_progress),
        ('角色一致', 10, check_character_consistency),
        ('逻辑自洽', 10, lambda c: check_logic(c, ch_num)),
        ('节奏控制', 10, check_rhythm),
        ('伏笔管理', 10, check_foreshadowing),
        ('可读性', 10, check_readability),
        ('商业价值', 5, check_commercial),
    ]

    all_issues = []
    for name, max_score, check_fn in dimensions:
        score, issues = check_fn(content)
        results['breakdown'][name] = {
            'score': score,
            'max': max_score,
            'pct': round(score / max_score * 100)
        }
        all_issues.extend(issues)
        results['total_score'] += score

    results['issues'] = all_issues

    # 判定
    if results['total_score'] < 80:
        results['verdict'] = 'REWRITE'
    elif any(d['score'] / d['max'] < 0.5 for d in results['breakdown'].values()):
        results['verdict'] = 'FORCE_FIX'
    elif all_issues:
        results['verdict'] = 'FIX'
    else:
        results['verdict'] = 'PASS'

    return results

# ============================================================
# 报告输出
# ============================================================

def print_report(result):
    """打印单章报告"""
    emoji = {'PASS': '✅', 'FIX': '⚠️', 'FORCE_FIX': '🔴', 'REWRITE': '❌'}
    print(f"\n{'='*60}")
    print(f"{emoji[result['verdict']]} {result['chapter']} — {result['total_score']}/100 [{result['verdict']}]")
    print(f"{'='*60}")

    for name, data in result['breakdown'].items():
        bar = '█' * (data['pct'] // 10) + '░' * (10 - data['pct'] // 10)
        status = '✅' if data['pct'] >= 80 else '⚠️' if data['pct'] >= 50 else '❌'
        print(f"  {status} {name:6s} {bar} {data['score']}/{data['max']} ({data['pct']}%)")

    if result['issues']:
        print(f"\n  问题 ({len(result['issues'])}个):")
        for issue in result['issues']:
            sev = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
            print(f"    {sev.get(issue.get('severity','low'), '⚪')} {issue.get('type','')}: {issue.get('fix','')}")

def print_summary(results):
    """打印总报告"""
    print(f"\n{'='*60}")
    print(f"📊 质检总报告")
    print(f"{'='*60}")

    total = len(results)
    passed = sum(1 for r in results if r['verdict'] == 'PASS')
    fix = sum(1 for r in results if r['verdict'] == 'FIX')
    force = sum(1 for r in results if r['verdict'] == 'FORCE_FIX')
    rewrite = sum(1 for r in results if r['verdict'] == 'REWRITE')

    avg_score = sum(r['total_score'] for r in results) / total if total else 0

    print(f"  章节数: {total}")
    print(f"  平均分: {avg_score:.1f}/100")
    print(f"  ✅ PASS: {passed}")
    print(f"  ⚠️ FIX: {fix}")
    print(f"  🔴 FORCE_FIX: {force}")
    print(f"  ❌ REWRITE: {rewrite}")

    if rewrite > 0:
        print(f"\n  需重写的章节:")
        for r in results:
            if r['verdict'] == 'REWRITE':
                print(f"    ❌ {r['chapter']} ({r['total_score']}分)")

    if force > 0:
        print(f"\n  需强制修复的章节:")
        for r in results:
            if r['verdict'] == 'FORCE_FIX':
                print(f"    🔴 {r['chapter']} ({r['total_score']}分)")

# ============================================================
# 主程序
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 novel_check.py <章节文件>")
        print("  python3 novel_check.py --all")
        print("  python3 novel_check.py --range 42 56")
        sys.exit(1)

    if sys.argv[1] == '--all':
        files = sorted(glob.glob(os.path.join(BASE_DIR, '第*章*.md')))
        chapter_files = [f for f in files if re.search(r'第[一二三四五六七八九十百]+章', os.path.basename(f))]
    elif sys.argv[1] == '--range' and len(sys.argv) >= 4:
        start, end = int(sys.argv[2]), int(sys.argv[3])
        files = sorted(glob.glob(os.path.join(BASE_DIR, '第*章*.md')))
        chapter_files = []
        for f in files:
            fname = os.path.basename(f)
            # Match both Arabic and Chinese numerals
            match = re.search(r'第(\d+)章', fname)
            if match:
                ch_num = int(match.group(1))
                if start <= ch_num <= end:
                    chapter_files.append(f)
            else:
                # Try Chinese numeral
                cn_match = re.search(r'第(.+?)章', fname)
                if cn_match:
                    cn = cn_match.group(1)
                    cn_map = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
                             '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18,'十九':19,
                             '二十':20,'二十一':21,'二十二':22,'二十三':23,'二十四':24,'二十五':25,
                             '二十六':26,'二十七':27,'二十八':28,'二十九':29,'三十':30,
                             '三十一':31,'三十二':32,'三十三':33,'三十四':34,'三十五':35,
                             '三十六':36,'三十七':37,'三十八':38,'三十九':39,'四十':40,
                             '四十一':41,'四十二':42,'四十三':43,'四十四':44,'四十五':45,
                             '四十六':46,'四十七':47,'四十八':48,'四十九':49,'五十':50,
                             '五十一':51,'五十二':52,'五十三':53,'五十四':54,'五十五':55,
                             '五十六':56,'五十七':57,'五十八':58,'五十九':59,'六十':60,
                             '六十一':61,'六十二':62,'六十三':63,'六十四':64,'六十五':65,
                             '六十六':66,'六十七':67,'六十八':68,'六十九':69,'七十':70,
                             '七十一':71,'七十二':72,'七十三':73,'七十四':74,'七十五':75,
                             '七十六':76,'七十七':77,'七十八':78,'七十九':79,'八十':80,
                             '八十一':81,'八十二':82,'八十三':83,'八十四':84,'八十五':85,
                             '八十六':86,'八十七':87,'八十八':88,'八十九':89,'九十':90,
                             '九十一':91,'九十二':92,'九十三':93,'九十四':94,'九十五':95,
                             '九十六':96,'九十七':97,'九十八':98,'九十九':99,'一百':100}
                    ch_num = cn_map.get(cn, 0)
                    if start <= ch_num <= end:
                        chapter_files.append(f)
    else:
        chapter_files = [sys.argv[1]] if os.path.exists(sys.argv[1]) else \
                        [os.path.join(BASE_DIR, sys.argv[1])]

    results = []
    for f in chapter_files:
        if os.path.exists(f):
            result = check_chapter(f)
            results.append(result)
            print_report(result)

    if len(results) > 1:
        print_summary(results)

    # 输出JSON报告
    report_path = '/Users/narain/.openclaw/workspace-jinghong/novel/quality_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 JSON报告已保存: {report_path}")
