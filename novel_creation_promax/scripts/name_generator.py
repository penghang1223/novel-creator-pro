#!/usr/bin/env python3
"""
小说人物随机命名生成器 v2
从名字数据库中随机生成人物名字，支持题材/性别/风格/角色类型/年代过滤，
自动避开知名角色撞名、AI同质化命名、同音字冲突
"""

import argparse
import json
import os
import random
import re
import sys


# ========== 拼音映射（用于反同音检测）==========

_PINYIN_MAP = None


def _load_pinyin_map():
    """简化的拼音映射表，覆盖常用字"""
    global _PINYIN_MAP
    if _PINYIN_MAP is not None:
        return _PINYIN_MAP

    _PINYIN_MAP = {
        # 声母+韵母 → [同音字列表]
        "chen": ["陈", "沉", "晨", "辰", "尘"],
        "lin": ["林", "临", "邻", "麟", "霖"],
        "li": ["李", "黎", "丽", "莉", "力", "利", "立"],
        "zhang": ["张", "章", "彰"],
        "wang": ["王", "望", "旺"],
        "liu": ["刘", "流", "柳", "留"],
        "yang": ["杨", "阳", "洋", "扬"],
        "huang": ["黄", "皇", "煌"],
        "zhao": ["赵", "照", "兆"],
        "wu": ["吴", "无", "武", "物"],
        "xu": ["徐", "许", "序", "旭"],
        "sun": ["孙", "损"],
        "hu": ["胡", "湖", "虎"],
        "zhu": ["朱", "竹", "珠", "祝"],
        "gao": ["高", "糕"],
        "he": ["何", "贺", "河", "和", "合"],
        "guo": ["郭", "国", "果"],
        "ma": ["马", "麻"],
        "luo": ["罗", "洛", "落", "逻"],
        "liang": ["梁", "良", "亮"],
        "song": ["宋", "送", "颂"],
        "zheng": ["郑", "正", "政", "征"],
        "xie": ["谢", "解", "写", "谢"],
        "han": ["韩", "寒", "涵", "含"],
        "tang": ["唐", "堂", "糖"],
        "feng": ["冯", "风", "峰", "凤"],
        "deng": ["邓", "灯", "登"],
        "cao": ["曹", "草", "操"],
        "peng": ["彭", "鹏", "蓬"],
        "zeng": ["曾", "增", "赠"],
        "xiao": ["肖", "萧", "笑", "晓"],
        "tian": ["田", "甜", "天"],
        "dong": ["董", "东", "冬", "懂"],
        "pan": ["潘", "盼", "盘"],
        "yuan": ["袁", "元", "源", "原", "远"],
        "cai": ["蔡", "才", "财"],
        "jiang": ["蒋", "江", "姜", "将"],
        "yu": ["于", "余", "鱼", "雨", "宇", "羽", "玉"],
        "du": ["杜", "度", "独"],
        "ye": ["叶", "夜", "野", "业"],
        "cheng": ["程", "成", "城", "诚", "承"],
        "wei": ["魏", "韦", "卫", "伟", "维", "威", "唯"],
        "su": ["苏", "素", "速", "诉"],
        "lv": ["吕", "旅", "律", "绿"],
        "ding": ["丁", "定", "顶"],
        "shen": ["沈", "深", "申", "神"],
        "ren": ["任", "仁", "认"],
        "yao": ["姚", "遥", "摇", "尧"],
        "lu": ["卢", "鲁", "路", "陆", "鹿", "录"],
        "cui": ["崔", "催", "翠"],
        "zhong": ["钟", "中", "忠", "终"],
        "tan": ["谭", "谈", "探"],
        "fan": ["范", "凡", "繁"],
        "wang_": ["汪", "王"],
        "jin": ["金", "进", "近", "今"],
        "shi": ["石", "史", "时", "师", "十"],
        "liao": ["廖", "辽", "了"],
        "jia": ["贾", "家", "佳", "嘉"],
        "xia": ["夏", "下", "霞"],
        "fu": ["傅", "付", "福", "复", "富"],
        "fang": ["方", "房", "放"],
        "zou": ["邹", "走"],
        "xiong": ["熊", "雄"],
        "bai": ["白", "百"],
        "meng": ["孟", "梦", "蒙"],
        "qin": ["秦", "琴", "勤"],
        "qiu": ["邱", "秋", "求"],
        "hou": ["侯", "后", "厚"],
        "gu": ["顾", "古", "谷", "故"],
        "shao": ["邵", "少", "绍"],
        "long": ["龙", "隆"],
        "wan": ["万", "完", "晚"],
        "duan": ["段", "短", "端"],
        "lei": ["雷", "类", "泪"],
        "qian": ["钱", "前", "千", "潜"],
        "yin": ["殷", "银", "音", "因", "隐"],
        "zhuang": ["庄", "壮", "装"],
        "wen": ["温", "文", "闻"],
        "niu": ["牛", "扭"],
        "yan": ["严", "颜", "言", "燕", "艳", "岩"],
        "an": ["安", "按", "案"],
        "chang": ["常", "长", "尝", "唱"],
        "mo": ["莫", "墨", "默", "末"],
        "yi": ["易", "义", "意", "艺", "一", "亦", "毅"],
        "geng": ["耿", "更", "耕"],
        "kuang": ["邝", "况", "狂"],
        "qiao": ["乔", "桥", "巧"],
        "zhai": ["翟", "宅"],
        "lan": ["蓝", "兰", "览"],
        "nie": ["聂", "捏"],
        }

    return _PINYIN_MAP


def get_pinyin_group(char):
    """获取字符的拼音组（简化版，用于同音检测）"""
    pinyin_map = _load_pinyin_map()
    for pinyin, chars in pinyin_map.items():
        if char in chars:
            return chars
    return [char]


def check_homophony(name1, name2):
    """检查两个名字是否存在同音风险（姓同音或名同音）"""
    if not name2:
        return False

    # 姓同音
    surname1_group = get_pinyin_group(name1[0])
    surname2_group = get_pinyin_group(name2[0])
    if set(surname1_group) & set(surname2_group):
        return True

    # 名同音（至少一个字同音）
    given1 = name1[1:] if len(name1) > 1 else ""
    given2 = name2[1:] if len(name2) > 1 else ""
    for c1 in given1:
        for c2 in given2:
            group1 = get_pinyin_group(c1)
            group2 = get_pinyin_group(c2)
            if set(group1) & set(group2):
                return True

    return False


# ========== 角色类型 → 风格映射 ==========

ROLE_STYLE_MAP = {
    # (优先风格池, 姓氏倾向, 特征说明)
    "entrepreneur": (["urban_tech", "modern"], None, "创业者/技术天才，名字现代感强"),
    "tech": (["urban_tech", "modern"], None, "科技行业，名字有科技感"),
    "investor": (["urban_finance", "modern"], "literary", "投资人/金融人，名字稳重有分量"),
    "finance": (["urban_finance", "modern"], "literary", "金融行业，名字专业感"),
    "villain": (["dark", "urban_finance"], "literary", "反派/暗面人物，名字表面正气实则城府"),
    "capitalist": (["urban_finance", "dark"], "literary", "资本大佬，名字大气有压迫感"),
    "executive": (["urban_finance", "modern"], None, "高管/总监，名字专业有格局"),
    "analyst": (["urban_finance", "modern"], None, "分析师/专业人员，名字聪慧敏锐"),
    "parent": (["modern", "gentle"], None, "父母辈，名字有年代感"),
    "child": (["modern"], None, "孩子辈，名字清新"),
    "scholarly": (["ancient_elegant", "modern"], "literary", "学者/文人，名字有书卷气"),
    "martial": (["martial", "strong"], None, "武人/军人，名字刚健"),
    "gentle": (["gentle", "modern"], None, "温柔角色，名字柔和"),
    "strong": (["strong", "modern"], None, "强势角色，名字有力"),
}


# ========== 年代 → 年代标签映射 ==========

ERA_TAG_MAP = {
    "60": ["60-70"],
    "70": ["60-70", "70-90"],
    "80": ["70-90", "80-00", "80-10"],
    "90": ["80-00", "80-10", "90-10"],
    "00": ["90-10", "00-10"],
    "10": ["90-10", "00-10"],
}


# ========== 数据库加载 ==========

def load_database(db_path=None):
    """加载名字数据库"""
    if db_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, "..", "assets", "corpus", "name-database.json")

    db_path = os.path.normpath(db_path)
    if not os.path.exists(db_path):
        print(json.dumps({"error": f"名字数据库不存在: {db_path}"}, ensure_ascii=False))
        sys.exit(1)

    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_input(args):
    """验证输入参数"""
    if args.gender and args.gender not in ("male", "female"):
        print(json.dumps({"error": f"gender 必须为 male 或 female，当前: {args.gender}"}, ensure_ascii=False))
        sys.exit(1)

    valid_styles = [
        "ancient_elegant", "martial", "xianxia", "modern", "rustic", "dark",
        "gentle", "strong", "scholarly", "neutral",
        "urban_tech", "urban_finance", "urban_executive"
    ]
    if args.style and args.style not in valid_styles:
        print(json.dumps({"error": f"style 必须为以下之一: {', '.join(valid_styles)}", "valid_styles": valid_styles}, ensure_ascii=False))
        sys.exit(1)

    if args.role and args.role not in ROLE_STYLE_MAP:
        valid_roles = list(ROLE_STYLE_MAP.keys())
        print(json.dumps({"error": f"role 必须为以下之一: {', '.join(valid_roles)}", "valid_roles": valid_roles}, ensure_ascii=False))
        sys.exit(1)

    if args.count < 1 or args.count > 50:
        print(json.dumps({"error": "count 必须在 1-50 之间"}, ensure_ascii=False))
        sys.exit(1)

    if args.era and args.era not in ERA_TAG_MAP:
        valid_eras = list(ERA_TAG_MAP.keys())
        print(json.dumps({"error": f"era 必须为以下之一: {', '.join(valid_eras)}", "valid_eras": valid_eras}, ensure_ascii=False))
        sys.exit(1)


# ========== 姓氏池 ==========

def get_surname_pool(db, tier=None, exclude_surnames=None):
    """获取姓氏池"""
    exclude = set(exclude_surnames or [])

    overused = {item["char"] for item in db["surnames"].get("overused_in_webnovel", [])}

    pools = []
    if tier == "common" or tier is None:
        pools.append(db["surnames"]["common"])
    if tier == "literary" or tier is None:
        pools.append(db["surnames"]["literary"])
    if tier == "compound" or tier is None:
        pools.append(db["surnames"]["compound"])

    result = []
    for pool in pools:
        for item in pool:
            char = item["char"]
            if char in exclude:
                continue
            is_overused = char in overused
            result.append({
                "char": char,
                "note": item.get("note", ""),
                "overused": is_overused
            })

    return result


# ========== 名字池 ==========

def get_given_name_pool(db, gender, style=None, era=None):
    """获取名字池，支持 style + era 双重过滤"""
    pools = []

    if gender == "male":
        gender_data = db["given_names"]["male"]
    elif gender == "female":
        gender_data = db["given_names"]["female"]
    else:
        gender_data = {}

    if style and style in gender_data:
        pools.append(gender_data[style])
    elif style == "neutral":
        pools.append(db["given_names"]["neutral"].get("single_char", []))
        pools.append(db["given_names"]["neutral"].get("double_char", []))
    elif style == "scholarly" and gender == "male":
        pools.append(gender_data.get("ancient_elegant", []))
    else:
        for style_name, items in gender_data.items():
            pools.append(items)
        if random.random() < 0.3:
            pools.append(db["given_names"]["neutral"].get("single_char", []))

    result = []
    for pool in pools:
        for item in pool:
            entry = {
                "name": item["name"],
                "meaning": item.get("meaning", ""),
                "era": item.get("era", ""),
                "ai_warning": item.get("ai_warning", None)
            }

            # 年代过滤
            if era:
                era_tags = ERA_TAG_MAP.get(era, [])
                item_era = item.get("era", "")
                if item_era and not any(tag in item_era for tag in era_tags):
                    continue

            result.append(entry)

    return result


# ========== 检查函数 ==========

def check_avoid_list(full_name, db):
    """检查是否撞名知名角色"""
    for item in db["avoid_list"]["famous_characters"]:
        if full_name == item["name"]:
            return {"hit": True, "source": item["source"]}
    return {"hit": False}


def check_ai_pattern(given_name, db):
    """检查是否匹配AI同质化命名模式"""
    for item in db["avoid_list"]["ai_pattern_names"]:
        patterns = item["pattern"].split("/")
        for p in patterns:
            if given_name.startswith(p[0]) and given_name.endswith(p[-1]) and len(given_name) == len(p):
                return {"hit": True, "reason": item["reason"]}
            if p in given_name:
                return {"hit": True, "reason": item["reason"]}
    return {"hit": False}


# ========== 生成逻辑 ==========

def generate_names(db, gender=None, style=None, count=5, surname_tier=None,
                   exclude_surnames=None, allow_overused=False,
                   role=None, era=None, reason=False, exclude_names=None):
    """生成随机名字，支持角色类型、年代、反同音"""

    # 角色类型 → 风格覆盖
    if role and role in ROLE_STYLE_MAP:
        role_styles, role_surname_tier, _ = ROLE_STYLE_MAP[role]
        if style is None:
            # 从角色风格池中加权选择（第一个风格权重更高）
            style = random.choices(role_styles, weights=[3] + [1] * (len(role_styles) - 1), k=1)[0]
        if surname_tier is None and role_surname_tier:
            surname_tier = role_surname_tier

    surname_pool = get_surname_pool(db, tier=surname_tier, exclude_surnames=exclude_surnames)

    if not allow_overused:
        weighted_surnames = []
        for s in surname_pool:
            if s["overused"]:
                weighted_surnames.append(s)
            else:
                weighted_surnames.extend([s] * 5)
        surname_pool = weighted_surnames if weighted_surnames else surname_pool

    if gender is None:
        gender = random.choice(["male", "female"])

    given_name_pool = get_given_name_pool(db, gender, style, era)

    if not surname_pool:
        return {"error": "姓氏池为空，请检查过滤条件"}
    if not given_name_pool:
        return {"error": f"名字池为空，gender={gender}, style={style}, era={era} 无可用名字"}

    existing_names = list(exclude_names) if exclude_names else []
    results = []
    attempts = 0
    max_attempts = count * 20

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        surname = random.choice(surname_pool)
        given = random.choice(given_name_pool)
        full_name = surname["char"] + given["name"]

        # 撞名检查
        avoid_check = check_avoid_list(full_name, db)
        if avoid_check["hit"]:
            continue

        # AI模式检查
        ai_check = check_ai_pattern(given["name"], db)

        # 反同音检查：与已存在名字不同音
        if any(check_homophony(full_name, en) for en in existing_names):
            continue

        # 去重
        if any(r["full_name"] == full_name for r in results):
            continue

        entry = {
            "full_name": full_name,
            "surname": surname["char"],
            "given_name": given["name"],
            "meaning": given.get("meaning", ""),
            "surname_note": surname.get("note", ""),
            "surname_overused": surname.get("overused", False),
            "ai_pattern_warning": ai_check["reason"] if ai_check["hit"] else None,
        }

        if given.get("ai_warning"):
            entry["ai_pattern_warning"] = given["ai_warning"]

        if given.get("era"):
            entry["era"] = given["era"]

        if reason:
            entry["reason"] = _generate_reason(surname, given, role, style, gender)

        results.append(entry)
        existing_names.append(full_name)

    output = {
        "count": len(results),
        "gender": gender,
        "style": style,
        "role": role,
        "era": era,
        "names": results
    }

    return output


def _generate_reason(surname, given, role, style, gender):
    """生成命名理由"""
    parts = []

    if surname.get("note"):
        parts.append(f"姓：{surname['char']}——{surname['note']}")

    if given.get("meaning"):
        parts.append(f"名：{given['name']}——{given['meaning']}")

    if role and role in ROLE_STYLE_MAP:
        _, _, desc = ROLE_STYLE_MAP[role]
        parts.append(f"适配：{desc}")

    if given.get("era"):
        parts.append(f"年代感：{given['era']}后常见")

    return "；".join(parts)


# ========== CLI ==========

def main():
    parser = argparse.ArgumentParser(description="小说人物随机命名生成器 v2")
    parser.add_argument("--gender", choices=["male", "female"], default=None,
                        help="角色性别（不指定则随机）")
    parser.add_argument("--style", default=None,
                        help="命名风格: ancient_elegant/martial/xianxia/modern/rustic/dark/gentle/strong/neutral/urban_tech/urban_finance/urban_executive")
    parser.add_argument("--count", type=int, default=5,
                        help="生成名字数量（1-50，默认5）")
    parser.add_argument("--surname-tier", choices=["common", "literary", "compound"], default=None,
                        help="姓氏层级偏好: common(常见)/literary(文艺)/compound(复姓)")
    parser.add_argument("--exclude-surnames", nargs="*", default=None,
                        help="排除的姓氏列表")
    parser.add_argument("--allow-overused", action="store_true",
                        help="允许使用网文过用姓氏（叶/林/萧等）")
    parser.add_argument("--db", default=None,
                        help="名字数据库文件路径")
    parser.add_argument("--role", default=None,
                        help="角色类型: entrepreneur/tech/investor/finance/villain/capitalist/executive/analyst/parent/child/scholarly/martial/gentle/strong")
    parser.add_argument("--era", default=None,
                        help="年代适配: 60/70/80/90/00/10")
    parser.add_argument("--reason", action="store_true",
                        help="输出命名理由")
    parser.add_argument("--exclude-names", nargs="*", default=None,
                        help="排除已有名字（反同音检测）")

    args = parser.parse_args()
    validate_input(args)

    db = load_database(args.db)
    result = generate_names(
        db,
        gender=args.gender,
        style=args.style,
        count=args.count,
        surname_tier=args.surname_tier,
        exclude_surnames=args.exclude_surnames,
        allow_overused=args.allow_overused,
        role=args.role,
        era=args.era,
        reason=args.reason,
        exclude_names=args.exclude_names
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
