document.addEventListener('DOMContentLoaded', function() {
    // 获取签到状态
    fetch('/user/checkin-status')
        .then(response => response.json())
        .then(data => {
            const consecutiveDays = document.getElementById('consecutiveDays');
            if (consecutiveDays) {
                consecutiveDays.textContent = data.consecutive_days;
            }
            
            // 更新签到按钮状态
            const checkinBtn = document.querySelector('#checkinArea button');
            if (checkinBtn) {
                if (data.today_checked) {
                    checkinBtn.classList.remove('btn-primary');
                    checkinBtn.classList.add('btn-secondary');
                    checkinBtn.disabled = true;
                    checkinBtn.textContent = '今日已签到';
                }
            }
        });
}); 