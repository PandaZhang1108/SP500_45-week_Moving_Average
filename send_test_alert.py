#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送标普500指数技术指标分析测试邮件
"""

import os
import datetime
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

def create_test_chart():
    """创建测试用的S&P500图表"""
    # 创建日期范围
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365)  # 一年的数据
    date_range = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days)]
    
    # 仅保留工作日
    date_range = [date for date in date_range if date.weekday() < 5]
    
    # 生成价格数据（带有上升趋势）
    n = len(date_range)
    trend = np.linspace(4000, 5000, n)  # 基础上升趋势
    noise = np.random.normal(0, 50, n)  # 随机波动
    price = trend + noise
    
    # 计算45周均线（约225个交易日）
    window_size = min(225, n//2)  # 确保窗口大小不超过数据点数量的一半
    ma_45w = np.array([np.mean(price[max(0, i-window_size):i+1]) for i in range(n)])
    
    # 创建图表
    plt.figure(figsize=(12, 6))
    
    # 绘制价格和均线
    plt.plot(date_range, price, label='S&P 500 Index', color='blue')
    plt.plot(date_range, ma_45w, label='45-Week Moving Average', color='red', linestyle='--')
    
    # 添加金叉信号标记
    signal_idx = int(n * 0.9)  # 假设在最近的10%处发生金叉
    plt.scatter(date_range[signal_idx], price[signal_idx], color='gold', s=100, zorder=5, marker='^')
    plt.annotate('Golden Cross', (date_range[signal_idx], price[signal_idx]),
               xytext=(-30, 30), textcoords='offset points',
               color='green', fontsize=12,
               arrowprops=dict(arrowstyle='->', color='green'))
    
    # 设置图表样式
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.title('S&P 500 Index with 45-Week Moving Average', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Price')
    
    # 格式化x轴日期
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.gcf().autofmt_xdate()
    
    # 添加图例
    plt.legend()
    
    # 保存图表
    chart_path = 'sp500_45wma_chart.png'
    plt.tight_layout()
    plt.savefig(chart_path, dpi=100)
    plt.close()
    
    print(f"测试图表已保存为: {chart_path}")
    return chart_path

def compose_test_analysis():
    """生成测试分析内容"""
    analysis = """【市场状态摘要】
标普500当前价格: 4733.59
移动均线状态: 价格位于45周均线上方, 价格位于50日均线上方, 价格位于200日均线上方, 50日均线位于200日均线上方
RSI值: 61.45 (中性区间)
MACD值: 12.4872, 信号线: 8.3381, 柱状图: 4.1491
VIX恐慌指数: 13.85 (正常波动范围)

【检测到的信号】
- 均线系统多头排列 [强信号]
  建议: 买入
- 50日均线上穿200日均线 [强信号]
  建议: 买入
- MACD线上穿信号线 [中等信号]
  建议: 买入
- RSI从超卖区域反弹 [中等信号]
  建议: 考虑做多

【指标说明】
• 45周移动平均线: 用于长期趋势识别。金叉表示进入上升趋势，死叉表示进入下降趋势
• 50/200日均线: 金叉(50日线在200日线上方)是看涨信号，死叉(50日线在200日线下方)是看跌信号
• RSI(14): 0-100之间的振荡器，低于30为超卖，高于70为超买
• MACD(12,26,9): 趋势指标，MACD线上穿信号线形成金叉，下穿形成死叉
• 布林带: 基于标准差的波动率指标，价格触及上轨可能超买，触及下轨可能超卖
• VIX恐慌指数: 市场波动预期指标，高于30表示市场恐慌，低于12表示过度乐观

【免责声明】
本分析仅供参考，不构成投资建议。投资决策应考虑个人风险承受能力和市场研究。
"""
    return analysis

def send_test_email():
    """发送测试邮件"""
    # 获取邮箱设置
    sender_email = input("请输入您的邮箱地址: ").strip()
    sender_password = input("请输入您的邮箱密码或授权码: ").strip()
    
    # 创建邮件
    msg = MIMEMultipart()
    
    # 设置邮件内容
    signal_date = datetime.datetime.now().strftime('%Y-%m-%d')
    subject = f"标普500指数提醒 - 技术指标信号 - {signal_date}"
    
    # 生成邮件正文
    body = f"""标普500指数技术分析提醒:

日期: {signal_date}
当前价格: 4733.59

{compose_test_analysis()}
"""
    
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = sender_email  # 发给自己
    
    # 添加文本内容
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 创建测试图表
    print("正在生成测试图表...")
    chart_path = create_test_chart()
    
    # 添加图表附件
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
                <h2>标普500指数技术分析报告</h2>
                <p><pre style="font-family: Arial, sans-serif; font-size: 14px;">{body}</pre></p>
                <p><img src="cid:chart" style="width:100%;max-width:1000px"></p>
                <p style="color:#666; font-size:12px;">* 本邮件由自动监控系统发送，请勿直接回复 *</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html', 'utf-8'))
    
    # 尝试发送邮件
    try:
        # 尝试连接到QQ邮箱
        print("正在连接到QQ邮箱服务器...")
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(sender_email, sender_password)
        
        # 发送邮件
        server.send_message(msg)
        server.quit()
        print(f"成功发送测试邮件到 {sender_email}")
        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始运行测试邮件发送程序...")
    send_test_email()