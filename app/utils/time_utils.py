import requests
from datetime import datetime, timedelta
import pytz

class NetworkTimeCache:
    def __init__(self):
        self.cached_time = None
        self.cache_time = None
        self.cache_duration = timedelta(minutes=5)  # 缓存5分钟
    
    def get_time(self):
        now = datetime.now(pytz.timezone('Asia/Shanghai'))
        
        # 如果缓存存在且未过期，返回计算后的时间
        if self.cached_time and self.cache_time:
            elapsed = now - self.cache_time
            if elapsed < self.cache_duration:
                return self.cached_time + elapsed
        
        try:
            # 使用淘宝的时间API
            response = requests.get(
                'http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp',
                timeout=2
            )
            if response.status_code == 200:
                timestamp = int(response.json()['data']['t']) / 1000
                self.cached_time = datetime.fromtimestamp(
                    timestamp,
                    pytz.timezone('Asia/Shanghai')
                )
                self.cache_time = now
                return self.cached_time
        except Exception as e:
            print(f"获取网络时间失败: {str(e)}")
        
        # 如果获取失败，返回系统时间
        return now

# 创建全局单例
_time_cache = NetworkTimeCache()

def get_current_time():
    """
    获取当前时间，优先使用网络时间
    """
    return _time_cache.get_time() 