@echo off
chcp 65001
color 07

title Web项目管理

:start
cls
echo.
echo     校园学习资源分享平台项目管理
echo  ==================================
echo.
echo    1. 配置环境
echo    2. 初始化数据库
echo    3. 启动服务器
echo.
set /p opt=   选择(1-3): 

if %opt%==1 goto env
if %opt%==2 goto db
if %opt%==3 goto run
goto start

:env
cls
echo.
echo  配置环境
echo  ========
echo.
python -m venv venv
call venv\Scripts\activate
echo 正在安装依赖...
pip install -r requirements.txt
echo.
echo 完成！
pause
goto start

:db
cls
echo.
echo  初始化数据库
echo  ============
echo.
call venv\Scripts\activate
python init_db.py
echo.
echo 完成！
pause
goto start

:run
cls
echo.
echo  启动服务器
echo  ==========
echo.
call venv\Scripts\activate
python run.py
pause
goto start 