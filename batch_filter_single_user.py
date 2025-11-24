#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
功能：
  指定某个用户，对整个商品池执行过滤
  输出两种结果文件：
    result_<user_id>.jsonl
    result_<user_id>.json
"""

import json
from product_filter import filter_product


# =====================
# 工具函数
# =====================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jsonl(results, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def save_json(results, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


# =====================
# 核心过滤流程
# =====================

def run_filter_for_user(user_id, users_path="users.json", products_path="products.json"):
    print(f"载入用户文件: {users_path}")
    users = load_json(users_path)

    print(f"载入商品池: {products_path}")
    products = load_json(products_path)

    # 找到指定用户
    target_user = None
    for u in users:
        if u.get("user_id") == user_id:
            target_user = u
            break

    if target_user is None:
        raise ValueError(f"未找到用户 user_id = {user_id}")

    print(f"\n开始过滤：用户 {target_user['user_id']} （类型 {target_user['user_type']}）\n")

    results = []

    # 执行过滤
    for prod in products:
        res = filter_product(target_user, prod)
        r = {
            "user_id": target_user["user_id"],
            "user_type": target_user["user_type"],
            "product_id": prod["product_id"],
            "product_name": prod["name"],
            "category": prod["category"],
            "price": prod["price"],
            "stock": prod["stock"],
            "result": res["result"],
            "reason": res["reason"]
        }
        results.append(r)

        print(f"[{target_user['user_id']}] {prod['name']} -> {r['result']}  | {r['reason']}")

    # 保存结果
    out_jsonl = f"result_{user_id}.jsonl"
    out_json = f"result_{user_id}.json"

    print(f"\n保存文件: {out_jsonl}, {out_json}")

    save_jsonl(results, out_jsonl)
    save_json(results, out_json)

    print("\n完成！")


# =====================
# 程序入口
# =====================

if __name__ == "__main__":
    # TODO：在这里填写你想过滤的用户 id，例如：
    YOUR_USER_ID = "C1_U001"

    run_filter_for_user(YOUR_USER_ID, users_path="user_info.json", products_path="products.json")
