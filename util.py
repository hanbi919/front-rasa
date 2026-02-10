import configparser
import hashlib


def md5_encrypt(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def md5_encrypt_16_lower(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()[8:24]


# XML 转义函数
def escape_xml(s):
    if not isinstance(s, str):
        s = str(s)
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '“')  # 转成全角双引号
    s = s.replace("'", '‘')  # 转成全角单引号
    return s


# 读取配置文件
def getConfig():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    return dict(
        SMS_API_URL=config['SMS']['SMS_API_URL'],
        ENTERPRISE_ID=config['SMS']['ENTERPRISE_ID'],
        USERNAME=config['SMS']['USERNAME'],
        PASSWORD=config['SMS']['PASSWORD'],
        MSG_CONTENT=config['SMS']['MSG_CONTENT'],
        TOKEN=config['SMS']['X-Access-Token'],
        ALARM_CRON=config['SMS']['ALARM_CRON'],
        ALARM_COUNT=int(config['SMS']['ALARM_COUNT']),
        ALARM_PHONE=config['SMS']['ALARM_PHONE'],
        ALARM_CONTENT=config['SMS']['ALARM_CONTENT']
    )

# TOKEN
# print(md5_encrypt("ccznkf@2026@"))
