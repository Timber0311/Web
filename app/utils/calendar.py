from calendar import monthcalendar
from datetime import date, timedelta

def get_month_calendar(year, month, checkin_dates):
    """
    生成月份日历数据
    :param year: 年份
    :param month: 月份
    :param checkin_dates: 已签到日期集合
    :return: 日历数据列表
    """
    # 获取当月日历
    cal = monthcalendar(year, month)
    today = date.today()
    
    # 转换为更易于使用的格式
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # 填充空白日期
                week_data.append({
                    'day': '',
                    'is_today': False,
                    'is_checked': False,
                    'is_future': False
                })
            else:
                current_date = date(year, month, day)
                week_data.append({
                    'day': day,
                    'is_today': current_date == today,
                    'is_checked': current_date in checkin_dates,
                    'is_future': current_date > today
                })
        calendar_data.append(week_data)
    
    return calendar_data 