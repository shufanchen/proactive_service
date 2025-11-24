#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品过滤器 (基于 LLM)
输入：用户信息 + 待过滤商品
输出：可推荐 / 不可推荐 + 一句话理由

使用你现有的 GPT 调用方式。
"""

import os
import json
import requests
import random

# ======================
# 配置（与你一致）
# ======================

GPT_URL = os.getenv("GPT_URL", "http://gpt-proxy.jd.com/gateway/azure/chat/completions")
API_LIST = ["41698f72-aa72-41fc-b621-ed206141295e",
            "0209233e-53f7-4f5b-8d56-ed1cae67e482",
            "5380365d-902a-4567-afdb-e18afad53f72",
            "27a53deb-689b-403b-946b-007d66c75c02",
            "c310c351-eaff-48bd-a6bc-708077e0f254",
            "1fe168c2-ebf2-43ca-a008-005f2f33a835",
            "2d2856c9-d4bf-4e83-81c0-ec5dee1d35d9",
            "bb5fcf95-3705-416e-b2b9-5a49fa3d950b",
            "3547d05a-6c90-41c1-9aba-a26af77b5814"]   # 可填多个 API key
MODEL_NAME = "DeepSeek-V3-baidu"
TEMPERATURE = 0.0
RETRY_TIMES = 3
TIMEOUT = 30


# ======================
# GPT 调用函数（从你的代码抽取）
# ======================

def query_gpt(system="", user="", temp=0, retry=RETRY_TIMES, model=MODEL_NAME):
    data = {
        "model": model,
        "temperature": temp,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    json_data = json.dumps(data, ensure_ascii=False)

    for attempt in range(retry):
        api_key = random.choice(API_LIST) if API_LIST else ""
        header = {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": api_key,
        }
        try:
            resp = requests.post(
                url=GPT_URL,
                data=json_data.encode("utf-8", errors="ignore"),
                headers=header,
                timeout=TIMEOUT
            )
            if resp.status_code == 200:
                dd = resp.json()
                return dd["choices"][0]["message"]["content"]
            else:
                print(f"[WARN] HTTP {resp.status_code}, retry {attempt+1}/{retry}")
        except Exception as e:
            print(f"[ERROR] {e}, retry {attempt+1}/{retry}")
    return None


# ======================
# Prompt 构造
# ======================

def build_filter_prompt(user_info, product_info):
    """
    根据你之前写好的 Prompt 生成输入文本。
    user_info: dict
    product_info: dict
    """

    prompt = f"""
你现在扮演电商系统中的“商品推荐过滤器”。
请根据以下规则判断商品是否适合主动推荐。

【用户信息】
{json.dumps(user_info, ensure_ascii=False, indent=2)}

【商品信息】
{json.dumps(product_info, ensure_ascii=False, indent=2)}

【需要执行的过滤规则】
1. 年龄限制过滤：若商品为年龄受限类目，且用户年龄不满足，则不可推荐。
2. 性别与敏感品类匹配过滤：若商品性别倾向强，且与用户性别不匹配，则不可推荐。
3. 用户拒绝列表过滤：若商品类目或品牌在用户拒绝列表中，则不可推荐。
4. 价格带过滤：若商品价格显著超出用户可接受价格带，则不可推荐。
5. 库存过滤：若库存量为 0 或标记为不可售，则不可推荐。
6. 耐用品重复购买过滤：若商品为耐用品类主商品，且用户近期已购买同类，则不可推荐主商品（配件/耗材不受限）。

请严格执行上述规则。

输出格式：
【结论】可推荐 / 不可推荐
【理由】一句话解释原因
"""

    return prompt


# ======================
# 输出解析
# ======================

def parse_filter_output(text):
    """
    简单解析 LLM 输出格式：
    【结论】xxx
    【理由】xxx
    """
    if not text:
        return {"result": "不可推荐", "reason": "LLM 无返回"}

    lines = text.strip().split("\n")

    result = "不可推荐"
    reason = "无理由"

    for line in lines:
        if "【结论】" in line:
            result = line.replace("【结论】", "").strip()
        elif "【理由】" in line:
            reason = line.replace("【理由】", "").strip()

    return {
        "result": result,
        "reason": reason
    }


# ======================
# 主流程：过滤单个商品
# ======================

def filter_product(user_info, product_info):
    system_msg = "You are a strict rule-based product filtering engine."
    prompt = build_filter_prompt(user_info, product_info)

    content = query_gpt(system=system_msg, user=prompt, temp=0.0)
    parsed = parse_filter_output(content)
    return parsed


# ======================
# Demo 示例（你后续可以删除）
# ======================

if __name__ == "__main__":
    # 示例用户
    user = {
        "age": 15,
        "gender": "M",
        "price_range": [30, 120],
        "blocked_list": ["酒类"],
        "search_history": ["耳机", "篮球鞋"],
        "view_history": [],
        "cart_history": [],
        "purchase_history": []
    }

    # 示例商品
    product = {
        "name": "杜蕾斯 避孕套",
        "category": "成人用品",
        "brand": "杜蕾斯",
        "price": 59,
        "stock": 100
    }

    result = filter_product(user, product)
    print(json.dumps(result, ensure_ascii=False, indent=2))
