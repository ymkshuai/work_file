# -*- coding:utf-8 -*-
# !/usr/bin/python
import random
import re
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import datetime
import json
import logging
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
from pyquery import PyQuery as pq
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from setting.defaultsetting import globalSetting, checkBalance, updateBalance
# from utils.Order import Order, Contact, Passenger, Luggage, LuggageItems
from entity.order import Order

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# from selenium import webdriver
import math
import string
from lxml import etree

# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service

TITLES = {'M': 'MR', 'F': 'MS'}
GENDER = {'M': 1, 'F': 2}
PAYTYPE_ALIPAY = 0
PAYTYPE_TENPAY = 1
DEFAULT_CURRENCY_GROUP = 'DEFAULT'
DEFAULT_CURRENCY_CODE = 'CNY'
CURRENCY = {
    'VND': ['HPH', 'VCL', 'VCA', 'VII', 'THD', 'BMV', 'DLI', 'DAD', 'VDH', 'HAN', 'SGN', 'HUI', 'CXR', 'PQC', 'PXU',
            'UIH'],  # 越南：越南盾
    'USD': [],  # 美国：美元
    'THB': ['BKK'],  # 泰国：泰铢
    'SGD': ['SIN'],  # 新加坡：新加坡元
    'KRW': ['ICN'],  # 朝鲜：圆
    'TWD': ['TPE'],  # 中国台湾：台币
    'KHR': [],  # 柬埔寨：瑞尔
    'HKD': [],  # 中国香港：港元
    'MYR': [],  # 马来西亚：马元
    'CNY': ['HGH'],  # 中国：人民币
    'MMK': ['RGN'],  # 缅甸：缅元
}
COUNTRYDICT = {"AD": "AND", "AE": "ARE", "AF": "AFG", "AG": "ATG", "AI": "AIA", "AL": "ALB", "AM": "ARM", "AO": "AGO",
               "AQ": "ATA", "AR": "ARG", "AS": "ASM", "AT": "AUT", "AU": "AUS", "AW": "ABW", "AX": "ALA", "AZ": "AZE",
               "BA": "BIH", "BB": "BRB", "BD": "BGD", "BE": "BEL", "BF": "BFA", "BG": "BGR", "BH": "BHR", "BI": "BDI",
               "BJ": "BEN", "BL": "BLM", "BM": "BMU", "BN": "BRN", "BO": "BOL", "BQ": "BES", "BR": "BRA", "BS": "BHS",
               "BT": "BTN", "BV": "BVT", "BW": "BWA", "BY": "BLR", "BZ": "BLZ", "CA": "CAN", "CC": "CCK", "CF": "CAF",
               "CH": "CHE", "CL": "CHL", "CM": "CMR", "CO": "COL", "CR": "CRI", "CU": "CUB", "CV": "CPV", "CX": "CXR",
               "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DJ": "DJI", "DK": "DNK", "DM": "DMA", "DO": "DOM", "DZ": "DZA",
               "EC": "ECU", "EE": "EST", "EG": "EGY", "EH": "ESH", "ER": "ERI", "ES": "ESP", "FI": "FIN", "FJ": "FJI",
               "FK": "FLK", "FM": "FSM", "FO": "FRO", "FR": "FRA", "GA": "GAB", "GD": "GRD", "GE": "GEO", "GF": "GUF",
               "GH": "GHA", "GI": "GIB", "GL": "GRL", "GN": "GIN", "GP": "GLP", "GQ": "GNQ", "GR": "GRC", "GS": "SGS",
               "GT": "GTM", "GU": "GUM", "GW": "GNB", "GY": "GUY", "HK": "HKG", "HM": "HMD", "HN": "HND", "HR": "HRV",
               "HT": "HTI", "HU": "HUN", "ID": "IDN", "IE": "IRL", "IL": "ISR", "IM": "IMN", "IN": "IND", "IO": "IOT",
               "IQ": "IRQ", "IR": "IRN", "IS": "ISL", "IT": "ITA", "JE": "JEY", "JM": "JAM", "JO": "JOR", "JP": "JPN",
               "KH": "KHM", "KI": "KIR", "KM": "COM", "KW": "KWT", "KY": "CYM", "LB": "LBN", "LI": "LIE", "LK": "LKA",
               "LR": "LBR", "LS": "LSO", "LT": "LTU", "LU": "LUX", "LV": "LVA", "LY": "LBY", "MA": "MAR", "MC": "MCO",
               "MD": "MDA", "ME": "MNE", "MF": "MAF", "MG": "MDG", "MH": "MHL", "MK": "MKD", "ML": "MLI", "MM": "MMR",
               "MO": "MAC", "MQ": "MTQ", "MR": "MRT", "MS": "MSR", "MT": "MLT", "MV": "MDV", "MW": "MWI", "MX": "MEX",
               "MY": "MYS", "NA": "NAM", "NE": "NER", "NF": "NFK", "NG": "NGA", "NI": "NIC", "NL": "NLD", "NO": "NOR",
               "NP": "NPL", "NR": "NRU", "OM": "OMN", "PA": "PAN", "PE": "PER", "PF": "PYF", "PG": "PNG", "PH": "PHL",
               "PK": "PAK", "PL": "POL", "PN": "PCN", "PR": "PRI", "PS": "PSE", "PW": "PLW", "PY": "PRY", "QA": "QAT",
               "RE": "REU", "RO": "ROU", "RS": "SRB", "RU": "RUS", "RW": "RWA", "SB": "SLB", "SC": "SYC", "SD": "SDN",
               "SE": "SWE", "SG": "SGP", "SI": "SVN", "SJ": "SJM", "SK": "SVK", "SL": "SLE", "SM": "SMR", "SN": "SEN",
               "SO": "SOM", "SR": "SUR", "SS": "SSD", "ST": "STP", "SV": "SLV", "SY": "SYR", "SZ": "SWZ", "TC": "TCA",
               "TD": "TCD", "TG": "TGO", "TH": "THA", "TK": "TKL", "TL": "TLS", "TN": "TUN", "TO": "TON", "TR": "TUR",
               "TV": "TUV", "TZ": "TZA", "UA": "UKR", "UG": "UGA", "US": "USA", "UY": "URY", "VA": "VAT", "VE": "VEN",
               "VG": "VGB", "VI": "VIR", "VN": "VNM", "WF": "WLF", "WS": "WSM", "YE": "YEM", "YT": "MYT", "ZA": "ZAF",
               "ZM": "ZMB", "ZW": "ZWE", "CN": "CHN", "CG": "COG", "CD": "COD", "MZ": "MOZ", "GG": "GGY", "GM": "GMB",
               "MP": "MNP", "ET": "ETH", "NC": "NCL", "VU": "VUT", "TF": "ATF", "NU": "NIU", "UM": "UMI", "CK": "COK",
               "GB": "GBR", "TT": "TTO", "VC": "VCT", "TW": "TWN", "NZ": "NZL", "SA": "SAU", "LA": "LAO", "KP": "PRK",
               "KR": "KOR", "PT": "PRT", "KG": "KGZ", "KZ": "KAZ", "TJ": "TJK", "TM": "TKM", "UZ": "UZB", "KN": "KNA",
               "PM": "SPM", "SH": "SHN", "LC": "LCA", "MU": "MUS", "CI": "CIV", "KE": "KEN", "MN": "MNG"}
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
    "CL": {"code": "DHL", "name": "Chile"},  # 注意：你接口里 Chile 用的是 DHL（非标准）
    "CO": {"code": "COL", "name": "Colombia"},
    "PE": {"code": "PER", "name": "Peru"},
    "VE": {"code": "VEN", "name": "Venezuela"},
    "ZA": {"code": "ZAF", "name": "South Africa"},
    "EG": {"code": "EGY", "name": "Egypt"},
    "AE": {"code": "ARE", "name": "United Arab Emirates"},
    "SA": {"code": "SAU", "name": "Saudi Arabia"},
    "QA": {"code": "QAT", "name": "Qatar"},
    "TR": {"code": "TUR", "name": "Turkey"},
    "IL": {"code": "ISR", "name": "Israel"},
    "IR": {"code": "IRN", "name": "Iran"},
    "IQ": {"code": "IRQ", "name": "Iraq"},
    "KH": {"code": "KHM", "name": "Cambodia"},
    "LK": {"code": "LKA", "name": "Sri Lanka"},
    "MM": {"code": "MMR","name": "Myanmar"}
}
PUBLIC_KEY_PEM = """-----BEGIN RSA PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzzlX85HWtWs9duKm97Dl
8gf+ojFq50KobiWL6GNCbw8lcoINCA4pLu2mInC6jaaNK0NY6PvlwfkJIlcTcBf2
sczV+2Ju3nad4G7Po9xYkyFAcCsMygGmGvQag9kcmSOEQtMKwNGdqdOe6AR21CMI
n0TgRIBejpkw3anfG79GCYkj4vRJPKMNRLoBbJibITrXR2mbzPpNoP9FezoImY9z
f4WFhr/6+rv1yjGSbefhXPeUFRauBcYFJl/CeJuDTnW7/QH43tdPQEEzPOiATsTi
jrBS2eVRlrNkZCieZeDqwArcBug/JjWnImSmuYQDmCB7J+jrCSASjPPrZM6M8fuc
NQIDAQAB
-----END RSA PUBLIC KEY-----"""


def get_ancillary_options(result):
    luggage_key_dict = {
        'from': {},
        'ret': {}
    }
    try:
        for ancillary_info in result['data']:
            if 'Baggage' in ancillary_info['code']:
                ancillariesDeparture = ancillary_info['ancillariesDeparture']
                if ancillariesDeparture:
                    for bag_item in ancillariesDeparture:
                        if "Baggage" in bag_item['description']:
                            weight = int(re.findall('(\d{0,3})kgs', bag_item['description'])[0])
                            luggage_key_dict['from'][weight] = bag_item
                ancillariesReturn = ancillary_info['ancillariesReturn']
                if ancillariesReturn:
                    for bag_item in ancillariesDeparture:
                        if "Baggage" in bag_item['description']:
                            weight = int(re.findall('(\d{0,3})kgs', bag_item['description'])[0])
                            luggage_key_dict['ret'][weight] = bag_item
    except:
        pass

    return luggage_key_dict

def config_log():
    level = logging.DEBUG
    fmt = '%(asctime)s - %(levelname)s - %(message)s - %(thread)d'
    logging.basicConfig(filename='VJBOOK.log', level=level, format=fmt)
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(fmt))
    logging.getLogger('').addHandler(console)


class VJB2BBooker():

    def __init__(self):
        self.setting = globalSetting.instance()
        self.session = requests.session()
        self.timeout = 30
        self.method = 'VJB2B'
        self.redis10 = self.setting.redis10
        self.priceIndex = 0
        self.currency = "USD"
        self.iplist = ["http://Jk0915mkdawe:Jk0915mkdawe@218.78.81.205:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@218.78.58.191:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.91.216.244:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@218.78.97.32:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@218.78.87.58:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@218.78.117.80:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.89.120.95:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.89.205.30:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.91.238.24:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@61.171.33.251:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@61.171.8.236:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@61.171.61.82:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@61.171.30.73:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@218.78.113.17:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@61.171.62.183:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.91.124.231:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.89.153.98:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.91.113.152:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.91.118.125:65000",
                       "http://Jk0915mkdawe:Jk0915mkdawe@101.89.167.38:65000"]
        self.passEmailList = ["675109006@qq.com", "10571985@qq.com", "8063162@qq.com", "362604071@qq.com",
                              "858687397@qq.com", "675109106@qq.com", "10571285@qq.com", "8063132@qq.com",
                              "362644071@qq.com"]
        self.session.headers.update({
            "Host": "agents.vietjetair.com",
            "Connection": "keep-alive",
            "sec-ch-ua": 'Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "sec-ch-ua-platform": "Windows",
            "Accept": "*/*",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://agents.vietjetair.com/ViewFlights.aspx?lang=en&st=sl&sesid=",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://agents.vietjetair.com",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        self.availableCredits = 0
        self.from_is_bj = False
        self.from_free_bj_count = 0
        self.logurl = "https://oa.tripto.cn/flightoa/order/addorderlog?orderid={orderno}&operator=robot&optname={mes}&optdesc={mesdesc}"
        self.rz_url = "https://oa.tripto.cn/flightoa/order/addorderlog?orderid={orderno}&operator=robot&optname={mes}&optdesc={mesdesc}&keyWordColor={keyWordColor}"

    def setproxy(self):
        try:
            content = requests.post("http://127.0.0.1:9090/agent/getip", timeout=3).content
            if content:
                root = json.loads(content)
                if root['ret'] == 0:
                    self.proxyurl = root['data']
                    logging.info('Use letsfly proxy: %s for method %s' % (self.proxyurl, self.method))
                    proxy_handler = {
                        'http': self.proxyurl,
                        'https': self.proxyurl,
                    }
                    self.session.proxies = proxy_handler
                else:
                    logging.info(root['ret'])
            else:
                logging.info('http request error!!!')
        except:
            logging.exception('Get letsfly proxy failed')

    def setproxy3(self):
        ipstr = random.choice(self.iplist)
        self.session.proxies = {
            "http": ipstr,
            "https": ipstr
        }
        logging.info('Use letsfly proxy: %s for method %s' % (self.session.proxies["http"], self.method))

    def setproxy2(self):
        proxy_handler = {
            'http': "http://47.106.143.189:36302",
            'https': "http://47.106.143.189:36302"
        }
        self.session.proxies = proxy_handler

    def convert2RMB(self, currencycode, value, method=None):
        if currencycode == DEFAULT_CURRENCY_CODE:
            return int(math.ceil(float(value)))

        currencyMap = globalSetting.instance().currencyMap
        if method and (method in currencyMap) and (currencycode in currencyMap[method]):
            exchangerate = currencyMap[method][currencycode]
        else:
            if DEFAULT_CURRENCY_GROUP in currencyMap:
                exchangerate = currencyMap[DEFAULT_CURRENCY_GROUP][currencycode]
            else:
                exchangerate = currencyMap[currencycode]
        return int(math.ceil(float(value) * exchangerate)), exchangerate

    def ageType(self, birthday, flightdate):
        birthday = datetime.datetime.strptime(birthday, '%Y-%m-%d')
        flightdate = datetime.datetime.strptime(flightdate, '%Y-%m-%d')
        delta = flightdate - birthday
        if delta < datetime.timedelta(days=2 * 365):
            return 'INFANT'
        elif delta < datetime.timedelta(days=12 * 365):
            return 'CHILD'
        else:
            return 'ADULT'

    # def getCookies(self, orderno, account, password):
    #     driver = None
    #     cookieStr = self.redis10.get("VJB2bCookieStr")
    #     if not cookieStr:
    #         try:
    #             cookieStr = ""
    #             options = webdriver.ChromeOptions()
    #             # 禁用图片
    #             # options.add_argument('--headless')  # 无头
    #             options.add_argument('--disable-gpu')  # 禁用GPU加速，加快图片显示速度
    #             options.add_argument('--blink-settings=imagesEnabled=false')  # 禁用图片
    #             # 禁用 CSS 和 JavaScript
    #             prefs = {
    #                 "profile.managed_default_content_settings.images": 2,  # 禁用图片
    #                 "profile.managed_default_content_settings.stylesheets": 2,  # 禁用 CSS
    #                 # "profile.managed_default_content_settings.javascript": 2,  # 禁用 JavaScript
    #                 "profile.managed_default_content_settings.plugins": 2,  # 禁用插件
    #             }
    #             options.add_experimental_option("prefs", prefs)
    #             # C:\chromedriver_129.exe
    #             service = Service(executable_path='C:/chromedriver_129.exe')  # 使用正斜杠
    #             driver = webdriver.Chrome( service=service,options=options)
    #             driver.get("https://www.vietjetair.com/en")
    #             driver.execute_script("window.location = 'https://agents.vietjetair.com/sitelogin.aspx?lang=en'")
    #             time.sleep(3)
    #             acc = driver.find_element(By.ID, 'txtAgentID')
    #             acc.clear()
    #             acc.send_keys(account)
    #             # txtAgentPswd
    #             pas =  driver.find_element(By.ID, 'txtAgentPswd')
    #             pas.clear()
    #             pas.send_keys(password)
    #             driver.find_element(By.CSS_SELECTOR, "a[class=button]").click()
    #             time.sleep(3)
    #             cookies = driver.get_cookies()
    #             for cookie in cookies:
    #                 cookieStr += cookie['name'] + '=' + cookie['value'] + ';'
    #             try:
    #                 loginB = pq(driver.page_source)
    #                 balanceinfo = loginB("span[id='AgencyCreditAvailable']").text()
    #                 balance, currency = float(balanceinfo.strip()[:-3]), balanceinfo.strip()[-3:]
    #                 self.availableCredits = balance
    #                 balanceStr = "{} {}".format(balance, currency)
    #                 self.writelog(self.logurl.format(orderno=orderno, mes=u"余额信息", mesdesc=balanceStr))
    #                 checkBalance(balance, currency, 6600000, "VJ", account)
    #             except:
    #                 logging.exception('get balance:')
    #             # self.redis10.setex("VJB2bCookieStr", cookieStr, 30 * 60)
    #         except:
    #             logging.exception("error:")
    #         finally:
    #             if driver:
    #                 driver.close()
    #                 driver.quit()
    #     return cookieStr

    def writelog(self, mesurl):
        try:
            requests.get(mesurl, verify=False, timeout=30)
            # logging.info(mesurl)
        except:
            logging.exception('log error:')

    def get_proxy(self):
        username = 'astoip3305'
        password = 'ZUOPGEE-CNJYIFI-TDJECSC-AJGS2TC-STK0IZ0-Y57LNII-UY3FEGD'
        ip = "209.205.219.18"
        port = random.choice(range(9001, 9051))
        super_proxy_url = ('http://%s:%s@%s:%d' %
                           (username, password, ip, port))
        proxy_handler = {
            'http': super_proxy_url,
            'https': super_proxy_url,
        }
        return proxy_handler

    def set_proxy(self):
        username = 'astoip3305'
        password = 'ZUOPGEE-CNJYIFI-TDJECSC-AJGS2TC-STK0IZ0-Y57LNII-UY3FEGD'
        ip = "209.205.219.18"
        port = random.choice(range(9001, 9021))
        super_proxy_url = ('http://%s:%s@%s:%d' %
                           (username, password, ip, port))
        proxy_handler = {
            'http': super_proxy_url,
            'https': super_proxy_url,
        }
        self.session.proxies = proxy_handler

    def loginIn(self, username, passwd):
        res = {}
        self.session.headers.update({
            "Host": "agentapi.vietjetair.com",
            "sec-ch-ua-platform": "\"Windows\"",
            "languagecode": "zh-CN",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "platform": "3",
            "origin": "https://agents2.vietjetair.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://agents2.vietjetair.com/",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i"
        })
        try:
            url1 = "https://agentapi.vietjetair.com/api/v14/Auth/login"
            key = RSA.import_key(PUBLIC_KEY_PEM)
            cipher = PKCS1_OAEP.new(key)
            encrypted = cipher.encrypt(passwd.encode())
            encrypted_b64 = base64.b64encode(encrypted).decode()
            data1 = {
                "lang": "zh-CN",
                "username": username,
                "password": encrypted_b64
            }
            resp1 = self.session.post(url1, json=data1)
            if resp1.status_code == 200:
                res = resp1.json()
        except:
            logging.exception("errpr")
        finally:
            return res

    def pay_run_log(self, orderno):
        rz_url = "https://oa.tripto.cn/flightoa/order/addorderlog?orderid={orderno}&operator=robot&optname={mes}&optdesc={mesdesc}&keyWordColor={keyWordColor}"
        self.writelog(
            rz_url.format(orderno=orderno, mes="正在进行支付", mesdesc="进入支付环节, 出现任何问题请人工核对", keyWordColor="red"))

    @staticmethod
    def setproxt4(city=None):
        session_id = ''.join(random.sample(string.ascii_lowercase + string.digits, 9))
        if city is None:
            city = "us"
        proxy_handler = {
            'http': 'http://wuxiao123-zone-custom-region-{}-session-{}-sessTime-1:wuxiao123@fe8d7973174b824c.fjt.as.ipidea.online:2333'.format(
                city, session_id),
            'https': 'http://wuxiao123-zone-custom-region-{}-session-{}-sessTime-1:wuxiao123@fe8d7973174b824c.fjt.as.ipidea.online:2333'.format(
                city, session_id),
        }
        return proxy_handler

    @staticmethod
    def seat_proxy(city=None, tt_time=None):
        # http://wuxiao123-zone-custom-region-hk-session-{9位随机数}-sessTime-{时效时间(分钟)}:wuxiao123@fe8d7973174b824c.fjt.as.ipidea.online:2336
        session_id = ''.join(random.sample(string.ascii_lowercase + string.digits, 9))
        if city is None:
            city = "us"
        if tt_time is None:
            tt_time = 3
        proxy = f"http://SEAT20251201-zone-custom-region-{city}-session-{session_id}-sessTime-{tt_time}:SEAT20251201@pr-as.ipidea.net:2333"
        proxy_handler = {
            'http': proxy,
            'https': proxy,
        }
        return proxy_handler

    @staticmethod
    def new_seat(city=None):
        # http://wuxiao123-zone-custom-region-hk-session-{9位随机数}-sessTime-{时效时间(分钟)}:wuxiao123@fe8d7973174b824c.fjt.as.ipidea.online:2336
        session_id = ''.join(random.sample(string.ascii_lowercase + string.digits, 9))
        if city is None:
            city = "us"
        tt_time = 3
        proxy = f"http://client-wuxiaocq_area-{city}_session-{session_id}_life-{tt_time}:Flight898@proxy.iproyal.net:9000"
        proxy_handler = {
            'http': proxy,
            'https': proxy,
        }
        return proxy_handler

    def getflightInfo(self, trip, flightno,fromdate):
        flight_data={}
        for flight in trip:
            if fromdate==flight['DepartureDate']:
                flino=flight['segmentOptions'][0]['flight']['Number']
                if flightno==flino:
                    flight_data=flight
                    break
        return flight_data

    def select_seat_data(self,seat_data,item_data):
        res=None
        number = item_data['selectedSeatNo']
        flightNo = item_data['flightNo']
        try:
            seat_list=seat_data[flightNo]['seatGroups'][0]['seatOptions']
            for seat_item in seat_list:
                if f"{seat_item['rowIdentifier']}{seat_item['seatIdentifier']}" == number and seat_item['available'] is True:
                    res=seat_item
                    break
        except:
            pass
        finally:
            return res


    def book(self, order, resdict={}):
        passengers_adt = []
        passengers_chd = []
        passengers_infant = []
        dptcity = order.dptAirport.split('|')[0] if '|' in order.dptAirport else order.dptAirport
        arrcity = order.arrAirport.split('|')[-1] if '|' in order.arrAirport else order.arrAirport
        fromdate = order.fromDate.split('|')[0]
        retdate = order.retDate.split("|")[0]
        # resdict["bookingAccount"] = "CH330207A1QX14"
        # resdict["bookingAccountPwd"] = "Xingzou@888666"
        account, password = resdict["bookingAccount"], resdict["bookingAccountPwd"]
        self.writelog(self.logurl.format(orderno=order.orderno, mes="占座中", mesdesc=f"出票账号:{account},出票密码:{password}"))
        logging.info(f"出票账号:{account},出票密码:{password}")

        for ind, passenger in enumerate(order.passengers):
            ageType = self.ageType(passenger.birthday, fromdate)
            if ageType == 'INFANT':
                passengers_infant.append(passenger)
            elif ageType == 'CHILD':
                passengers_chd.append(passenger)
            elif ageType == 'ADULT':
                passengers_adt.append(passenger)
        # self.set_proxy()
        PromotionCode = ""
        self.writelog(self.logurl.format(orderno=order.orderno, mes="促销码", mesdesc='促销码为:{}'.format(PromotionCode)))
        self.session.proxies = self.new_seat(city='hk')
        # self.session.proxies = {
        #     'http': 'http://127.0.0.1:7890',
        #     'https': 'http://127.0.0.1:7890',
        # }
        resdict["passenger"] = "|".join(["{}/{}".format(p.lastname, p.firstname) for p in order.passengers])
        sleep_t=30
        self.writelog(self.logurl.format(orderno=order.orderno, mes="出票中", mesdesc=f'睡眠：{sleep_t}在开始占座'))
        time.sleep(sleep_t)
        # if "searchCurrency" in order.policyinfo and len(order.policyinfo["searchCurrency"]) == 3:
        #     self.currency = order.policyinfo["searchCurrency"]
        # 强制美元
        self.currency = "USD"
        login_flag = self.loginIn(account, password)
        if not login_flag:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "登录失败"
            self.writelog(self.logurl.format(orderno=order.orderno, mes=u"占座失败", mesdesc=resdict["msg"]))
            return

        self.session.headers.update({
            "Host": "agentapi.vietjetair.com",
            "sec-ch-ua-platform": "\"Windows\"",
            "authorization": f"Bearer {login_flag['data']['token']}",
            "languagecode": "zh-CN",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "platform": "3",
            "origin": "https://agents2.vietjetair.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://agents2.vietjetair.com/",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=1, i"
        })
        url1 = "https://agentapi.vietjetair.com/api/v14/Booking/findtraveloptions"
        params1 = {
            "cityPair": f"{dptcity}-{arrcity}",
            "departurePlace": dptcity,
            "departurePlaceName": "Ha Noi",
            "returnPlace": arrcity,
            "returnPlaceName": "Phu Quoc",
            "departure": fromdate,
            "currency": self.currency,
            "company": "DdZQ590rFTUr9jbtƒZYz33Ey5ƒaeSbUDgC¥BxF2orG8=",
            "adultCount": f"{len(passengers_adt)}",
            "childCount": f"{len(passengers_chd)}",
            "infantCount": f"{len(passengers_infant)}",
            "promoCode": "",
            "greaterNumberOfStops": "0"
        }
        for _ in range(3):
            try:
                resp1 = self.session.get(url1, params=params1)
                if resp1.status_code==200:
                    break
                time.sleep(2)
            except:
                logging.exception("error")
                time.sleep(2)
        else:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "重试3次失败, 请稍后再重试..."
            self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败",mesdesc=resdict["msg"]))
            return

        resdict["msg"] = u"搜索航班成功 ......"
        self.writelog(self.logurl.format(orderno=order.orderno, mes=u"占座中",mesdesc=resdict["msg"]))
        # 拿到产品名字
        obbrandname = order.policyinfo.get("obbrandname", "Eco")
        luggageServices = {}
        for luggageObj in order.luggages:
            for item in luggageObj.luggageItems:
                if not luggageServices.get(luggageObj.passengerName):
                    luggageServices[luggageObj.passengerName] = {}
                luggageServices[luggageObj.passengerName][item.dep] = int(item.weightPerPC)

        if luggageServices:
            self.writelog(
                self.rz_url.format(orderno=order.orderno, mes="行李信息", keyWordColor="red", mesdesc=luggageServices))
            # 先看看要不要比价  先不比价回程
            from_luggage_type = []
            for k, v in luggageServices.items():
                count = v.get(dptcity)
                if count:
                    from_luggage_type.append(count)
            from_bag_bj = False
            if len(passengers_adt) + len(passengers_chd) == len(from_luggage_type) and len(set(from_luggage_type)) == 1:
                from_bag_bj = True
            else:
                self.writelog(
                    self.rz_url.format(orderno=order.orderno, mes="行李信息", keyWordColor="red",
                                       mesdesc=f"行李规格为:{from_luggage_type},没有达到比价要求,不比价"))

            if from_bag_bj is True and obbrandname == "Eco":
                try:
                    self.writelog(
                        self.rz_url.format(orderno=order.orderno, mes="行李信息", keyWordColor="red", mesdesc="需要进行行李比价"))
                    url = f"http://47.238.120.15:10001/vj_query?dep={dptcity}&arr={arrcity}&fromdate={fromdate}&cbin={order.fromFlightNo}"
                    bag_data_res = requests.get(url).json()
                    logging.info(f"bag_data_res:{bag_data_res}")
                    bj_count = from_luggage_type[0]
                    # 裸票价
                    Eco1 = bag_data_res['Eco1']['dj_price']
                    Deluxe1 = bag_data_res['Deluxe1']['dj_price']  # 20
                    Business = bag_data_res['Business']['dj_price']  # 30
                    price_jg = Eco1 + bag_data_res['bags'][f'{bj_count}']['totalAmount']
                    if bj_count == 20:
                        if Deluxe1 < price_jg:
                            obbrandname = "Deluxe"
                        else:
                            obbrandname = "Eco"
                        self.writelog(self.rz_url.format(orderno=order.orderno, mes="行李比价情况", keyWordColor="red",
                                                         mesdesc=f"Deluxe套餐价格为:{Deluxe1},后买价格为:{price_jg},最终走:{obbrandname}票价"))
                    elif bj_count == 30:
                        if Business < price_jg:
                            obbrandname = "Business"
                        else:
                            obbrandname = "Eco"
                        self.writelog(self.rz_url.format(orderno=order.orderno, mes="行李比价情况", keyWordColor="red",
                                                         mesdesc=f"Business套餐价格为:{Business},后买价格为:{price_jg},最终走:{obbrandname}票价"))
                    else:
                        self.writelog(self.rz_url.format(orderno=order.orderno, mes="行李信息", keyWordColor="red",
                                                         mesdesc=f"行李比价失败,目前只能比价20或者30公斤行李"))
                except:
                    self.writelog(self.rz_url.format(orderno=order.orderno, mes="行李比价情况", keyWordColor="red",
                                                     mesdesc=f"行李比价过程中发生错误,走原套餐:{obbrandname}"))
                    logging.exception("error")

            # 查看免费行李额度
            if obbrandname == "Eco":
                self.from_free_bj_count = 0
            elif obbrandname == "Deluxe":
                self.from_free_bj_count = 20
            elif obbrandname == "Business":
                self.from_free_bj_count = 30

            for k, v in luggageServices.items():
                if v.get(dptcity):
                    v[dptcity] -= self.from_free_bj_count

            for k, v in luggageServices.items():
                if v.get(dptcity):
                    if v.get(dptcity) > 0:
                        self.from_is_bj = True
                        break
            if self.from_is_bj is True:
                self.writelog(self.rz_url.format(orderno=order.orderno, mes="占座中", keyWordColor="red",
                                                 mesdesc='需要进行辅营购买'))
            else:
                self.writelog(self.rz_url.format(orderno=order.orderno, mes="占座中", keyWordColor="red",
                                                 mesdesc=f'不需要进行辅营购买,套餐中包含{self.from_free_bj_count}的行李'))
        # obbrandname="Deluxe"
        self.writelog(self.logurl.format(orderno=order.orderno, mes=u"占座中", mesdesc=f"去程的产品名为:{obbrandname}"))
        # 帅选航班
        routeList=resp1.json()['data']['list_Travel_Options_Departure']
        fromFlightInfo = self.getflightInfo(routeList, order.fromFlightNo,fromdate)
        if not fromFlightInfo:
            logging.info('去程无航班 ......')
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "去程无航班"
            self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败",
                                             mesdesc=resdict["msg"]))
            return
        # ETDLocal
        ret_time = fromFlightInfo['segmentOptions'][0]['flight']['ETDLocal'].replace("T", "") + ":00"  # 去程起飞时间 2025-01-30T06:10:00
        oa_ret_time = order.flightnotime.get(order.retFlightNo).replace(" ","")
        if ret_time != oa_ret_time:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = f"回程发生航班,请核实,官网起飞时间:{ret_time},oa起飞时间:{oa_ret_time}"
            self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败", mesdesc=resdict["msg"]))
            return

        retFlightInfo = {}
        if retdate:
            retFlightInfo = self.getflightInfo(routeList, order.retFlightNo,retdate)
            if not retFlightInfo:
                logging.info('回程无航班 ......')
                resdict["payStatus"] = "12"
                resdict["orderStatus"] = "0"
                resdict["msg"] = "回程无航班"
                self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败",
                                                 mesdesc=resdict["msg"]))
                return
            ret_time = retFlightInfo['segmentOptions'][0]['flight']['ETDLocal'].replace("T", "") + ":00"  # 去程起飞时间 2025-01-30T06:10:00
            oa_ret_time = order.flightnotime.get(order.retFlightNo).replace(" ", "")
            if ret_time != oa_ret_time:
                resdict["payStatus"] = "12"
                resdict["orderStatus"] = "0"
                resdict["msg"] = f"回程发生航班,请核实,官网起飞时间:{ret_time},oa起飞时间:{oa_ret_time}"
                self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败", mesdesc=resdict["msg"]))
                return
        from_bookingKey=list(filter(lambda k: k['Description'] == obbrandname, fromFlightInfo['fareOption']))[0]['BookingKey']

        sell_url = "https://agentapi.vietjetair.com/api/v14/Booking/quotationwithoutpassenger"
        sell_data = {
            "journeys": [
                {
                    "index": 1,
                    "bookingKey": from_bookingKey
                }
            ],
            "numberOfAdults": len(passengers_adt),
            "numberOfChilds": len(passengers_chd),
            "numberOfInfants": len(passengers_infant)
        }
        if retdate:
            ret_bookingKey = list(filter(lambda k: k['Description'] == obbrandname, retFlightInfo['fareOption']))[0]['BookingKey']
            sell_data['journeys'].append({
                "index": 2,
                "bookingKey": ret_bookingKey
            })
        sell_resp = self.session.post(sell_url, json=sell_data)
        if sell_resp.status_code!=200:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "选择航班失败。。。"
            self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败",mesdesc=resdict["msg"]))
            return
        sell_resp_data=sell_resp.json()
        totalamountdeparture=sell_resp_data['data']['totalamountdeparture']
        self.writelog(self.logurl.format(orderno=order.orderno, mes="占座中", mesdesc=f"当前占座金额为：{totalamountdeparture}\t{self.currency}"))
        resdict["msg"] = "提交航班成功 ......"
        self.writelog(self.logurl.format(orderno=order.orderno, mes="占座中",mesdesc=resdict["msg"]))

        add_parser_url = "https://agentapi.vietjetair.com/api/v14/Booking/insurances"
        add_parser_data = {
            "languagecode": "zh-CN",
            "bookingInformation": {
                "contactInformation": {
                    "isoCode": "VN",
                    "phoneNumber": "8638473699",
                    "name": "GUANGZHOU HONGDALIAN AVIATION SERVICE CO., LTD",
                    "email": "77148009@qq.com"
                }
            },
            "departureAirportCode": dptcity,
            "passengers": [],
            "journeys": [
                {
                    "index": 1,
                    "passengerJourneyDetails": [
                    ]
                }
            ],
            "seatSelections": [],
            "ancillaryPurchases": [],
            "paymentTransactions": []
        }
        if retdate:
            add_parser_data['journeys'].append({
                "index": 2,
                "passengerJourneyDetails": [
                ]
            })
        seatSelections=[]
        ancillaryPurchases=[]
        seat_map_dic = {}
        if order.seats:
            for item in order.seats:
                name = item.name
                if seat_map_dic.get(name):
                    seat_map_dic[name].append({
                        "flightNo": item.flightNo,
                        "selectedSeatNo": item.selectedSeatNo
                    })
                else:
                    seat_map_dic[name] = []
                    seat_map_dic[name].append({
                        "flightNo": item.flightNo,
                        "selectedSeatNo": item.selectedSeatNo
                    })
            self.writelog(
                self.rz_url.format(orderno=order.orderno, mes="选座信息", mesdesc=seat_map_dic, keyWordColor="red"))

        # 拿选座数据
        map_seats_resp_data = {}
        seat_url = "https://agentapi.vietjetair.com/api/v14/Booking/seatSelectionOptions"
        if seat_map_dic:
            from_seat_params = {
                "bookingKey": from_bookingKey
            }
            from_seat_resp=self.session.get(seat_url, params=from_seat_params)
            from_seat_data=from_seat_resp.json()
            for item in from_seat_data['data']['departureTrips']:
                map_seats_resp_data[item['flightSegment']['Number']]=item

            if retdate:
                ret_seat_params = {
                    "bookingKey": ret_bookingKey
                }
                ret_seat_resp = self.session.get(seat_url, params=ret_seat_params)
                ret_seat_data = ret_seat_resp.json()
                for item in ret_seat_data['data']['departureTrips']:
                    map_seats_resp_data[item['flightSegment']['Number']] = item
        # 拿行李数据
        bag_url = "https://agentapi.vietjetair.com/api/v14/Booking/ancillaryOptions"
        bag_params = {
            "bookingKey": from_bookingKey,
            "languageCode": "zh-CN"
        }
        bag_resp = self.session.get(bag_url, params=bag_params)
        bag_resp_data=bag_resp.json()
        bag_map_data=get_ancillary_options(bag_resp_data)
        passengers = []
        namelist = []
        passengers.extend(passengers_adt)
        passengers.extend(passengers_chd)
        parser_index=1
        parser_index_map_name={}
        for parser in passengers_adt:
            pasname = "{}/{}".format(parser.lastname, parser.firstname)
            parser_data={
                "index": parser_index,
                "sendmail": True,
                "passengerSuffix": f" {parser_index}",
                "fareApplicability": {
                    "child": False,
                    "adult": True
                },
                "reservationProfile": {
                    "lastName": parser.lastname,
                    "firstName": parser.firstname,
                    "title": "Mr" if parser.sex == 'M' else "Mrs",
                    "gender": "Male" if parser.sex == 'M' else "Female",
                    "address": {
                        "address1": "",
                        "location": {
                            "country": {
                                "code": COUNTRY_2_TO_3[parser.national]['code'],
                                "name": COUNTRY_2_TO_3[parser.national]['name']
                            }
                        }
                    },
                    "birthDate": parser.birthday,
                    "nationCountry": {
                        "code": COUNTRY_2_TO_3[parser.national]['code'],
                        "name": COUNTRY_2_TO_3[parser.national]['name']
                    },
                    "personalContactInformation": {
                        "number": order.contact.phonenum,
                        "mobileIsoCode": "CN",
                        "mobileNumber": order.contact.phonenum,
                        "extension": "86",
                        "isoCode": "MN",
                        "email": order.contact.email
                    },
                    "passport": {
                        "number": parser.cardnum
                    },
                    "loyaltyProgram": {}
                }
            }
            parser_index_map_name[parser_index]=f"{parser.lastname}/{parser.firstname}"
            add_parser_data['passengers'].append(parser_data)
            add_parser_data['journeys'][0]['passengerJourneyDetails'].append({
                "passenger": {
                    "index": parser_index
                },
                "bookingKey": from_bookingKey
            })
            # 添加行李====
            # {'WI/HLAING': {'DMK': 25}, 'MWE/HOM': {'DMK': 25}}
            parsenger_bag = luggageServices.get(pasname)
            if parsenger_bag and obbrandname == "Eco":
                from_bag = parsenger_bag.get(dptcity)
                if from_bag:
                    from_bj_data=bag_map_data['from'].get(int(from_bag))
                    if from_bj_data:
                        ancillaryPurchases.append({
                            "purchaseKey":from_bj_data['purchaseKey'],
                            "passenger":{"index":parser_index},
                            "journey":{"index":1}
                        })
                if retdate:
                    ret_bag = parsenger_bag.get(arrcity)
                    if ret_bag:
                        ret_bj_data = bag_map_data['ret'].get(int(ret_bag))
                        if ret_bj_data:
                            ancillaryPurchases.append({
                                "purchaseKey": ret_bj_data['purchaseKey'],
                                "passenger": {"index": parser_index},
                                "journey": {"index": 2}
                            })
            # =============
            # ==========添加选座
            if seat_map_dic.get(pasname):
                for temp_item in seat_map_dic[pasname]:
                    seat_res = self.select_seat_data(map_seats_resp_data, temp_item)
                    if seat_res:
                        seat_data={
                            "selectionKey": seat_res['selectionKey'],
                            "rowIdentifier": seat_res['rowIdentifier'],
                            "seatIdentifier": seat_res['seatIdentifier'],
                            "rowIndex": seat_res['rowIndex'],
                            "seatIdentifierParse": seat_res['seatIdentifierParse'],
                            "color": seat_res['color'],
                            "available": seat_res['available'],
                            "isWay": seat_res['isWay'],
                            "seatCharges": seat_res['seatCharges'],
                            "seatClass":None,
                            "displayAmount":seat_res['seatCharges']['totalAmount'],
                            "passengerKey":"",
                            "passenger":{"index":parser_index},
                            "journey":{"index":1},
                            "segment":{"index":1},
                        }
                        seatSelections.append(seat_data)
                    else:
                        resdict["payStatus"] = "12"
                        resdict["orderStatus"] = "0"
                        resdict["msg"] = f"乘客：{pasname}所选座位：{temp_item}失败。。。"
                        self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败", mesdesc=resdict["msg"]))
                        return
            # ===============
            if retdate:
                add_parser_data['journeys'][1]['passengerJourneyDetails'].append({
                    "passenger": {
                        "index": parser_index
                    },
                    "bookingKey": ret_bookingKey
                })
            parser_index+=1
        for parser in passengers_chd:
            pasname = "{}/{}".format(parser.lastname, parser.firstname)
            parser_data={
                "index": parser_index,
                "sendmail": True,
                "passengerSuffix": f" {parser_index}",
                "fareApplicability": {
                    "child": True,
                    "adult": False
                },
                "reservationProfile": {
                    "lastName": parser.lastname,
                    "firstName": parser.firstname,
                    "title": None,
                    "gender": "Male" if parser.sex == 'M' else "Female",
                    "address": {
                        "location": {

                        }
                    },
                    "birthDate": parser.birthday,
                    "personalContactInformation": {
                    },
                    "passport": {
                        "number": parser.cardnum
                    },
                    "loyaltyProgram": {}
                }
            }
            parser_index_map_name[parser_index]=f"{parser.lastname}/{parser.firstname}"
            add_parser_data['passengers'].append(parser_data)
            add_parser_data['journeys'][0]['passengerJourneyDetails'].append({
                "passenger": {
                    "index": parser_index
                },
                "bookingKey": from_bookingKey
            })
            # 添加行李====
            # {'WI/HLAING': {'DMK': 25}, 'MWE/HOM': {'DMK': 25}}
            parsenger_bag = luggageServices.get(pasname)
            if parsenger_bag and obbrandname == "Eco":
                from_bag = parsenger_bag.get(dptcity)
                if from_bag:
                    from_bj_data = bag_map_data['from'].get(int(from_bag))
                    if from_bj_data:
                        ancillaryPurchases.append({
                            "purchaseKey": from_bj_data['purchaseKey'],
                            "passenger": {"index": parser_index},
                            "journey": {"index": 1}
                        })
                if retdate:
                    ret_bag = parsenger_bag.get(arrcity)
                    if ret_bag:
                        ret_bj_data = bag_map_data['ret'].get(int(ret_bag))
                        if ret_bj_data:
                            ancillaryPurchases.append({
                                "purchaseKey": ret_bj_data['purchaseKey'],
                                "passenger": {"index": parser_index},
                                "journey": {"index": 2}
                            })
            # =============
            # ==========添加选座
            if seat_map_dic.get(pasname):
                for temp_item in seat_map_dic[pasname]:
                    seat_res = self.select_seat_data(map_seats_resp_data, temp_item)
                    if seat_res:
                        seat_data = {
                            "selectionKey": seat_res['selectionKey'],
                            "rowIdentifier": seat_res['rowIdentifier'],
                            "seatIdentifier": seat_res['seatIdentifier'],
                            "rowIndex": seat_res['rowIndex'],
                            "seatIdentifierParse": seat_res['seatIdentifierParse'],
                            "color": seat_res['color'],
                            "available": seat_res['available'],
                            "isWay": seat_res['isWay'],
                            "seatCharges": seat_res['seatCharges'],
                            "seatClass": None,
                            "displayAmount": seat_res['seatCharges']['totalAmount'],
                            "passengerKey": "",
                            "passenger": {"index": parser_index},
                            "journey": {"index": 1},
                            "segment": {"index": 1},
                        }
                        seatSelections.append(seat_data)
                    else:
                        resdict["payStatus"] = "12"
                        resdict["orderStatus"] = "0"
                        resdict["msg"] = f"乘客：{pasname}所选座位：{temp_item}失败。。。"
                        self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败", mesdesc=resdict["msg"]))
                        return
            # ===============
            if retdate:
                add_parser_data['journeys'][1]['passengerJourneyDetails'].append({
                    "passenger": {
                        "index": parser_index
                    },
                    "bookingKey": ret_bookingKey
                })
            parser_index+=1
        # 提交乘客数据
        send_parser_resp = self.session.post(add_parser_url, json=add_parser_data)
        if send_parser_resp.status_code!=200:
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "提交乘客信息数据失败。。。"
            self.writelog(self.logurl.format(orderno=order.orderno, mes="占座失败", mesdesc=resdict["msg"]))
            return
        resdict["msg"] = "乘客信息提交成功 ......"
        self.writelog(self.logurl.format(orderno=order.orderno, mes="占座中",mesdesc=resdict["msg"]))
        # 获取支付方式
        payment_method_url = "https://agentapi.vietjetair.com/api/v14/Booking/paymentMethods"
        payment_method_params = {
            "bookingkeydeparture": from_bookingKey
        }
        payment_method_resp = self.session.get(payment_method_url, params=payment_method_params)
        payment_method_resp_data=payment_method_resp.json()

        # 先占座
        identifier="AG"  #  PL 占座  AG是余额支付
        payment_data=list(filter(lambda k: k['identifier'] == identifier, payment_method_resp_data['data']))[0]
        add_parser_data['paymentTransactions'].append({
            "allPassengers":True,
            "paymentMethod":{
                "key":payment_data['key'],
                "identifier":identifier,
            },
            "currencyAmounts":[{
                "totalAmount":0,
                "exchangeRate":1,
                "currency":{"code":self.currency},
            }]
        })
        add_parser_data['seatSelections']=seatSelections
        add_parser_data['ancillaryPurchases']=ancillaryPurchases

        # 提交辅营数据 拿价格
        quotations_url = "https://agentapi.vietjetair.com/api/v14/Booking/quotations"
        logging.info(f"add_parser_data:{add_parser_data}")
        quotations_resp = self.session.post(quotations_url, json=add_parser_data)
        logging.info(f"quotations_resp:{quotations_resp.text}")
        quotations_resp_data=quotations_resp.json()
        totalprice=quotations_resp_data['data']['totalamountdeparture']
        curMethod = "VJ"
        if self.currency == "CNY":
            cnyamount, exchangeRate = float(totalprice), 1
        else:
            cnyamount, exchangeRate = self.convert2RMB(self.currency, float(totalprice), curMethod)
        resdict["exchangeRate"] = str(exchangeRate)
        self.writelog(self.logurl.format(orderno=order.orderno, mes=u"占座中",
                                         mesdesc="paymoney:{} {}, cnymoney:{} CNY, exchangeRate: {}".format(
                                             float(totalprice),
                                             self.currency,
                                             cnyamount, exchangeRate)))

        self.writelog(self.logurl.format(orderno=order.orderno, mes=u"占座中",
                                         mesdesc="minProfit: {}".format(resdict["minProfit"])))
        if order.totalprice < cnyamount + resdict["minProfit"]:
            logging.info(u'涨价 ......')
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = u"涨价, {}, {}, over:{}".format(order.totalprice, cnyamount,
                                                           cnyamount - order.totalprice)
            self.writelog(self.logurl.format(orderno=order.orderno, mes=u"占座失败",
                                             mesdesc=resdict["msg"]))
            return


        # 先检查客人是否申请退款=====
        url_order_status = "https://oa.tripto.cn/flightoa/order/getstatus"
        querystring = {"orderId": order.orderno}
        for _ in range(3):
            try:
                resp = requests.get(url_order_status, params=querystring, timeout=20)
                logging.info(f"{order.orderno}支付前出票状态:{resp.text}")
                # true 为可以出票
                if resp.text == "true":
                    break
                elif resp.text == "false":
                    resdict["payStatus"] = "12"
                    resdict["orderStatus"] = "0"
                    resdict["msg"] = '客人可能已经申请退票 请检查状态...'
                    self.writelog(self.rz_url.format(orderno=order.orderno, mes="支付失败", keyWordColor="red",
                                                     mesdesc=resdict["msg"]))
                    return

            except:
                logging.error("请求是否取消超时,正在重试....")
        # =====================
        # 以上为支付之前操作
        resdict["msg"] = "进入支付环节 ......"
        self.writelog(self.logurl.format(orderno=order.orderno, mes=u"占座中",mesdesc=resdict["msg"]))
        self.pay_run_log(order.orderno)
        try:
            create_url = "https://agentapi.vietjetair.com/api/v14/Booking/createbooking"
            create_resp = self.session.post(create_url, json=add_parser_data)
            logging.info(f"VJ 升单接口响应：{create_resp.status_code}")
            logging.info(f"VJ 升单接口响应：{create_resp.text}")
            pnrcode=create_resp.json()['data']['locator']
            if pnrcode:
                # resdict["payCardSource"] = "VJB2B"
                resdict["payCardNo"] = ""
                # resdict["bookingAccount"] = ""
                resdict["bookingOrderId"] = order.orderno
                resdict["bookingAllPrice"] = str(totalprice)
                resdict["bookingCurrency"] = self.currency
                resdict["availableCredits"] = self.availableCredits
                resdict["bookingPnr"] = pnrcode
                resdict["bookingStatus"] = "1"
                resdict["payStatus"] = "21"
                resdict["msg"] = u"支付成功"
                self.writelog(self.logurl.format(orderno=order.orderno, mes=resdict["msg"],
                                                 mesdesc="{}, {} {}".format(resdict["bookingPnr"], totalprice,
                                                                            self.currency)))
                self.writelog(self.logurl.format(orderno=order.orderno, mes=u"支付乘客", mesdesc=", ".join(namelist)))
                updateBalance(float(totalprice), self.currency, "VJ", account)
            else:
                logging.exception("error:")
                logging.info('支付异常, 可能支付成功, 请人工检查 ......')
                resdict["payStatus"] = "12"
                resdict["orderStatus"] = "0"
                resdict["msg"] = "支付异常, 可能支付成功, 请人工检查 ......"
                self.writelog(self.logurl.format(orderno=order.orderno, mes=u"支付失败",
                                                 mesdesc=resdict["msg"]))
                return
        except:
            logging.exception("error")
            resdict["payStatus"] = "12"
            resdict["orderStatus"] = "0"
            resdict["msg"] = "支付环节报错,请去代理人账户检查是否支付!!!"
            rz_url = "https://oa.tripto.cn/flightoa/order/addorderlog?orderid={orderno}&operator=robot&optname={mes}&optdesc={mesdesc}&keyWordColor={keyWordColor}"
            self.writelog(
                rz_url.format(orderno=order.orderno, mes="请检查支付状态", mesdesc=resdict["msg"], keyWordColor="red"))
            return


if __name__ == '__main__':
    config_log()
    obj = Order.form_dict({
        "flightnotime": {
            "5J805": "2024-10-01 13:35:00"
        },
        "isFlush": False,
        "brushkey": "",
        "currency": "",
        "session": "",
        "producttype": 0,
        "pricebig": "9446721#5J|@|",
        "fromtime": "2024-10-01 13:35:00",
        "isbrushbooking": 1,
        "luggageprice": 0,
        "price62": "0~PD~ ~5J~PDCRAZY~5203~~0~176~~X!1|5J~ 805~ ~~MNL~10/01/2024 13:35~SIN~10/01/2024 17:25~~@",
        "profit": 0,
        "brushtime": "",
        "contact": {
            "city": "",
            "firstname": "fei",
            "lastname": "zhang",
            "ctripemail": "",
            "useGuestMail": False,
            "nation": "",
            "email": "2751058111@qq.com",
            "postcode": "",
            "address": "",
            "sex": "",
            "phonenum": "18083560942"
        },
        "ispay": True,
        "paypnr": "",
        "lfprice": 0,
        "forcecurrency": "",
        "metadata": "",
        "orderid": 0,
        "otanamestr": "KUANG/ZHIHAI",
        "oriprice": 0,
        "pnr": "YRWOHN",
        "policyinfo": {
            "addinfo": {
                "qujian": -5.3
            },
            "oriprice": 220,
            "payinfo": {
                "payCurrency": ""
            }
        },
        "passengersinfo": "",
        "maxSeats": -1,
        "reason": "",
        "totalprice": 215,
        "rettime": "",
        "ttsname": "jtctrip",
        "forcepay": False,
        "seats": [
            {
                "paySeatPrice": 1000.0,
                "selectedSeatNo": "10A",
                "flightNo": "VJ1441",
                "name": "SHI/XIAOLIN",
                "paySeatCurrency": "JPY"
            },
        ],
        "luggages": [
            {
                "luggageItems": [
                    {
                        "dep": "HAN",
                        "pc": -1,
                        "arr": "PQC",
                        "weightPerPC": 20.0
                    }
                ],
                "isDb": False,
                "passengerName": "SHI/XIAOLIN",
                "cardType": "",
                "cardNum": ""
            },
            # {
            #     "luggageItems": [
            #         {
            #             "dep": "ICN",
            #             "pc": -1,
            #             "arr": "NRT",
            #             "weightPerPC": 23.0
            #         }
            #     ],
            #     "isDb": False,
            #     "passengerName": "LIM/RECHYUAN",
            #     "cardType": "",
            #     "cardNum": ""
            # },
        ],
        "passengers": [
            {
                "firstname": "XIAOLIN",
                "ticketno": "",
                "national": "SG",
                "cardexpired": "2025-12-15",
                "sex": "M",
                "cardtype": "PP",
                "birthday": "2001-01-19",
                "cardnum": "K2093126P",
                "lastname": "SHI",
                "cardissueplace": "SG"
            },
            # {
            #     "firstname": "RECHYUAN",
            #     "ticketno": "",
            #     "national": "SG",
            #     "cardexpired": "2025-12-15",
            #     "sex": "M",
            #     "cardtype": "PP",
            #     "birthday": "2018-05-24",
            #     "cardnum": "K2093126P",
            #     "lastname": "LIM",
            #     "cardissueplace": "SG"
            # },
            # {
            #     "firstname": "MENG",
            #     "ticketno": "",
            #     "national": "SG",
            #     "cardexpired": "2025-12-15",
            #     "sex": "M",
            #     "cardtype": "PP",
            #     "birthday": "2023-08-21",
            #     "cardnum": "K2093126P",
            #     "lastname": "WU",
            #     "cardissueplace": "SG"
            # }
        ],
        "remark": "",
        "retDate": "",  # 回程时间
        "priceinfo": "",
        "plmpnr": "",
        "createtime": "",
        "retFlightNo": "DD101",  # 回程航班号
        "method": "5JWEB",
        "isspecial": False,
        "carrier": "5J",
        "fromDate": "2026-01-10",  # 去程时间
        "dptAirport": "HAN",  # 出发地
        "arrAirport": "PQC",  # 抵达机场
        "fromFlightNo": "VJ1441",  # 去程航班号
        "realtimeprice": 0,
        "hasdevied": False,
        "returnrettime": "",
        "orderno": "2213238651",  # 订单编号
        "inorderno": "",
        "brushstatus": 2,
        "returnfromtime": ""
    })
    vj = VJB2BBooker()
    vj.book(obj)
