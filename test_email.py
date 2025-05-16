#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S&P 500 Technical Indicator Analysis Email Test Script
"""

import os
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# 从主脚本导入需要的函数
from main import compose_signal_analysis, create_chart

# 设置英文字体
plt.rcParams['font.family'] = 'Arial'

def create_test_data():
    """创建测试数据，包含技术指标"""
    # 创建日期范围
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=500)
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # 'B'表示仅工作日
    
    # 设置随机种子以确保结果可重现
    np.random.seed(42)
    
    # 创建价格数据
    close_price = 4500 + np.cumsum(np.random.normal(0, 30, len(date_range)))
    
    # 创建DataFrame
    df = pd.DataFrame({
        'Open': close_price - np.random.normal(0, 10, len(date_range)),
        'High': close_price + np.random.normal(15, 5, len(date_range)),
        'Low': close_price - np.random.normal(15, 5, len(date_range)),
        'Close': close_price,
        'Volume': np.random.normal(1000000, 200000, len(date_range))
    }, index=date_range)
    
    # 添加技术指标
    # 45周均线 (45*5=225天，因为一周约有5个交易日)
    df['45WMA'] = df['Close'].rolling(window=225).mean()
    
    # 50日和200日移动平均线
    df['50MA'] = df['Close'].rolling(window=50).mean()
    df['200MA'] = df['Close'].rolling(window=200).mean()
    
    # 计算布林带 (20日, 2标准差)
    rolling_mean = df['Close'].rolling(window=20).mean()
    rolling_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = rolling_mean + (rolling_std * 2)
    df['BB_Middle'] = rolling_mean
    df['BB_Lower'] = rolling_mean - (rolling_std * 2)
    
    # 计算RSI (14日)
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    
    # 对于第14天以后的数据使用Wilder平滑
    for i in range(14, len(df)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * 13 + gain.iloc[i]) / 14
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * 13 + loss.iloc[i]) / 14
        
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算MACD(12,26,9)
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # 添加VIX模拟数据
    df['VIX'] = 20 + np.random.normal(0, 5, len(date_range))
    
    return df

def create_test_signals():
    """Create test signals"""
    signals = {
        '45WMA': {'type': 'Golden Cross', 'action': 'Buy', 'strength': 'strong'},
        '50_200MA': {'type': 'Golden Cross', 'action': 'Buy', 'strength': 'strong', 'desc': '50-day MA crosses above 200-day MA'},
        'rsi': {'type': 'Rebound from Oversold', 'action': 'Consider Long Position', 'strength': 'medium', 'desc': 'RSI rebounds from oversold territory'},
        'macd': {'type': 'Golden Cross', 'action': 'Buy', 'strength': 'medium', 'desc': 'MACD crosses above Signal Line'},
        'vix': {'type': 'Moderate Fear', 'action': 'Watch', 'strength': 'medium', 'desc': 'VIX Fear Index moderate (22.45)'}
    }
    return signals

def send_test_email():
    """发送测试邮件"""
    # 获取邮箱设置
    sender_email = input("Please enter your email address: ").strip()
    sender_password = input("Please enter your email password or authorization code: ").strip()
    
    # 创建测试数据
    print("Creating test data...")
    df = create_test_data()
    signals = create_test_signals()
    signal_date = df.index[-1]
    
    # 创建图表
    print("正在生成测试图表...")
    chart_path = create_chart(df, signal_date, True, False, signals)
    
    # 生成邮件内容
    subject = f"Test Email - S&P 500 Alert - Multiple Technical Indicators - {datetime.datetime.now().strftime('%Y-%m-%d')}"
    
    # 准备邮件正文
    body = f"""S&P 500 Technical Analysis Alert (Test Email):

Date: {signal_date.strftime('%Y-%m-%d')}
Current Price: {df['Close'].iloc[-1]:.2f}

{compose_signal_analysis(df, signals)}

* This is a test email with simulated data, for testing email functionality only *
"""
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = sender_email  # 发给自己
    
    # 添加文本内容
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 添加图表附件
    if os.path.exists(chart_path):
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
                <h2>S&P 500 Technical Analysis Report (Test Email)</h2>
                <p><pre style="font-family: Arial, sans-serif; font-size: 14px;">{body}</pre></p>
                <p><img src="cid:chart" style="width:100%;max-width:1000px"></p>
                <p style="color:#666; font-size:12px;">* This is a test email with simulated data, for testing email functionality only *</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html', 'utf-8'))
    
    # 尝试发送邮件
    try:
        # 先尝试Gmail
        try:
            print("Trying to send via Gmail...")
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, sender_password)
            is_gmail = True
        except Exception as e:
            print(f"Gmail login failed: {str(e)}")
            # 如果Gmail连接失败，尝试QQ邮箱
            try:
                print("Trying to send via QQ Mail...")
                server = smtplib.SMTP_SSL('smtp.qq.com', 465)
                server.login(sender_email, sender_password)
                is_gmail = False
            except Exception as e:
                print(f"QQ Mail login failed: {str(e)}")
                return False
        
        # 发送邮件
        server.send_message(msg)
        server.quit()
        print(f"Successfully sent test email to {sender_email} (using {'Gmail' if is_gmail else 'QQ Mail'})")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting email test program...")
    send_test_email() 