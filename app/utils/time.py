import logging
import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def get_network_time():
    """获取网络时间，如果失败则使用本地时间"""
    # 定义多个时间服务器
    time_servers = [
        'http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp',
        'http://worldtimeapi.org/api/timezone/Asia/Shanghai',
        'http://www.beijing-time.org/time.asp'
    ]
    
    for server in time_servers:
        try:
            session = requests.Session()
            # 设置较短的超时时间和更少的重试次数
            retries = Retry(total=1, backoff_factor=0.1)
            session.mount('http://', HTTPAdapter(max_retries=retries))
            
            response = session.get(server, timeout=1)
            
            if response.status_code == 200:
                if 'taobao' in server:
                    return float(response.json()['data']['t']) / 1000
                elif 'worldtimeapi' in server:
                    return float(response.json()['unixtime'])
                else:
                    # 其他服务器的处理逻辑
                    pass
                    
        except Exception as e:
            logging.debug(f"从 {server} 获取时间失败: {str(e)}")
            continue
    
    # 所有服务器都失败时使用本地时间
    logging.debug("所有时间服务器均不可用，使用本地时间")
    return time.time() 