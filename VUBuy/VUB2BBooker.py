# -*- coding:utf-8 -*-
"""
VU (Vietravel Airlines) B2B Booker
仿照 VJB2BBooker 结构, 调用 VU Sabre API 完成订票
流程: B2B登录 → 搜索航班 → 选择 Economy Saver → 填写乘客 → PreBook → [选座] → [买行李] → 报价校验 → B2B支付(INVC)
"""
import random
import re
import time
import math
import string
import datetime
import json
import logging
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ==================== 常量 ====================

TITLES = {'M': 'MR', 'F': 'MS'}
GENDER = {'M': 'M', 'F': 'F'}

# VU Sabre API 配置
BASE_URL = "https://vietravel-api-ase1.ezycommerce.sabre.com/api/v1"
TENANT_KEY = "FrcfKCaL47LiRMzX9qMAqguP6ztQEM3UHnjTbQKyp3dLjVEFBf4nnu7YG6afzV64"

# 国家 2位→3位 映射
COUNTRY_2_TO_3 = {
    "US": {"code": "USA", "name": "United States"},
    "CN": {"code": "CHN", "name": "China"},
    "HK": {"code": "HKG", "name": "Hong Kong"},
    "MO": {"code": "MAC", "name": "Macau"},
    "TW": {"code": "TWN", "name": "Taiwan"},
    "JP": {"code": "JPN", "name": "Japan"},
    "KR": {"code": "KOR", "name": "South Korea"},
    "VN": {"code": "VNM", "name": "Vietnam"},
    "TH": {"code": "THA", "name": "Thailand"},
    "SG": {"code": "SGP", "name": "Singapore"},
    "MY": {"code": "MYS", "name": "Malaysia"},
    "PH": {"code": "PHL", "name": "Philippines"},
    "ID": {"code": "IDN", "name": "Indonesia"},
    "IN": {"code": "IND", "name": "India"},
    "PK": {"code": "PAK", "name": "Pakistan"},
    "AU": {"code": "AUS", "name": "Australia"},
    "NZ": {"code": "NZL", "name": "New Zealand"},
    "GB": {"code": "GBR", "name": "United Kingdom"},
    "FR": {"code": "FRA", "name": "France"},
    "DE": {"code": "DEU", "name": "Germany"},
    "IT": {"code": "ITA", "name": "Italy"},
    "ES": {"code": "ESP", "name": "Spain"},
    "PT": {"code": "PRT", "name": "Portugal"},
    "NL": {"code": "NLD", "name": "Netherlands"},
    "BE": {"code": "BEL", "name": "Belgium"},
    "CH": {"code": "CHE", "name": "Switzerland"},
    "AT": {"code": "AUT", "name": "Austria"},
    "SE": {"code": "SWE", "name": "Sweden"},
    "NO": {"code": "NOR", "name": "Norway"},
    "FI": {"code": "FIN", "name": "Finland"},
    "DK": {"code": "DNK", "name": "Denmark"},
    "IE": {"code": "IRL", "name": "Ireland"},
    "PL": {"code": "POL", "name": "Poland"},
    "CZ": {"code": "CZE", "name": "Czech Republic"},
    "SK": {"code": "SVK", "name": "Slovakia"},
    "HU": {"code": "HUN", "name": "Hungary"},
    "RO": {"code": "ROU", "name": "Romania"},
    "RU": {"code": "RUS", "name": "Russia"},
    "UA": {"code": "UKR", "name": "Ukraine"},
    "CA": {"code": "CAN", "name": "Canada"},
    "MX": {"code": "MEX", "name": "Mexico"},
    "BR": {"code": "BRA", "name": "Brazil"},
    "AR": {"code": "ARG", "name": "Argentina"},
    "CO": {"code": "COL", "name": "Colombia"},
    "PE": {"code": "PER", "name": "Peru"},
    "ZA": {"code": "ZAF", "name": "South Africa"},
    "EG": {"code": "EGY", "name": "Egypt"},
    "AE": {"code": "ARE", "name": "United Arab Emirates"},
    "SA": {"code": "SAU", "name": "Saudi Arabia"},
    "QA": {"code": "QAT", "name": "Qatar"},
    "TR": {"code": "TUR", "name": "Turkey"},
    "IL": {"code": "ISR", "name": "Israel"},
    "KH": {"code": "KHM", "name": "Cambodia"},
    "LK": {"code": "LKA", "name": "Sri Lanka"},
    "MM": {"code": "MMR", "name": "Myanmar"},
    "LA": {"code": "LAO", "name": "Laos"},
    "MN": {"code": "MNG", "name": "Mongolia"},
}

# 越南国内机场代码 (用于判断是否国际线)
VN_AIRPORTS = {"HAN", "SGN", "DAD", "HPH", "VCA", "DLI", "CXR", "PQC", "BMV", "UIH",
               "VDH", "THD", "VCL", "VII", "PXU", "HUI", "VKG", "CAH"}

# 代理配置 (astospider)
PROXY_USERNAME = "astoip3305"
PROXY_PASSWORD = "ZUOPGEE-CNJYIFI-TDJECSC-AJGS2TC-STK0IZ0-Y57LNII-UY3FEGD"
PROXY_HOST = "proxy.astospider.com"
PROXY_PORT_RANGE = range(9001, 9050)

# ==================== Order 数据类 ====================

class Contact:
    def __init__(self, data=None):
        data = data or {}
        self.city = data.get("city", "")
        self.firstname = data.get("firstname", "")
        self.lastname = data.get("lastname", "")
        self.ctripemail = data.get("ctripemail", "")
        self.useGuestMail = data.get("useGuestMail", False)
        self.nation = data.get("nation", "")
        self.email = data.get("email", "")
        self.postcode = data.get("postcode", "")
        self.address = data.get("address", "")
        self.sex = data.get("sex", "")
        self.phonenum = data.get("phonenum", "")


class Passenger:
    def __init__(self, data=None):
        data = data or {}
        self.firstname = data.get("firstname", "")
        self.lastname = data.get("lastname", "")
        self.ticketno = data.get("ticketno", "")
        self.national = data.get("national", "")
        self.cardexpired = data.get("cardexpired", "")
        self.sex = data.get("sex", "M")
        self.cardtype = data.get("cardtype", "PP")
        self.birthday = data.get("birthday", "")
        self.cardnum = data.get("cardnum", "")
        self.cardissueplace = data.get("cardissueplace", "")


class LuggageItem:
    def __init__(self, data=None):
        data = data or {}
        self.dep = data.get("dep", "")
        self.pc = data.get("pc", -1)
        self.arr = data.get("arr", "")
        self.weightPerPC = data.get("weightPerPC", 0)


class Luggage:
    def __init__(self, data=None):
        data = data or {}
        self.passengerName = data.get("passengerName", "")
        self.isDb = data.get("isDb", False)
        self.cardType = data.get("cardType", "")
        self.cardNum = data.get("cardNum", "")
        self.luggageItems = [LuggageItem(item) for item in data.get("luggageItems", [])]


class Seat:
    def __init__(self, data=None):
        data = data or {}
        self.paySeatPrice = data.get("paySeatPrice", 0)
        self.selectedSeatNo = data.get("selectedSeatNo", "")
        self.flightNo = data.get("flightNo", "")
        self.name = data.get("name", "")
        self.paySeatCurrency = data.get("paySeatCurrency", "")


class Order:
    """标准 Order 对象, 与 VJ 传参格式一致"""

    @staticmethod
    def form_dict(data):
        obj = Order()
        obj.flightnotime = data.get("flightnotime", {})
        obj.isFlush = data.get("isFlush", False)
        obj.brushkey = data.get("brushkey", "")
        obj.currency = data.get("currency", "")
        obj.session = data.get("session", "")
        obj.producttype = data.get("producttype", 0)
        obj.pricebig = data.get("pricebig", "")
        obj.fromtime = data.get("fromtime", "")
        obj.isbrushbooking = data.get("isbrushbooking", 1)
        obj.luggageprice = data.get("luggageprice", 0)
        obj.price62 = data.get("price62", "")
        obj.profit = data.get("profit", 0)
        obj.brushtime = data.get("brushtime", "")
        obj.contact = Contact(data.get("contact", {}))
        obj.ispay = data.get("ispay", True)
        obj.paypnr = data.get("paypnr", "")
        obj.lfprice = data.get("lfprice", 0)
        obj.forcecurrency = data.get("forcecurrency", "")
        obj.metadata = data.get("metadata", "")
        obj.orderid = data.get("orderid", 0)
        obj.otanamestr = data.get("otanamestr", "")
        obj.oriprice = data.get("oriprice", 0)
        obj.pnr = data.get("pnr", "")
        obj.policyinfo = data.get("policyinfo", {})
        obj.passengersinfo = data.get("passengersinfo", "")
        obj.maxSeats = data.get("maxSeats", -1)
        obj.reason = data.get("reason", "")
        obj.totalprice = data.get("totalprice", 0)
        obj.rettime = data.get("rettime", "")
        obj.ttsname = data.get("ttsname", "")
        obj.forcepay = data.get("forcepay", False)
        obj.seats = [Seat(s) for s in data.get("seats", [])]
        obj.luggages = [Luggage(l) for l in data.get("luggages", [])]
        obj.passengers = [Passenger(p) for p in data.get("passengers", [])]
        obj.remark = data.get("remark", "")
        obj.retDate = data.get("retDate") or data.get("retdate", "")
        obj.priceinfo = data.get("priceinfo", "")
        obj.plmpnr = data.get("plmpnr", "")
        obj.createtime = data.get("createtime", "")
        obj.retFlightNo = data.get("retFlightNo") or data.get("retflightno", "")
        obj.method = data.get("method", "")
        obj.isspecial = data.get("isspecial", False)
        obj.carrier = data.get("carrier", "")
        obj.fromDate = data.get("fromDate") or data.get("fromdate", "")
        obj.dptAirport = data.get("dptAirport") or data.get("dptairport", "")
        obj.arrAirport = data.get("arrAirport") or data.get("arrairport", "")
        obj.fromFlightNo = data.get("fromFlightNo") or data.get("fromflightno", "")
        obj.realtimeprice = data.get("realtimeprice", 0)
        obj.hasdevied = data.get("hasdevied", False)
        obj.returnrettime = data.get("returnrettime", "")
        obj.orderno = data.get("orderno", "")
        obj.inorderno = data.get("inorderno", "")
        obj.brushstatus = data.get("brushstatus", 2)
        obj.returnfromtime = data.get("returnfromtime", "")
        return obj


# ==================== 辅助函数 ====================

def config_log():
    level = logging.DEBUG
    fmt = '%(asctime)s - %(levelname)s - %(message)s - %(thread)d'
    logging.basicConfig(filename='VUBOOK.log', level=level, format=fmt)
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(fmt))
    logging.getLogger('').addHandler(console)


# ==================== VUB2BBooker 核心类 ====================

class VUB2BBooker:

    def __init__(self):
        self.session = requests.Session()
        self.timeout = 30
        self.method = 'VUB2B'
        self.currency = "VND"
        self.session_token = None
        self.user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=28))

        # OA 日志 URL (与 VJ 完全一致, 通过 orderno 关联)
        self.logurl = "https://oa.tripto.cn/flightoa/order/addorderlog?orderid={orderno}&operator=robot&optname={mes}&optdesc={mesdesc}"
        self.rz_url = "https://oa.tripto.cn/flightoa/order/addorderlog?orderid={orderno}&operator=robot&optname={mes}&optdesc={mesdesc}&keyWordColor={keyWordColor}"

        # 公共 headers (Sabre ezycommerce 平台)
        self.session.headers.update({
            "Accept": "text/plain",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "AppContext": "ibe",
            "Content-Type": "application/json",
            "Origin": "https://booking.vietravelairlines.com",
            "Referer": "https://booking.vietravelairlines.com/",
            "Tenant-Identifier": TENANT_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "X-ClientVersion": "0.5.4036",
            "X-UserIdentifier": self.user_id,
            "Channel": "web",
            "languageCode": "zh-CN",
        })

        # 代理人登录相关
        self.agent_token = None        # JWT Bearer token (登录后填充)
        self.agent_logged_in = False
        self.iata_code = ""            # 代理人 IATA 编码 (登录后填充)
        self.agency_name = ""          # 代理机构名称
        self.login_credit = 0          # 登录响应中的可用额度 (Balance 401 时备用)

        # 汇率 (VND → CNY, 默认近似值, 运行时由 exchangerates 参数覆盖)
        self.vnd_to_cny_rate = 0.000257  # 1 VND ≈ 0.000257 CNY

        # 座位图缓存 (每次 book() 调用时重置)
        self._seat_map_cache = None

    # ==================== API 请求封装 ====================

    def _api(self, method, path, data=None, retries=3):
        """发送 API 请求, 自动管理 SessionToken 和 B2B JWT"""
        url = BASE_URL + "/" + path
        if self.session_token:
            self.session.headers["SessionToken"] = self.session_token
        else:
            self.session.headers.pop("SessionToken", None)

        # B2B JWT: 登录后始终携带 (web 通道支付也需要 B2B 认证)
        if self.agent_token:
            self.session.headers["Authorization"] = f"Bearer {self.agent_token}"
        else:
            self.session.headers.pop("Authorization", None)

        last_error = None
        for attempt in range(retries):
            try:
                if method == "GET":
                    resp = self.session.get(url, params=data, timeout=self.timeout)
                else:
                    resp = self.session.post(url, json=data, timeout=self.timeout)

                # 自动保存 sessiontoken
                token = resp.headers.get("sessiontoken")
                if token:
                    self.session_token = token

                return resp
            except Exception as e:
                last_error = e
                logging.warning(f"API 请求失败 (尝试 {attempt+1}/{retries}): {e}")
                time.sleep(2)

        logging.error(f"API 请求最终失败: {last_error}")
        return None

    # ==================== 代理 IP 管理 ====================

    def set_proxy(self):
        """设置随机代理端口 (astospider)"""
        try:
            port = random.choice(PROXY_PORT_RANGE)
            proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{port}"
            self.session.proxies = {"http": proxy_url, "https": proxy_url}
            logging.info(f"使用代理: {PROXY_HOST}:{port}")
        except Exception:
            logging.exception("代理设置错误:")

    # ==================== 代理人登录 ====================

    def agent_login(self, username, password):
        """
        登录 VU B2B 代理人平台
        API: POST TravelAgent/Login
        登录成功后:
          - 存储 JWT Bearer token (self.agent_token)
          - SessionToken 自动由 _api() 保存
          - 切换 Channel/AppContext 为代理人模式
          - 后续请求自动携带双重认证
        """
        logging.info(f"B2B 代理人登录: 用户={username}")

        # 临时切换到代理人登录所需的 headers
        self.session.headers["Channel"] = "travelagent"
        self.session.headers["AppContext"] = "manage"

        login_body = {
            "username": username,
            "password": password,
            "languageCode": "zh-CN",
        }

        resp = self._api("POST", "TravelAgent/Login", login_body)
        if resp is None:
            logging.error("代理人登录请求失败 (网络错误)")
            self.agent_logged_in = False
            return False

        if resp.status_code != 200:
            logging.error(f"代理人登录失败: HTTP {resp.status_code}, body={resp.text[:500]}")
            self.agent_logged_in = False
            # 恢复公共 headers
            self.session.headers["Channel"] = "web"
            self.session.headers["AppContext"] = "ibe"
            return False

        data = resp.json()

        # 提取 JWT Bearer token
        security_token = data.get("securityToken") or data.get("pssSessionIdentifier", "")
        if not security_token:
            logging.error(f"代理人登录失败: 响应中无 securityToken, body={json.dumps(data, ensure_ascii=False)[:500]}")
            self.agent_logged_in = False
            self.session.headers["Channel"] = "web"
            self.session.headers["AppContext"] = "ibe"
            return False

        # 提取代理人信息
        agent_info = data.get("travelAgent", {})
        agency = agent_info.get("agency", {})
        settings = agency.get("settings", {})

        self.iata_code = agency.get("iataCode", "")
        self.agency_name = agency.get("name", "")
        available_credit = settings.get("availableCredit", 0)
        is_prepaid = settings.get("prepaid", False)
        self.login_credit = available_credit  # 登录响应中的可用额度 (Balance 查询失败时备用)

        # 保存登录状态
        # session_token: 由 _api() 从响应 header 自动获取 (加密会话令牌)
        # agent_token: 从响应 body 获取 (JWT Bearer token)
        # 两者是不同的值, 后续请求需要同时携带:
        #   Header: SessionToken={session_token}  (会话令牌)
        #   Header: Authorization: Bearer {agent_token}  (JWT)
        self.agent_token = security_token
        self.agent_logged_in = True

        # 如果 _api() 没有从 header 获取到 sessiontoken, 则用 body 的 securityToken 兜底
        if not self.session_token:
            self.session_token = security_token
            logging.warning("登录响应 header 无 sessiontoken, 使用 body securityToken 兜底")

        logging.info(f"B2B 登录成功! IATA={self.iata_code}, 机构={self.agency_name}, "
                     f"可用额度={available_credit}, 预付={is_prepaid}")
        logging.debug(f"  session_token(前30): {str(self.session_token)[:30]}...")
        logging.debug(f"  agent_token(前30): {str(self.agent_token)[:30]}...")
        logging.debug(f"  两者相同: {self.session_token == self.agent_token}")

        # 登录后切回公共通道 (搜索/预订/支付均走 web+ibe, JWT 由 _api() 自动携带)
        self.session.headers["Channel"] = "web"
        self.session.headers["AppContext"] = "ibe"
        # 清空登录会话的 session_token, 让后续搜索在 web 通道建立全新会话
        # agent_token (JWT) 保留, 支付时仍可使用
        login_session_token = self.session_token
        self.session_token = None
        logging.debug(f"  清空 session_token (登录时的: {str(login_session_token)[:20]}...)")
        logging.debug(f"  搜索/预订/支付均使用 web 通道, B2B JWT 由 _api() 自动携带")

        return True

    def get_balance(self):
        """查询代理人账户余额 (需先登录)"""
        if not self.agent_logged_in:
            logging.warning("查询余额失败: 代理人未登录")
            return None
        # 临时切换到代理人通道
        old_channel = self.session.headers.get("Channel", "web")
        old_app = self.session.headers.get("AppContext", "ibe")
        self.session.headers["Channel"] = "travelagent"
        self.session.headers["AppContext"] = "manage"
        resp = self._api("GET", "TravelAgent/Balance")
        # 切回公共通道
        self.session.headers["Channel"] = old_channel
        self.session.headers["AppContext"] = old_app
        if resp and resp.status_code == 200:
            data = resp.json()
            balance = data.get("balance", 0)
            logging.info(f"代理人余额: {balance}")
            return balance
        logging.warning(f"查询余额失败: HTTP {resp.status_code if resp else 'N/A'}")
        return None

    # ==================== OA 日志 ====================

    def writelog(self, mesurl):
        """写入 OA 日志 (通过 orderno 关联)"""
        try:
            requests.get(mesurl, verify=False, timeout=30)
        except Exception:
            logging.exception('OA 日志写入失败:')

    def pay_run_log(self, orderno):
        """支付环节日志"""
        self.writelog(
            self.rz_url.format(orderno=orderno, mes="正在进行支付",
                               mesdesc="进入支付环节, 出现任何问题请人工核对",
                               keyWordColor="red"))

    # ==================== 货币转换 ====================

    def vnd_to_cny(self, vnd_amount):
        """VND 转 CNY (用于涨价校验)"""
        return math.ceil(float(vnd_amount) * self.vnd_to_cny_rate)

    # ==================== 乘客年龄分类 ====================

    def ageType(self, birthday, flightdate):
        """
        根据生日和航班出发日期判断乘客类型
        < 2岁 → INFANT (婴儿)
        2~12岁 → CHILD (儿童)
        > 12岁 → ADULT (成人)
        """
        birthday = datetime.datetime.strptime(birthday, '%Y-%m-%d')
        flightdate = datetime.datetime.strptime(flightdate, '%Y-%m-%d')
        delta = flightdate - birthday
        if delta < datetime.timedelta(days=2 * 365):
            return 'INFANT'
        elif delta < datetime.timedelta(days=12 * 365):
            return 'CHILD'
        else:
            return 'ADULT'

    # ==================== 判断是否国际线 ====================

    def is_international(self, dep_airport, arr_airport):
        """根据出发/到达机场判断是否国际航线"""
        dep_intl = dep_airport not in VN_AIRPORTS
        arr_intl = arr_airport not in VN_AIRPORTS
        return dep_intl or arr_intl

    # ==================== 搜索航班 ====================

    def search_flights(self, dep_airport, arr_airport, dep_date,
                       adult_count, child_count, infant_count):
        """
        搜索可用航班
        调用 Availability/SearchShop API
        """
        body = {
            "passengers": [
                {"code": "ADT", "count": adult_count},
                {"code": "CHD", "count": child_count},
                {"code": "INF", "count": infant_count},
            ],
            "routes": [{
                "fromAirport": dep_airport,
                "toAirport": arr_airport,
                "departureDate": dep_date,
                "startDate": dep_date,
                "endDate": dep_date,
                "cabin": None,
                "segmentKey": None,
                "routeIndex": 0,
            }],
            "currency": self.currency,
            "fareTypeCategories": None,
            "isManageBooking": False,
        }

        resp = self._api("POST", "Availability/SearchShop", body)
        if resp is None or resp.status_code != 200:
            return None
        return resp.json()

    # ==================== 匹配航班 ====================

    def find_flight(self, search_data, flight_no, dep_date=None):
        """
        从搜索结果中按航班号匹配航班, 固定选择 Economy Saver
        返回 {"flight":..., "fare":..., "route":...} 或 None

        匹配优先级:
          1. fare name 包含 "saver" (不区分大小写, 如 "Economy Saver", "Intl - Economy Saver")
          2. fareBasis 包含 "SAV" (如 "BSAVIN", "XSAV")
          3. 选最便宜的 (兜底)
        """
        routes = search_data.get("routes", [])
        if not routes:
            return None

        # 清理航班号 (去掉 VU 前缀)
        fn_clean = flight_no.strip().upper()
        if fn_clean.startswith("VU"):
            fn_clean = fn_clean[2:]

        for route in routes:
            flights = route.get("flights", [])
            for flight in flights:
                if flight.get("flightNumber", "").strip() == fn_clean:
                    # 找到了目标航班
                    fares = flight.get("fares", [])
                    if not fares:
                        logging.warning(f"航班 {fn_clean} 无可用票价")
                        return None

                    # 打印所有可用票价 (调试用)
                    for i, f in enumerate(fares):
                        logging.info(f"  票价[{i}]: name={f.get('name')}, "
                                     f"fareBasis={f.get('fareBasis')}, "
                                     f"price={f.get('price')} {self.currency}")

                    # 优先级 1: fare name 包含 "saver"
                    saver_fare = None
                    for fare in fares:
                        fare_name = fare.get("name", "").upper()
                        if "SAVER" in fare_name:
                            saver_fare = fare
                            logging.info(f"  匹配: name='{fare.get('name')}' (含 SAVER)")
                            break

                    # 优先级 2: fareBasis 包含 "SAV"
                    if saver_fare is None:
                        for fare in fares:
                            fb = fare.get("fareBasis", "").upper()
                            fb_code = ""
                            if fare.get("fareBundle"):
                                fb_code = fare["fareBundle"].get("bundleCode", "").upper()
                            if "SAV" in fb or "SAV" in fb_code:
                                saver_fare = fare
                                logging.info(f"  匹配: fareBasis='{fb}' (含 SAV)")
                                break

                    # 优先级 3: 选最便宜的 (兜底)
                    if saver_fare is None:
                        saver_fare = min(fares, key=lambda f: f.get("price", float("inf")))
                        logging.warning(f"  未找到 Saver 票价, 兜底选择最便宜: "
                                        f"name='{saver_fare.get('name')}', "
                                        f"price={saver_fare.get('price')} {self.currency}")

                    saver_fare["selected"] = True
                    if "serviceBundles" not in saver_fare:
                        saver_fare["serviceBundles"] = []

                    return {"flight": flight, "fare": saver_fare, "route": route}

        return None

    # ==================== 获取座位图 ====================

    def get_seat_map(self, flight, fare, passenger_count=1):
        """获取座位图 (在 PreBook 之前调用)"""
        fb_code = ""
        if fare.get("fareBundle"):
            fb_code = fare["fareBundle"].get("bundleCode", "")

        passenger_id = "ADT_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        body = {
            "currency": self.currency,
            "flights": [{
                "cabin": fare.get("cabin", "ECONOMY"),
                "departureDate": flight["departureDate"],
                "fareBundleCode": fb_code,
                "flightNumber": flight["flightNumber"],
                "carrierCode": flight.get("carrierCode", "VU"),
                "from": flight["from"],
                "to": flight["to"],
                "id": flight["id"],
                "fareBasis": fare.get("fareBasis", ""),
            }],
            "isCheckin": False,
            "isManageBooking": False,
            "passengerTypes": [{"code": "ADT", "count": passenger_count}],
            "passengers": [{
                "id": passenger_id,
                "code": "ADT",
                "ssrs": [],
            }],
            "isPrivileged": False,
        }

        resp = self._api("POST", "Seat/Map", body)
        if resp is None or resp.status_code != 200:
            return None
        return resp.json()

    # ==================== 匹配座位 ====================

    def find_seat_in_map(self, seat_map_data, seat_code):
        """
        从座位图中找到指定座位号的数据
        seat_code: 如 "10A", "28F"
        """
        if not seat_map_data:
            return None

        for fl in seat_map_data.get("flights", []):
            flight_id = fl.get("id")
            for sm in fl.get("seatMaps", []):
                leg_id = sm.get("legId")
                for row in sm.get("seatRows", []):
                    for seat in row.get("seats", []):
                        if seat.get("code") == seat_code and seat.get("isAvailable"):
                            return {
                                "flightId": flight_id,
                                "legId": leg_id,
                                "row": seat.get("row"),
                                "code": seat.get("code"),
                                "char": seat.get("char"),
                                "price": seat.get("price", 0),
                                "priceIncludingTax": seat.get("priceIncludingTax", 0),
                                "chargeCode": seat.get("chargeCode", ""),
                                "chargeDescription": seat.get("chargeDescription", ""),
                                "chargeCurrency": seat.get("chargeCurrency", self.currency),
                                "isExit": seat.get("isExit", False),
                            }
        return None

    # ==================== 构建乘客数据 ====================

    def _build_passenger_id(self, age_type):
        """生成乘客 ID"""
        suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"{age_type}_{suffix}"

    def _clean_legs(self, legs):
        """将搜索返回的 legs 转换为 PreBook 需要的简化格式"""
        cleaned = []
        for leg in legs:
            from_code = ""
            to_code = ""
            if isinstance(leg.get("from"), dict):
                from_code = leg["from"].get("code", "")
            else:
                from_code = leg.get("from", "")
            if isinstance(leg.get("to"), dict):
                to_code = leg["to"].get("code", "")
            else:
                to_code = leg.get("to", "")

            cleaned.append({
                "id": leg.get("id"),
                "departureDate": leg.get("departureDate"),
                "arrivalDate": leg.get("arrivalDate"),
                "flightTime": leg.get("flightTime"),
                "flightNumber": leg.get("flightNumber"),
                "equipmentType": leg.get("equipmentType"),
                "carrierCode": leg.get("carrierCode"),
                "legType": leg.get("legType", "Regular"),
                "stopOverTime": leg.get("stopoverTime", 0),
                "from": from_code,
                "to": to_code,
            })
        return cleaned

    # ==================== PreBook ====================

    def prebook(self, flight, fare, passengers_adt, passengers_chd, passengers_infant,
                order, seats=None, is_international=False):
        """
        提交预订预校验 (PreBook)
        包含: 乘客信息 + 联系人 + 航班 + 座位
        """
        flight_obj = flight
        fare_obj = fare

        # 构建 selectedFare
        selected_fare = dict(fare_obj)
        selected_fare["selected"] = True

        # 联系人信息
        contact = order.contact

        # 收集所有乘客 (成人 → 儿童 → 婴儿)
        all_passengers_data = []
        passenger_fares = []
        seats_list = []

        # 构建座位映射
        seat_map = {}
        if seats:
            for seat_item in seats:
                pname = seat_item.get("name", "")
                if pname not in seat_map:
                    seat_map[pname] = []
                seat_map[pname].append(seat_item)

        # ---- 成人 ----
        for p in passengers_adt:
            pid = self._build_passenger_id("ADT")
            pasname = f"{p.lastname}/{p.firstname}"

            # 座位
            p_seats = []
            if pasname in seat_map and hasattr(self, '_seat_map_cache'):
                for sm in seat_map[pasname]:
                    found = self.find_seat_in_map(self._seat_map_cache, sm["selectedSeatNo"])
                    if found:
                        p_seats.append({
                            "passengerId": pid,
                            "radixxGoIdentifier": None,
                            "flightId": found["flightId"],
                            "legId": found["legId"],
                            "row": found["row"],
                            "code": found["code"],
                            "taxCurrency": None,
                            "currency": found.get("chargeCurrency", self.currency),
                            "price": found["price"],
                            "priceIncludingTax": found["priceIncludingTax"],
                            "char": found["char"],
                            "chargeCode": found["chargeCode"],
                            "chargeDescription": found["chargeDescription"],
                            "isExit": found.get("isExit"),
                            "isFromServiceBundle": None,
                            "isTravelWithInfant": False,
                            "isUpsell": False,
                            "isSaved": False,
                        })
            seats_list.extend(p_seats)

            # 乘客对象
            p_data = {
                "passengerTypeCode": "ADT",
                "id": pid,
                "associateWithPassengerId": None,
                "selectedTravelCompanionId": None,
                "title": "MR" if p.sex == "M" else "MS",
                "firstName": p.firstname,
                "middleName": "",
                "lastName": p.lastname,
                "dateOfBirth": p.birthday,
                "gender": p.sex,
                "mobileNumber": "",
                "email": "",
                "frequentFlyerNumber": "",
                "documentNumber": "",
                "redressNumber": "",
                "knownTravelerNumber": "",
                "height": "",
                "weight": "",
                "nationality": "",
                "seats": p_seats,
                "services": [],  # 行李在 Extras 步骤中添加
                "contactInformation": {
                    "address": "",
                    "address2": "",
                    "city": "",
                    "country": p.national or "CN",
                    "state": "",
                    "phoneNumber": contact.phonenum or "",
                    "workPhoneNumber": "",
                    "postal": "",
                    "email": contact.email or "",
                    "fax": "",
                    "pager": "",
                },
                "apisInfo": {
                    "nationality": p.national or "CN",
                    "residenceCountry": p.national or "CN",
                    "documentNumber": p.cardnum or "",
                    "issuedBy": p.cardissueplace or "",
                    "passportExpireDate": p.cardexpired or "",
                    "birthCountry": "",
                    "birthState": "",
                    "birthCity": "",
                    "destinationCountry": "",
                    "destinationPostal": "",
                    "destinationState": "",
                    "destinationCity": "",
                    "destinationAddress": "",
                    "documentNumber2": "",
                    "documentType2": "",
                    "document2IssuedBy": "",
                    "document2ExpireDate": "",
                } if is_international else {
                    "nationality": p.national or "",
                    "residenceCountry": p.national or "",
                    "documentNumber": "",
                    "issuedBy": "",
                    "passportExpireDate": "",
                    "birthCountry": "",
                    "birthState": "",
                    "birthCity": "",
                    "destinationCountry": "",
                    "destinationPostal": "",
                    "destinationState": "",
                    "destinationCity": "",
                    "destinationAddress": "",
                    "documentNumber2": "",
                    "documentType2": "",
                    "document2IssuedBy": "",
                    "document2ExpireDate": "",
                },
            }
            all_passengers_data.append(p_data)

            # passengerFare
            passenger_fares.append({
                "passengerId": pid,
                "passengerTypeCode": "ADT",
                "passengerTypeName": "成人",
                "passengerTypeNamePlural": "成人们",
                "fareName": fare_obj.get("name"),
                "farePrice": fare_obj.get("price", 0),
                "farePriceWithoutTax": fare_obj.get("priceWithoutTax", 0),
                "fareDiscount": fare_obj.get("discount", 0),
            })

        # ---- 儿童 ----
        for p in passengers_chd:
            pid = self._build_passenger_id("CHD")
            pasname = f"{p.lastname}/{p.firstname}"

            p_seats = []
            if pasname in seat_map and hasattr(self, '_seat_map_cache'):
                for sm in seat_map[pasname]:
                    found = self.find_seat_in_map(self._seat_map_cache, sm["selectedSeatNo"])
                    if found:
                        p_seats.append({
                            "passengerId": pid,
                            "radixxGoIdentifier": None,
                            "flightId": found["flightId"],
                            "legId": found["legId"],
                            "row": found["row"],
                            "code": found["code"],
                            "taxCurrency": None,
                            "currency": found.get("chargeCurrency", self.currency),
                            "price": found["price"],
                            "priceIncludingTax": found["priceIncludingTax"],
                            "char": found["char"],
                            "chargeCode": found["chargeCode"],
                            "chargeDescription": found["chargeDescription"],
                            "isExit": found.get("isExit"),
                            "isFromServiceBundle": None,
                            "isTravelWithInfant": False,
                            "isUpsell": False,
                            "isSaved": False,
                        })
            seats_list.extend(p_seats)

            p_data = {
                "passengerTypeCode": "CHD",
                "id": pid,
                "associateWithPassengerId": None,
                "selectedTravelCompanionId": None,
                "title": "",
                "firstName": p.firstname,
                "middleName": "",
                "lastName": p.lastname,
                "dateOfBirth": p.birthday,
                "gender": p.sex,
                "mobileNumber": "",
                "email": "",
                "frequentFlyerNumber": "",
                "documentNumber": "",
                "redressNumber": "",
                "knownTravelerNumber": "",
                "height": "",
                "weight": "",
                "nationality": "",
                "seats": p_seats,
                "services": [],
                "contactInformation": {
                    "address": "",
                    "address2": "",
                    "city": "",
                    "country": p.national or "CN",
                    "state": "",
                    "phoneNumber": contact.phonenum or "",
                    "workPhoneNumber": "",
                    "postal": "",
                    "email": contact.email or "",
                    "fax": "",
                    "pager": "",
                },
                "apisInfo": {
                    "nationality": p.national or "CN",
                    "residenceCountry": p.national or "CN",
                    "documentNumber": (p.cardnum or "") if is_international else "",
                    "issuedBy": (p.cardissueplace or "") if is_international else "",
                    "passportExpireDate": (p.cardexpired or "") if is_international else "",
                    "birthCountry": "",
                    "birthState": "",
                    "birthCity": "",
                    "destinationCountry": "",
                    "destinationPostal": "",
                    "destinationState": "",
                    "destinationCity": "",
                    "destinationAddress": "",
                    "documentNumber2": "",
                    "documentType2": "",
                    "document2IssuedBy": "",
                    "document2ExpireDate": "",
                },
            }
            all_passengers_data.append(p_data)

            passenger_fares.append({
                "passengerId": pid,
                "passengerTypeCode": "CHD",
                "passengerTypeName": "儿童",
                "passengerTypeNamePlural": "儿童们",
                "fareName": fare_obj.get("name"),
                "farePrice": fare_obj.get("price", 0),  # 儿童票价 (API 会自动计算)
                "farePriceWithoutTax": fare_obj.get("priceWithoutTax", 0),
                "fareDiscount": fare_obj.get("discount", 0),
            })

        # ---- 婴儿 ----
        for p in passengers_infant:
            pid = self._build_passenger_id("INF")

            p_data = {
                "passengerTypeCode": "INF",
                "id": pid,
                "associateWithPassengerId": all_passengers_data[0]["id"] if all_passengers_data else None,
                "selectedTravelCompanionId": None,
                "title": "",
                "firstName": p.firstname,
                "middleName": "",
                "lastName": p.lastname,
                "dateOfBirth": p.birthday,
                "gender": p.sex,
                "mobileNumber": "",
                "email": "",
                "frequentFlyerNumber": "",
                "documentNumber": "",
                "redressNumber": "",
                "knownTravelerNumber": "",
                "height": "",
                "weight": "",
                "nationality": "",
                "seats": [],  # 婴儿不占座
                "services": [],
                "contactInformation": {
                    "address": "",
                    "address2": "",
                    "city": "",
                    "country": p.national or "CN",
                    "state": "",
                    "phoneNumber": contact.phonenum or "",
                    "workPhoneNumber": "",
                    "postal": "",
                    "email": contact.email or "",
                    "fax": "",
                    "pager": "",
                },
                "apisInfo": {
                    "nationality": p.national or "CN",
                    "residenceCountry": p.national or "CN",
                    "documentNumber": (p.cardnum or "") if is_international else "",
                    "issuedBy": (p.cardissueplace or "") if is_international else "",
                    "passportExpireDate": (p.cardexpired or "") if is_international else "",
                    "birthCountry": "",
                    "birthState": "",
                    "birthCity": "",
                    "destinationCountry": "",
                    "destinationPostal": "",
                    "destinationState": "",
                    "destinationCity": "",
                    "destinationAddress": "",
                    "documentNumber2": "",
                    "documentType2": "",
                    "document2IssuedBy": "",
                    "document2ExpireDate": "",
                },
            }
            all_passengers_data.append(p_data)

            passenger_fares.append({
                "passengerId": pid,
                "passengerTypeCode": "INF",
                "passengerTypeName": "婴儿",
                "passengerTypeNamePlural": "婴儿们",
                "fareName": fare_obj.get("name"),
                "farePrice": fare_obj.get("price", 0),
                "farePriceWithoutTax": fare_obj.get("priceWithoutTax", 0),
                "fareDiscount": fare_obj.get("discount", 0),
            })

        # 构建完整 PreBook 请求体
        body = {
            "contact": {
                "address": contact.address or "Missing Address",
                "address2": "",
                "city": contact.city or "Missing City",
                "country": contact.nation or "CN",
                "state": "NA",
                "phoneNumber": contact.phonenum or "",
                "workPhoneNumber": "",
                "postal": contact.postcode or "00000",
                "email": contact.email or "",
                "fax": "",
                "pager": "",
            },
            "emergencyContact": {
                "firstName": all_passengers_data[0]["firstName"] if all_passengers_data else "",
                "lastName": all_passengers_data[0]["lastName"] if all_passengers_data else "",
                "reference": contact.phonenum or "",
                "referenceType": 0,
            },
            "flights": [{
                "route": 0,
                "key": flight_obj["key"],
                "id": flight_obj["id"],
                "carrierCode": flight_obj.get("carrierCode", "VU"),
                "flightNumber": flight_obj["flightNumber"],
                "selectedFare": selected_fare,
                "fareId": fare_obj.get("id"),
                "fareBasis": fare_obj.get("fareBasis"),
                "departureDate": flight_obj["departureDate"],
                "arrivalDate": flight_obj["arrivalDate"],
                "from": flight_obj["from"],
                "to": flight_obj["to"],
                "isInternational": flight_obj.get("isInternational", is_international),
                "passengerFares": passenger_fares,
                "price": fare_obj.get("price", 0),
                "priceWithoutTax": fare_obj.get("priceWithoutTax", 0),
                "legs": self._clean_legs(flight_obj.get("legs", [])),
                "cabin": fare_obj.get("cabin", "ECONOMY"),
            }],
            "recaptchaResponse": None,
            "hcaptchaToken": None,
            "passengers": all_passengers_data,
            "currency": self.currency,
            "fareTypeCategories": None,
            "promoCode": "",
            "tracking": {},
            "isExternallyPriced": False,
            "languageCode": "zh-CN",
        }

        resp = self._api("POST", "Booking/PreBook", body)
        if resp is None or resp.status_code != 200:
            if resp is not None:
                logging.error(f"PreBook 失败: HTTP {resp.status_code}, body={resp.text[:1000]}")
            return None, body
        return resp.json(), body

    # ==================== B2B 支付 ====================

    def create_payment(self, prebook_data, prebook_body, orderno):
        """
        创建预订并发起支付
        B2B 模式下优先使用 Agency Account (INVC, providerId=invoice)
        未登录时降级为 Pay Later
        支付始终在 web 通道执行 (与 PreBook 同一会话), JWT 由 _api() 自动携带
        """
        # 选择支付方式: B2B 优先 invoice, 否则 paylater
        payment_methods = []
        payment_option_id = ""
        method_id = ""

        all_options = prebook_data.get("paymentOptions", [])

        # 打印所有支付选项 (调试用)
        for opt in all_options:
            logging.info(f"  paymentOption: id={opt.get('id')}, disabled={opt.get('disabled')}, "
                         f"methods={[m.get('id') for m in opt.get('paymentMethods', [])]}")

        if self.agent_logged_in:
            # B2B 模式: 找 invoice (Agency Account / INVC)
            for opt in all_options:
                if opt.get("id") == "invoice" and not opt.get("disabled"):
                    payment_methods = opt.get("paymentMethods", [])
                    payment_option_id = "invoice"
                    method_id = "internal:invoice"
                    break

            if not payment_option_id:
                # invoice 不可用, 尝试 paylater
                logging.warning("B2B: invoice 不可用, 尝试 paylater")
                for opt in all_options:
                    if opt.get("id") == "paylater" and not opt.get("disabled"):
                        payment_methods = opt.get("paymentMethods", [])
                        payment_option_id = "paylater"
                        method_id = "paylater:paylater"
                        break
        else:
            # 公共模式: 用 paylater
            for opt in all_options:
                if opt.get("id") == "paylater" and not opt.get("disabled"):
                    payment_methods = opt.get("paymentMethods", [])
                    payment_option_id = "paylater"
                    method_id = "paylater:paylater"
                    break

        # 兜底: 用第一个非 disabled 的支付方式
        if not payment_option_id:
            for opt in all_options:
                if not opt.get("disabled"):
                    payment_methods = opt.get("paymentMethods", [])
                    payment_option_id = opt["id"]
                    method_id = payment_methods[0]["id"] if payment_methods else "paylater:paylater"
                    break

        if not payment_option_id:
            logging.error("未找到任何可用支付方式")
            return None

        # 支付金额
        amount = prebook_data.get("reservationBalance",
                                  prebook_data.get("totalPrice", 0))

        # 从预订结果提取乘客/联系人
        contact = prebook_data.get("contact", {})
        passengers = prebook_data.get("passengers", [])
        first_pax = passengers[0] if passengers else {}

        payment_request = {
            "providerId": payment_option_id,
            "paymentMethodId": method_id,
            "amount": amount,
            "basePaymentAmount": amount,
            "currency": self.currency,
            "baseCurrency": self.currency,
            "exchangeRate": 1,
            "confirmationNumber": prebook_data.get("confirmationNumber", ""),
            "bookingLastName": first_pax.get("lastName", ""),
            "iataCode": self.iata_code,  # B2B 登录后的 IATA 编码
            "isModifyPayment": False,
            "hasPaymentFee": False,
            "signUpToNewsletter": False,
            "areSeatsCached": False,
            "address": contact.get("address", ""),
            "address2": contact.get("address2", ""),
            "city": contact.get("city", ""),
            "postal": contact.get("postal", ""),
            "country": contact.get("country", ""),
            "email": contact.get("email", ""),
            "mobileNumber": contact.get("phoneNumber", ""),
            "state": contact.get("state", ""),
            "firstName": first_pax.get("firstName", ""),
            "lastName": first_pax.get("lastName", ""),
            "gender": first_pax.get("gender", ""),
            "birthDate": first_pax.get("dateOfBirth", ""),
            "nationality": first_pax.get("apisInfo", {}).get("nationality", ""),
            "title": first_pax.get("title", ""),
            "languageCode": "zh-CN",
            "receiptLanguageCode": "zh-CN",
            "firebaseCloudMessagingToken": "",
            "successUrl": "/zh/confirmation",
            "failureUrl": "/zh/payment",
            "vouchers": [],
            "invoiceDetails": None,
            "receiptDetails": None,
        }

        body = {
            "booking": prebook_body,
            "upsell": {},
            "payment": payment_request,
            "travelAgentFees": None,
        }

        logging.info(f"[支付] 金额: {amount:,.0f} {self.currency}, "
                     f"方式: {payment_option_id}/{method_id}, "
                     f"IATA: {self.iata_code}, B2B: {self.agent_logged_in}")

        # B2B 支付: 保持在 web 通道 (与 PreBook 同一会话)
        # agent_token 已在 _api() 中自动携带, 无需切换 Channel/AppContext

        resp = self._api("POST", "Booking/CreateAndProcessPayment", body)

        # 支付后保持 web 通道 (无需切换)

        if resp is None:
            logging.error("[支付] 请求失败 (网络错误)")
            return None
        if resp.status_code != 200:
            logging.error(f"[支付] HTTP {resp.status_code}: {resp.text[:500]}")
            return None

        result = resp.json()

        # 记录支付结果
        if result.get("success"):
            booking = result.get("booking", {})
            cn = booking.get("confirmationNumber", "")
            wid = booking.get("webBookingId", "")
            logging.info(f"[支付成功] PNR={cn}, webBookingId={wid}")
        else:
            errors = result.get("errors", [])
            for e in errors:
                logging.error(f"[支付错误] {e.get('message', '')}")

        return result

    # ==================== 主流程 ====================

    def book(self, order, resdict=None, exchangerates=None, dry_run=False):
        """
        VU B2B 订票主流程
        参数格式与 VJ 的 VJB2BBooker.book() 完全一致

        Args:
            order: Order 对象 (通过 Order.form_dict({...}) 构建)
            resdict: 结果字典 (回填 PNR, 支付状态等), 如传 None 则自动创建
            exchangerates: 实时汇率表 (dict, 如 {"VND": 0.000257, "USD": 6.7564, ...})
                           来自 booker.json 的 exchangerate 字段
            dry_run: 试运行模式 (默认 False). 设为 True 时跳过支付, 仅验证前置流程
        """
        if resdict is None:
            resdict = {}
        # 使用实时汇率表更新汇率 (优先使用传入值)
        if exchangerates and isinstance(exchangerates, dict):
            rate = exchangerates.get(self.currency, None)
            if rate and float(rate) > 0:
                self.vnd_to_cny_rate = float(rate)
                logging.info(f"使用实时汇率: 1 {self.currency} = {self.vnd_to_cny_rate} CNY (来自 exchangerates)")
            else:
                logging.warning(f"exchangerates 中无 {self.currency} 汇率, 使用默认值: {self.vnd_to_cny_rate}")
        else:
            logging.info(f"未提供汇率表, 使用默认汇率: 1 {self.currency} = {self.vnd_to_cny_rate} CNY")

        passengers_adt = []
        passengers_chd = []
        passengers_infant = []

        # 解析机场和城市
        dptcity = order.dptAirport.split('|')[0] if '|' in order.dptAirport else order.dptAirport
        arrcity = order.arrAirport.split('|')[-1] if '|' in order.arrAirport else order.arrAirport
        fromdate = order.fromDate.split('|')[0]

        self.writelog(self.logurl.format(
            orderno=order.orderno, mes="开始订票",
            mesdesc=f"VU B2B 订票, 航班:{order.fromFlightNo}, 日期:{fromdate}, {dptcity}->{arrcity}"))

        # ---- 1. 分类乘客 ----
        for passenger in order.passengers:
            age_type = self.ageType(passenger.birthday, fromdate)
            if age_type == 'INFANT':
                passengers_infant.append(passenger)
            elif age_type == 'CHILD':
                passengers_chd.append(passenger)
            else:
                passengers_adt.append(passenger)

        adt_count = len(passengers_adt)
        chd_count = len(passengers_chd)
        inf_count = len(passengers_infant)
        total_pax = adt_count + chd_count + inf_count

        self.writelog(self.logurl.format(
            orderno=order.orderno, mes="乘客信息",
            mesdesc=f"成人:{adt_count}, 儿童:{chd_count}, 婴儿:{inf_count}"))

        resdict["passenger"] = "|".join(
            [f"{p.lastname}/{p.firstname}" for p in order.passengers])

        # ---- 2. 设置代理 IP ----
        try:
            self.set_proxy()
        except Exception:
            logging.warning("代理 IP 设置失败, 使用直连")

        # ---- 3. B2B 代理人登录 ----
        booking_account = resdict.get("bookingAccount", "")
        booking_pwd = resdict.get("bookingAccountPwd", "")
        if booking_account and booking_pwd:
            login_ok = self.agent_login(booking_account, booking_pwd)
            if login_ok:
                self.writelog(self.logurl.format(
                    orderno=order.orderno, mes="B2B登录",
                    mesdesc=f"代理人登录成功, IATA={self.iata_code}, 机构={self.agency_name}"))
                # 查询余额
                balance = self.get_balance()
                if balance is not None:
                    resdict["availableCredits"] = balance
                    self.writelog(self.logurl.format(
                        orderno=order.orderno, mes="账户余额",
                        mesdesc=f"可用额度: {balance}"))
                else:
                    # Balance API 401 时, 使用登录响应中的 availableCredit 作为备用
                    resdict["availableCredits"] = self.login_credit
                    if self.login_credit:
                        self.writelog(self.logurl.format(
                            orderno=order.orderno, mes="账户余额",
                            mesdesc=f"可用额度(登录响应): {self.login_credit}"))
                # B2B 支付方式: Agency Account (INVC), 无卡号
                resdict["payCardNo"] = ""
            else:
                self.writelog(self.rz_url.format(
                    orderno=order.orderno, mes="B2B登录失败",
                    keyWordColor="red",
                    mesdesc="代理人登录失败, 将使用公共通道预订"))
        else:
            logging.info("未提供代理人账号, 使用公共通道")

        # ---- 4. 搜索航班 ----
        self.writelog(self.logurl.format(
            orderno=order.orderno, mes="搜索航班中",
            mesdesc=f"{dptcity} -> {arrcity}, {fromdate}"))

        search_data = self.search_flights(
            dptcity, arrcity, fromdate,
            adt_count, chd_count, inf_count)

        if not search_data:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "搜索航班失败"
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="订票失败", mesdesc=resdict["msg"]))
            return

        routes = search_data.get("routes", [])
        if not routes or not routes[0].get("flights"):
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "未找到可用航班"
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="订票失败", mesdesc=resdict["msg"]))
            return

        self.writelog(self.logurl.format(
            orderno=order.orderno, mes="搜索成功",
            mesdesc=f"找到 {len(routes[0].get('flights', []))} 个航班"))

        # ---- 5. 匹配航班 ----
        result = self.find_flight(search_data, order.fromFlightNo, fromdate)
        if not result:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = f"未找到航班 {order.fromFlightNo}"
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="订票失败", mesdesc=resdict["msg"]))
            return

        flight = result["flight"]
        fare = result["fare"]

        # 校验起飞时间
        dep_time = flight.get("departureDate", "")
        oa_dep_time = order.flightnotime.get(order.fromFlightNo, "")
        if oa_dep_time:
            # 规范化时间格式比较
            dep_clean = dep_time.replace("T", " ").replace("/", "-")
            oa_clean = oa_dep_time.replace("T", " ").replace("/", "-")
            # 只比较日期+时间部分 (去掉秒后差异)
            if dep_clean[:16] != oa_clean[:16]:
                resdict["payStatus"] = "12"
                resdict["orderStatus"] = "0"
                resdict["msg"] = f"航班时间变动, 官网:{dep_time}, OA:{oa_dep_time}"
                self.writelog(self.logurl.format(
                    orderno=order.orderno, mes="订票失败", mesdesc=resdict["msg"]))
                return

        fare_price = fare.get("price", 0)
        fare_name = fare.get("name", "Economy Saver")
        self.writelog(self.logurl.format(
            orderno=order.orderno, mes="选择航班",
            mesdesc=f"VU{flight['flightNumber']} | {fare_name} | {fare_price:,.0f} {self.currency}"))

        # ---- 6. 判断是否国际线 ----
        intl = self.is_international(dptcity, arrcity)
        if intl:
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="航线类型",
                mesdesc="国际航线, 需要护照信息"))

        # ---- 7. 获取座位图 (如果有选座需求) ----
        self._seat_map_cache = None
        if order.seats:
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="获取座位图",
                mesdesc=f"需要为 {len(order.seats)} 个选座请求匹配座位"))
            seat_map_data = self.get_seat_map(flight, fare, total_pax)
            if seat_map_data:
                self._seat_map_cache = seat_map_data
            else:
                self.writelog(self.rz_url.format(
                    orderno=order.orderno, mes="选座警告",
                    mesdesc="获取座位图失败, 将跳过选座",
                    keyWordColor="red"))

        # ---- 8. 构建行李信息 ----
        luggage_services = {}
        for luggage_obj in order.luggages:
            for item in luggage_obj.luggageItems:
                pname = luggage_obj.passengerName
                if pname not in luggage_services:
                    luggage_services[pname] = {}
                luggage_services[pname][item.dep] = int(item.weightPerPC)

        if luggage_services:
            self.writelog(self.rz_url.format(
                orderno=order.orderno, mes="行李信息",
                keyWordColor="red", mesdesc=str(luggage_services)))

        # ---- 9. PreBook ----
        self.writelog(self.logurl.format(
            orderno=order.orderno, mes="提交预订中",
            mesdesc="正在提交 PreBook..."))

        seats_data = None
        if order.seats:
            seats_data = [{"name": s.name, "selectedSeatNo": s.selectedSeatNo,
                           "flightNo": s.flightNo} for s in order.seats]

        prebook_data, prebook_body = self.prebook(
            flight, fare,
            passengers_adt, passengers_chd, passengers_infant,
            order, seats=seats_data, is_international=intl)

        if not prebook_data:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "PreBook 提交失败"
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="订票失败", mesdesc=resdict["msg"]))
            return

        # 保存 PreBook body (支付时需要)
        self.last_prebook_body = prebook_body

        # ---- 10. 解析 PreBook 结果 ----
        total_price = prebook_data.get("totalPrice", 0)
        web_booking_id = prebook_data.get("webBookingId", "")
        confirmation_number = prebook_data.get("confirmationNumber", "")

        self.writelog(self.logurl.format(
            orderno=order.orderno, mes="PreBook 成功",
            mesdesc=f"预订ID:{web_booking_id}, 总价:{total_price:,.0f} {self.currency}"))

        # ---- 11. VND → CNY 涨价校验 ----
        cny_amount = self.vnd_to_cny(total_price)
        exchange_rate = self.vnd_to_cny_rate

        resdict["exchangeRate"] = str(exchange_rate)
        min_profit = resdict.get("minProfit", 0)
        self.writelog(self.logurl.format(
            orderno=order.orderno, mes="价格校验",
            mesdesc=f"VND总价:{total_price:,.0f}, 汇率:{exchange_rate}, CNY约:{cny_amount}, "
                    f"订单价:{order.totalprice}, minProfit:{min_profit}"))

        if order.totalprice < cny_amount + min_profit:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = f"涨价, 订单价:{order.totalprice}, 实际CNY:{cny_amount}, 超出:{cny_amount - order.totalprice}"
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="订票失败", mesdesc=resdict["msg"]))
            return

        # ---- 12. 订单状态检查 ----
        url_order_status = "https://oa.tripto.cn/flightoa/order/getstatus"
        querystring = {"orderId": order.orderno}
        for attempt in range(3):
            try:
                resp = requests.get(url_order_status, params=querystring, timeout=20)
                logging.info(f"{order.orderno} 支付前出票状态: {resp.text}")
                if resp.text == "true":
                    break  # 可以出票
                elif resp.text == "false":
                    resdict["payStatus"] = "12"
                    resdict["orderStatus"] = "0"
                    resdict["msg"] = "客人可能已经申请退票, 请检查状态..."
                    self.writelog(self.rz_url.format(
                        orderno=order.orderno, mes="支付失败",
                        keyWordColor="red", mesdesc=resdict["msg"]))
                    return
            except Exception:
                logging.error("请求订单状态超时, 正在重试...")

        # ---- 13. 填写结果 (PreBook 已完成) ----
        resdict["bookingOrderId"] = order.orderno
        resdict["bookingAllPrice"] = str(total_price)
        resdict["bookingCurrency"] = self.currency
        # confirmationNumber 是真实 PNR (6位码), 仅在支付后才有值
        # webBookingId 是 Sabre 内部会话 ID (长hex串), 不是 PNR
        resdict["bookingPnr"] = confirmation_number or ""
        resdict["bookingStatus"] = "1"  # PreBook 完成
        resdict["payStatus"] = "0"  # 待支付
        resdict["msg"] = "PreBook 完成, 待支付"

        if confirmation_number:
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="预订完成",
                mesdesc=f"PNR:{confirmation_number}, 总价:{total_price:,.0f} {self.currency}"))
        else:
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="预订完成",
                mesdesc=f"PreBook成功, webBookingId:{web_booking_id}, 总价:{total_price:,.0f} {self.currency}, PNR将在支付后生成"))

        # ---- 14. 支付 (前置校验全部通过, 直接支付) ----
        if dry_run:
            # 试运行模式: 跳过支付, 仅验证前置流程
            resdict["payStatus"] = "0"
            resdict["msg"] = "dry_run 模式, 跳过支付 (前置校验全部通过)"
            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="跳过支付(dry_run)",
                mesdesc="试运行模式, 前置校验全部通过, 未执行支付"))
            logging.info(f"[{order.orderno}] dry_run: 前置流程全部通过, 跳过支付")
        else:
            # B2B 支付前检查: 如果未登录, 尝试从 resdict 获取账号登录
            if not self.agent_logged_in and booking_account and booking_pwd:
                self.writelog(self.rz_url.format(
                    orderno=order.orderno, mes="支付前登录",
                    keyWordColor="red",
                    mesdesc="尝试在支付前进行B2B登录"))
                self.agent_login(booking_account, booking_pwd)

            self.writelog(self.logurl.format(
                orderno=order.orderno, mes="准备支付",
                mesdesc=f"B2B={self.agent_logged_in}, 前置校验通过, 调用支付接口"))
            self.pay_run_log(order.orderno)

            payment_data = self.create_payment(prebook_data, prebook_body, order.orderno)
            if payment_data and payment_data.get("success"):
                booking = payment_data.get("booking", {})
                cn = booking.get("confirmationNumber", "")
                resdict["payStatus"] = "21"  # 支付成功
                resdict["bookingPnr"] = cn or resdict["bookingPnr"]
                resdict["payCardNo"] = ""  # B2B INVC 无卡号
                resdict["msg"] = "支付成功"

                # ── 购票成功: 打印乘客信息 + PNR ──
                pax_lines = []
                for p in order.passengers:
                    pax_lines.append(
                        f"{p.lastname}/{p.firstname} | {p.sex} | {p.birthday} | {p.national}")
                pax_detail = " ; ".join(pax_lines)

                success_msg = (
                    f"=== 购票成功 === "
                    f"PNR:{cn} | 航班:{order.fromFlightNo} | "
                    f"日期:{fromdate} | {dptcity}->{arrcity} | "
                    f"总价:{total_price:,.0f} {self.currency} | "
                    f"乘客: {pax_detail}"
                )
                logging.info(f"[{order.orderno}] {success_msg}")
                self.writelog(self.logurl.format(
                    orderno=order.orderno, mes="购票成功",
                    mesdesc=f"PNR:{cn}, 乘客:{resdict.get('passenger', '')}, "
                            f"航班:{order.fromFlightNo}, {dptcity}->{arrcity}, "
                            f"总价:{total_price:,.0f} {self.currency}"))
            else:
                resdict["payStatus"] = "12"
                resdict["orderStatus"] = "0"
                err_msg = ""
                if payment_data:
                    errors = payment_data.get("errors", [])
                    err_msg = "; ".join([e.get("message", "") for e in errors])
                resdict["msg"] = f"支付失败: {err_msg}" if err_msg else "支付失败, 请检查代理人账户"
                self.writelog(self.rz_url.format(
                    orderno=order.orderno, mes="支付失败",
                    keyWordColor="red",
                    mesdesc=resdict["msg"]))

        logging.info(f"VU B2B 订票完成: orderno={order.orderno}, resdict={json.dumps(resdict, ensure_ascii=False)}")


# ==================== 测试 ====================

if __name__ == '__main__':
    config_log()

    # 模拟 booker.json 中的 exchangerate 字段 (实时汇率)
    exchange_rates = {
        "VND": 0.000257,
        "USD": 6.7564,
        "CNY": 1.0,
        "EUR": 7.85093,
        "GBP": 9.084651,
        "THB": 0.208145,
        "KHR": 0.001704,
        "LAK": 0.000311,
        "HKD": 0.86271,
        "SGD": 5.362999,
        "MYR": 1.669896,
        "JPY": 0.04222,
        "KRW": 0.004488,
        "TWD": 0.214721,
        "AUD": 4.786908,
        "CAD": 5.025421,
        "INR": 0.071409,
    }

    # 模拟 booker.json 中的 bookdata 字段 (注意: 实际传输是小写字段名)
    obj = Order.form_dict({
        "flightnotime": {
            "VU750": "2026-07-26 05:45:00"
        },
        "isFlush": False,
        "brushkey": "",
        "currency": "VND",
        "session": "",
        "producttype": 0,
        "pricebig": "",
        "fromtime": "2026-07-26 05:45:00",
        "isbrushbooking": 1,
        "luggageprice": 0,
        "price62": "",
        "profit": 0,
        "brushtime": "",
        "contact": {
            "city": "",
            "firstname": "Rui",
            "lastname": "Pu",
            "ctripemail": "",
            "useGuestMail": False,
            "nation": "",
            "email": "ybooking@126.com",
            "postcode": "",
            "address": "",
            "sex": "",
            "phonenum": "18580215023"
        },
        "ispay": True,
        "paypnr": "",
        "lfprice": 0,
        "forcecurrency": "",
        "metadata": "{}",
        "orderid": 0,
        "otanamestr": "DINH/THI NGOC LE",
        "oriprice": 276,
        "pnr": "",
        "policyinfo": {
            "ob": "1070000.00,VND,0.000257,274.99CNY",
            "obcurrency": "VND",
            "oriprice": 276,
            "obprice": 439000.0,
            "addinfo": {
                "carrier": -7.0,
                "qujian": -2.5
            },
            "payinfo": {
                "payCurrency": ""
            }
        },
        "passengersinfo": "",
        "maxSeats": -1,
        "reason": "",
        "totalprice": 1500,  # 测试用 CNY 价格 (需大于等于 VND总价×汇率 - minProfit)
        "rettime": "",
        "ttsname": "ltpk",
        "forcepay": False,
        "seats": [],
        "luggages": [],
        "passengers": [
            {
                "firstname": "THI NGOC LE",
                "ticketno": "",
                "national": "VN",
                "cardexpired": "",
                "sex": "F",
                "cardtype": "O",
                "birthday": "1980-05-22",
                "cardnum": "",
                "lastname": "DINH",
                "cardissueplace": "VN"
            },
            {
                "firstname": "TUAN VU",
                "ticketno": "",
                "national": "VN",
                "cardexpired": "",
                "sex": "M",
                "cardtype": "O",
                "birthday": "1972-09-09",
                "cardnum": "",
                "lastname": "PHAN",
                "cardissueplace": "VN"
            }
        ],
        "remark": "",
        "retdate": "",         # 小写 (实际 bookdata 格式)
        "priceinfo": "",
        "plmpnr": "",
        "createtime": "",
        "retflightno": "",     # 小写
        "method": "1Booking",
        "isspecial": False,
        "carrier": "VU",
        "fromdate": "2026-07-26",     # 小写
        "dptairport": "SGN",          # 小写
        "arrairport": "HAN",          # 小写
        "fromflightno": "VU750",      # 小写
        "realtimeprice": 0,
        "hasdevied": False,
        "returnrettime": "",
        "orderno": "TEST_VU_001",
        "inorderno": "",
        "brushstatus": 2,
        "returnfromtime": ""
    })

    vu = VUB2BBooker()

    # 模拟 booker.json 中的 resdict 字段
    result = {
        "bookingAccount": "ltzd01",
        "bookingAccountPwd": "Tripto147258@@",
        "minProfit": -100.0,       # 允许涨价容忍度 (CNY)
    }

    # 调用 book() 时传入实时汇率表, dry_run=True 跳过支付 (安全测试)
    vu.book(obj, result, exchangerates=exchange_rates, dry_run=True)

    print("\n" + "=" * 60)
    print("订票结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("=" * 60)
