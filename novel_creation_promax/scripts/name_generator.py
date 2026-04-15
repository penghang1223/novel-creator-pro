#!/usr/bin/env python3
"""
小说人物随机命名生成器
从名字数据库中随机生成人物名字，支持题材/性别/风格过滤，自动避开知名角色撞名和AI同质化命名
"""

import argparse
import json
import os
import random
import sys


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
        "gentle", "strong", "scholarly", "neutral"
    ]
    if args.style and args.style not in valid_styles:
        print(json.dumps({"error": f"style 必须为以下之一: {', '.join(valid_styles)}", "valid_styles": valid_styles}, ensure_ascii=False))
        sys.exit(1)

    if args.count < 1 or args.count > 50:
        print(json.dumps({"error": "count 必须在 1-50 之间"}, ensure_ascii=False))
        sys.exit(1)


def get_surname_pool(db, tier=None, exclude_surnames=None):
    """获取姓氏池"""
    exclude = set(exclude_surnames or [])

    # 标记网文过用姓氏
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


def get_given_name_pool(db, gender, style=None):
    """获取名字池"""
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
        # scholarly 映射到 ancient_elegant
        pools.append(gender_data.get("ancient_elegant", []))
    else:
        # 返回该性别所有风格
        for style_name, items in gender_data.items():
            pools.append(items)
        # 有概率加入中性名
        if random.random() < 0.3:
            pools.append(db["given_names"]["neutral"].get("single_char", []))

    result = []
    for pool in pools:
        for item in pool:
            result.append({
                "name": item["name"],
                "meaning": item.get("meaning", "")
            })

    return result


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


def generate_names(db, gender=None, style=None, count=5, surname_tier=None,
                   exclude_surnames=None, allow_overused=False):
    """生成随机名字"""
    surname_pool = get_surname_pool(db, tier=surname_tier, exclude_surnames=exclude_surnames)

    if not allow_overused:
        # 降低网文过用姓氏的权重（不完全排除，但大幅降低概率）
        weighted_surnames = []
        for s in surname_pool:
            if s["overused"]:
                # 过用姓氏只保留1份，正常姓氏保留5份
                weighted_surnames.append(s)
            else:
                weighted_surnames.extend([s] * 5)
        surname_pool = weighted_surnames if weighted_surnames else surname_pool

    # 确定性别（未指定时随机）
    if gender is None:
        gender = random.choice(["male", "female"])

    given_name_pool = get_given_name_pool(db, gender, style)

    if not surname_pool:
        return {"error": "姓氏池为空，请检查过滤条件"}
    if not given_name_pool:
        return {"error": f"名字池为空，gender={gender}, style={style} 无可用名字"}

    results = []
    attempts = 0
    max_attempts = count * 10  # 防止无限循环

    while len(results) < count and attempts < max_attempts:
        attempts += 1

        surname = random.choice(surname_pool)
        given = random.choice(given_name_pool)
        full_name = surname["char"] + given["name"]

        # 检查撞名
        avoid_check = check_avoid_list(full_name, db)
        if avoid_check["hit"]:
            continue

        # 检查AI模式
        ai_check = check_ai_pattern(given["name"], db)

        entry = {
            "full_name": full_name,
            "surname": surname["char"],
            "given_name": given["name"],
            "meaning": given.get("meaning", ""),
            "surname_note": surname.get("note", ""),
            "surname_overused": surname.get("overused", False),
            "ai_pattern_warning": ai_check["reason"] if ai_check["hit"] else None
        }

        # 去重
        if any(r["full_name"] == full_name for r in results):
            continue

        results.append(entry)

    return {
        "count": len(results),
        "gender": gender,
        "style": style,
        "names": results
    }


def main():
    parser = argparse.ArgumentParser(description="小说人物随机命名生成器")
    parser.add_argument("--gender", choices=["male", "female"], default=None,
                        help="角色性别（不指定则随机）")
    parser.add_argument("--style", default=None,
                        help="命名风格: ancient_elegant/martial/xianxia/modern/rustic/dark/gentle/strong/neutral")
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
        allow_overused=args.allow_overused
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
