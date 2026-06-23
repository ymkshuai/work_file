# -*- coding: utf-8 -*-
"""
VU B2B Booking Flask Service
接收 booker.json 格式的 POST 请求, 调用 VUB2BBooker 完成订票流程

请求格式 (POST /booking):
{
    "exchangerate": {"VND": 0.000257, ...},
    "resdict": {"bookingAccount": "...", "bookingAccountPwd": "...", "minProfit": -100, ...},
    "bookdata": {"dptairport": "SGN", "arrairport": "PQC", "fromflightno": "9G1965", ...}
}

响应格式:
{
    "success": true,
    "resdict": { ... }  (回填后的完整 resdict)
}
"""

import json
import time
import logging
import logging.handlers
import os

from flask import Flask, jsonify, request

from VUB2BBooker import VUB2BBooker, Order

# 抑制 verify=False 的 SSL 警告
import requests as _requests
_requests.packages.urllib3.disable_warnings(
    _requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# ── Flask App ──────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── 日志配置 (文件轮转 + 控制台) ──────────────────────────────────────────
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "VUBOOK.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s - %(thread)d",
)
_file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s - %(thread)d")
)
logging.getLogger("").addHandler(_file_handler)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Flask 接口
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/vu/buy", methods=["POST"])
def booking():
    """
    VU B2B 订票接口

    接收 booker.json 格式的 JSON 请求体:
    {
        "exchangerate": {...},   # 实时汇率表
        "resdict": {...},        # 输入参数 + 输出结果
        "bookdata": {...}        # 预订数据 (乘客/航班/联系人等)
    }

    返回:
    {
        "success": true/false,
        "resdict": {...},        # 回填后的 resdict
        "msg": "..."             # 仅失败时
    }
    """
    start_time = time.time()

    # ── 1. 解析请求 ──
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "msg": "请求体必须为 JSON 格式"}), 400

    bookdata = data.get("bookdata")
    resdict = data.get("resdict")
    exchangerate = data.get("exchangerate", {})
    dry_run = data.get("dry_run", False)  # 试运行模式: 传 True 跳过支付

    if not bookdata:
        return jsonify({"success": False, "msg": "缺少 bookdata 字段"}), 400
    if not resdict:
        return jsonify({"success": False, "msg": "缺少 resdict 字段"}), 400

    # ── 2. 提取关键标识 (用于日志) ──
    orderno = bookdata.get("orderno", "unknown")
    flight_no = bookdata.get("fromflightno", "unknown")
    fromdate = bookdata.get("fromdate", "unknown")
    dpt = bookdata.get("dptairport", "?")
    arr = bookdata.get("arrairport", "?")
    logger.info(
        "[%s] 收到请求: %s %s->%s %s%s",
        orderno, flight_no, dpt, arr, fromdate,
        " [DRY_RUN]" if dry_run else "",
    )

    # ── 3. 基础参数校验 ──
    errors = []
    if not bookdata.get("dptairport"):
        errors.append("缺少 dptairport")
    if not bookdata.get("arrairport"):
        errors.append("缺少 arrairport")
    if not bookdata.get("fromflightno"):
        errors.append("缺少 fromflightno")
    if not bookdata.get("fromdate"):
        errors.append("缺少 fromdate")
    if not bookdata.get("passengers"):
        errors.append("缺少 passengers")
    if not resdict.get("bookingAccount"):
        errors.append("resdict 缺少 bookingAccount")
    if not resdict.get("bookingAccountPwd"):
        errors.append("resdict 缺少 bookingAccountPwd")

    if errors:
        logger.warning("[%s] 参数校验失败: %s", orderno, errors)
        return jsonify({
            "success": False,
            "msg": f"参数校验失败: {'; '.join(errors)}",
        }), 400

    # ── 4. 构建 Order 对象 ──
    try:
        order = Order.form_dict(bookdata)
    except Exception as e:
        logger.exception("[%s] 构建 Order 对象失败", orderno)
        return jsonify({
            "success": False,
            "msg": f"构建 Order 对象失败: {str(e)}",
        }), 400

    # ── 5. 执行订票 ──
    try:
        booker = VUB2BBooker()
        booker.book(order, resdict, exchangerates=exchangerate, dry_run=dry_run)
    except Exception as e:
        logger.exception("[%s] 订票过程异常", orderno)
        resdict["payStatus"] = "12"
        resdict["orderStatus"] = "0"
        resdict["msg"] = f"订票异常: {str(e)}"
        return jsonify({
            "success": False,
            "resdict": resdict,
            "msg": resdict["msg"],
        }), 500

    # ── 6. 返回结果 ──
    elapsed = time.time() - start_time
    pay_status = resdict.get("payStatus", "")
    msg = resdict.get("msg", "")
    pnr = resdict.get("bookingPnr", "")
    passenger = resdict.get("passenger", "")

    if pay_status == "21":
        # 购票成功: 重点记录乘客信息和 PNR
        logger.info(
            "[%s] ✓ 购票成功 (%.1fs) PNR=%s 乘客=%s 金额=%s %s",
            orderno, elapsed, pnr, passenger,
            resdict.get("bookingAllPrice", ""), resdict.get("bookingCurrency", ""),
        )
    else:
        logger.info(
            "[%s] 订票完成 (%.1fs) payStatus=%s msg=%s",
            orderno, elapsed, pay_status, msg,
        )

    return jsonify({
        "success": True,
        "resdict": resdict,
    })


@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "VUB2BBooker",
        "version": "1.0.0",
    })


# ═══════════════════════════════════════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("VU B2B Booking Service 启动, 端口: 10003")
    app.run(threaded=True, host="0.0.0.0", port=10003)
