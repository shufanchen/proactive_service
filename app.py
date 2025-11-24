#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, Response
import json
import time
from product_filter import filter_product, query_gpt

app = Flask(__name__)


def load_users():
    with open("user_info.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_products():
    with open("products.json", "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    users = load_users()
    products = load_products()
    return render_template("index.html", users=users, products=products)



@app.route("/get_user_profile")
def get_user_profile():
    user_id = request.args.get("user_id")
    users = load_users()
    user = next(u for u in users if u["user_id"] == user_id)
    return json.dumps(user, ensure_ascii=False)


# =========================
# 1) 流式输出过滤
# =========================
@app.route("/filter_stream")
def filter_stream():
    user_id = request.args.get("user_id")

    users = load_users()
    products = load_products()

    target_user = next(u for u in users if u["user_id"] == user_id)

    def generate():
        yield "event: start\ndata: {}\n\n"

        for prod in products:
            res = filter_product(target_user, prod)
            msg = {
                "product": prod,
                "result": res["result"],
                "reason": res["reason"]
            }

            yield "event: update\ndata: " + json.dumps(msg, ensure_ascii=False) + "\n\n"
            time.sleep(0.1)

        yield "event: done\ndata: {}\n\n"

    return Response(generate(), mimetype="text/event-stream")


# =========================
# 2) 流式输出推荐话术（单商品）
# =========================
@app.route("/copywriting_stream")
def copywriting_stream():
    user_id = request.args.get("user_id")
    product_id = request.args.get("product_id")

    users = load_users()
    products = load_products()

    user = next(u for u in users if u["user_id"] == user_id)
    product = next(p for p in products if p["product_id"] == product_id)

    prompt = f"""
    你是一个专业电商导购助手，为如下用户生成商品推荐话术：

    【用户画像】
    {json.dumps(user, ensure_ascii=False)}

    【商品】
    {json.dumps(product, ensure_ascii=False)}

    严格要求：
    1. 输出一句自然流畅、友好、有价值的推荐话术。
    2. 禁止输出括号、注释、总结、说明、分析、解释。
    3. 禁止出现如下格式：（xxx）、(xxx)、【xxx】、[xxx]。
    4. 禁止输出“共xx字”“理由”“要点”等内容。
    5. 字数不超过 60 字。
    """

    def generate():
        yield "event: start\ndata: {}\n\n"

        system_msg = "You are a helpful assistant."
        full_text = query_gpt(system=system_msg, user=prompt, temp=0.5)

        streamed = ""
        for ch in full_text:
            streamed += ch
            yield "event: update\ndata: " + json.dumps({"text": streamed}, ensure_ascii=False) + "\n\n"
            time.sleep(0.03)

        yield "event: done\ndata: {}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
