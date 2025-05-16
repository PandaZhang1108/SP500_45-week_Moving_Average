#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试标普500指数监控系统
使用模拟数据测试完整流程
"""

import os
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# 设置中文字体
try:
    chinese_font = FontProperties(family='PingFang SC')
except:
    chinese_font = FontProperties()

def generate_mock_data(signal_type=None):
    """生成模拟的标普500数据
    
    参数:
        signal_type: 可以是'golden_cross', 'death_cross', 或None(无信号)
    """
    # 创建日期范围 - 两年的数据
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=2*365)
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # 'B'表示工作日
    
    # 创建基本趋势
    n = len(date_range)
    base = np.linspace(3000, 4500, n)  # 基础趋势线
    
    # 添加一些波动
    noise = np.random.normal(0, 100, n)
    price = base + noise
    
    # 创建DataFrame
    df = pd.DataFrame({
        'Open': price - np.random.normal(0, 20, n),
        'High': price + np.random.normal(0, 30, n),
        'Low': price - np.random.normal(0, 30, n),
        'Close': price,
        'Volume': np.random.normal(5000000, 1000000, n)
    }, index=date_range)
    
    # 计算45周均线
    df['45WMA'] = df['Close'].rolling(window=225).mean()
    
    # 如果指定了信号类型，修改最近的数据点创建信号
    if signal_type and len(df) > 225:  # 确保有足够的数据计算均线
        if signal_type == 'golden_cross':
            # 创建金叉 - 价格从下方穿过均线
            df.loc[df.index[-2], 'Close'] = df.loc[df.index[-2], '45WMA'] * 0.99  # 昨天低于均线
            df.loc[df.index[-1], 'Close'] = df.loc[df.index[-1], '45WMA'] * 1.01  # 今天高于均线
        
        elif signal_type == 'death_cross':
            # 创建死叉 - 价格从上方穿过均线
            df.loc[df.index[-2], 'Close'] = df.loc[df.index[-2], '45WMA'] * 1.01  # 昨天高于均线
            df.loc[df.index[-1], 'Close'] = df.loc[df.index[-1], '45WMA'] * 0.99  # 今天低于均线
    
    return df

def check_cross_signals(df):
    """检查金叉和死叉信号"""
    # 确保数据不为空
    if df is None or len(df) == 0:
        print("警告: 数据为空，无法检查交叉信号")
        return False, False, None
        
    # 确保至少有两个数据点进行比较
    if len(df) < 3:
        print(f"警告: 数据点数量不足 (仅有 {len(df)} 行)，需要至少3个数据点")
        return False, False, df.index[-1] if len(df) > 0 else None
    
    # 取最近的数据进行判断
    recent_data = df.tail(3).copy()
    
    # 计算前一天和当天的关系
    yesterday = recent_data.index[-2]
    today = recent_data.index[-1]
    
    # 初始化信号
    golden_cross = False
    death_cross = False
    
    # 金叉：价格从下方穿过均线
    if df['Close'][yesterday] < df['45WMA'][yesterday] and df['Close'][today] > df['45WMA'][today]:
        golden_cross = True
    
    # 死叉：价格从上方穿过均线
    if df['Close'][yesterday] > df['45WMA'][yesterday] and df['Close'][today] < df['45WMA'][today]:
        death_cross = True
    
    return golden_cross, death_cross, today

def create_chart(df, signal_date=None, is_golden=False, is_death=False):
    """创建标普500和45周均线图表"""
    # 创建图形
    plt.figure(figsize=(12, 6))
    
    # 只绘制最近一年的数据
    plot_data = df.iloc[-252:].copy() if len(df) > 252 else df.copy()
    
    # 绘制收盘价和45周均线
    plt.plot(plot_data.index, plot_data['Close'], label='标普500指数', color='blue')
    plt.plot(plot_data.index, plot_data['45WMA'], label='45周移动平均线', color='red', linestyle='--')
    
    # 如果有信号，标记在图上
    if signal_date is not None:
        if signal_date in plot_data.index:
            if is_golden:
                plt.scatter(signal_date, plot_data.loc[signal_date, 'Close'], 
                         s=100, color='gold', zorder=5, marker='^')
                plt.annotate('金叉信号', (signal_date, plot_data.loc[signal_date, 'Close']),
                          xytext=(10, 30), textcoords='offset points',
                          color='green', fontproperties=chinese_font,
                          arrowprops=dict(arrowstyle='->', color='green'))
            elif is_death:
                plt.scatter(signal_date, plot_data.loc[signal_date, 'Close'], 
                         s=100, color='black', zorder=5, marker='v')
                plt.annotate('死叉信号', (signal_date, plot_data.loc[signal_date, 'Close']),
                          xytext=(10, -30), textcoords='offset points',
                          color='red', fontproperties=chinese_font,
                          arrowprops=dict(arrowstyle='->', color='red'))
    
    # 设置图表格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.gcf().autofmt_xdate()  # 自动格式化x轴日期标签
    
    # 添加标题和标签
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    plt.title(f'标普500指数与45周均线 (截至{current_date})', fontproperties=chinese_font)
    plt.xlabel('日期', fontproperties=chinese_font)
    plt.ylabel('价格', fontproperties=chinese_font)
    plt.legend(prop=chinese_font)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 保存图表
    plt.tight_layout()
    chart_path = 'test_sp500_chart.png'
    plt.savefig(chart_path, dpi=100)
    plt.close()
    
    return chart_path

def send_email_alert(subject, body, chart_path=None):
    """发送邮件提醒"""
    # 手动输入邮箱信息
    sender_email = input("请输入你的邮箱地址: ")
    sender_password = input("请输入你的邮箱密码或授权码: ")
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = sender_email  # 发给自己
    
    # 添加文本内容
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 如果有图表，添加为附件
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(chart_path))
            msg.attach(img)
        
        # 同时在邮件正文中嵌入图片
        with open(chart_path, 'rb') as f:
            img_inline = MIMEImage(f.read())
            img_inline.add_header('Content-ID', '<chart>')
            msg.attach(img_inline)
        
        # 添加HTML内容，引用嵌入的图片
        html = f"""
        <html>
            <body>
                <p>{body.replace('\n', '<br>')}</p>
                <p><img src="cid:chart" style="width:100%;max-width:800px"></p>
                <p>* 本邮件由自动监控系统发送，请勿直接回复 *</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html', 'utf-8'))
    
    # 尝试发送邮件
    try:
        # 尝试连接到Gmail SMTP服务器
        try:
            print("尝试连接Gmail服务器...")
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, sender_password)
            is_gmail = True
            print("成功连接到Gmail服务器!")
        except Exception as e:
            print(f"Gmail连接失败: {str(e)}")
            # 如果Gmail连接失败，尝试QQ邮箱
            try:
                print("尝试连接QQ邮箱服务器...")
                server = smtplib.SMTP_SSL('smtp.qq.com', 465)
                server.login(sender_email, sender_password)
                is_gmail = False
                print("成功连接到QQ邮箱服务器!")
            except Exception as e:
                print(f"QQ邮箱登录失败: {str(e)}")
                return False
        
        # 发送邮件
        server.send_message(msg)
        server.quit()
        print(f"成功发送邮件到 {sender_email} (使用{'Gmail' if is_gmail else 'QQ邮箱'})")
        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

def test_monitor_system():
    """测试标普500监控系统的完整流程"""
    print("=== 标普500指数技术指标监控系统测试 ===")
    
    # 选择测试模式
    print("\n请选择测试模式:")
    print("1. 无信号模式 (测试周报)")
    print("2. 金叉信号模式 (测试买入提醒)")
    print("3. 死叉信号模式 (测试卖出提醒)")
    
    choice = input("请输入选项 (1/2/3): ")
    
    # 根据选择生成不同的模拟数据
    signal_type = None
    if choice == '2':
        signal_type = 'golden_cross'
        print("\n生成带金叉信号的模拟数据...")
    elif choice == '3':
        signal_type = 'death_cross'
        print("\n生成带死叉信号的模拟数据...")
    else:
        print("\n生成无信号的模拟数据...")
    
    # 生成模拟数据
    data = generate_mock_data(signal_type)
    print(f"成功生成模拟数据，共{len(data)}个交易日")
    
    # 检查信号
    golden_cross, death_cross, signal_date = check_cross_signals(data)
    
    if golden_cross:
        print("检测到金叉信号!")
    elif death_cross:
        print("检测到死叉信号!")
    else:
        print("未检测到交叉信号")
    
    # 创建图表
    chart_path = create_chart(data, signal_date, golden_cross, death_cross)
    print(f"成功创建图表: {chart_path}")
    
    # 如果没有信号，发送周报
    if not golden_cross and not death_cross:
        # 准备周报内容
        latest_price = data['Close'].iloc[-1]
        latest_ma = data['45WMA'].iloc[-1]
        price_vs_ma = "高于" if latest_price > latest_ma else "低于"
        percent_diff = abs(latest_price - latest_ma) / latest_ma * 100
        
        subject = f"标普500指数周报 - {datetime.datetime.now().strftime('%Y-%m-%d')} [测试]"
        body = f"""标普500指数周报 [测试模式]:

当前价格: {latest_price:.2f}
45周均线: {latest_ma:.2f}
当前价格{price_vs_ma}45周均线 {percent_diff:.2f}%

无金叉或死叉信号。

* 这是一封测试邮件，使用的是模拟数据 *
"""
        
        # 发送周报邮件
        print("\n准备发送测试周报邮件...")
        send_email_alert(subject, body, chart_path)
    else:
        # 如果有信号，发送信号提醒
        signal_type = "金叉" if golden_cross else "死叉"
        action = "买入" if golden_cross else "卖出"
        
        subject = f"重要! 标普500指数出现{signal_type}信号 - [测试]"
        body = f"""标普500指数技术指标监控提醒 [测试模式]:

日期: {signal_date.strftime('%Y-%m-%d')}
信号类型: {signal_type}
建议操作: {action}

当前价格: {data['Close'].iloc[-1]:.2f}
45周均线: {data['45WMA'].iloc[-1]:.2f}

* 这是一封测试邮件，使用的是模拟数据 *
* 本邮件由自动监控系统生成，请结合其他指标综合判断。
"""
        
        # 发送提醒邮件
        print(f"\n准备发送{signal_type}信号测试邮件...")
        send_email_alert(subject, body, chart_path)

if __name__ == "__main__":
    test_monitor_system() 