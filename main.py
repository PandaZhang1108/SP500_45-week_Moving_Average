#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标普500指数45周均线策略监控脚本
自动检测金叉和死叉信号，并通过邮件发送提醒
"""

import os
import datetime
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# 设置中文字体（MacOS可用"Arial Unicode MS"或"PingFang SC"）
try:
    # 尝试加载中文字体
    chinese_font = FontProperties(family='PingFang SC')
except:
    # 如果失败，使用系统默认字体
    chinese_font = FontProperties()

def get_sp500_data():
    """获取标普500指数数据"""
    # 下载近两年的数据（确保有足够的历史数据计算均线）
    df = yf.download('^GSPC', period='2y')
    
    # 添加45周均线 (45*5=225天，因为一周约有5个交易日)
    df['45WMA'] = df['Close'].rolling(window=225).mean()
    
    return df

def check_cross_signals(df):
    """检查金叉和死叉信号"""
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
    plot_data = df.iloc[-252:].copy()
    
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
    chart_path = 'sp500_45wma_chart.png'
    plt.savefig(chart_path, dpi=100)
    plt.close()
    
    return chart_path

def send_email_alert(subject, body, chart_path=None):
    """发送邮件提醒"""
    # 从环境变量获取邮箱设置
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASS')
    receiver_email = os.environ.get('EMAIL_USER')  # 发给自己
    
    if not sender_email or not sender_password:
        print("错误: 未设置邮箱环境变量 EMAIL_USER 或 EMAIL_PASS")
        return False
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
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
                <p>{body}</p>
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
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, sender_password)
            is_gmail = True
        except:
            # 如果Gmail连接失败，尝试QQ邮箱
            try:
                server = smtplib.SMTP_SSL('smtp.qq.com', 465)
                server.login(sender_email, sender_password)
                is_gmail = False
            except Exception as e:
                print(f"邮箱登录失败: {str(e)}")
                return False
        
        # 发送邮件
        server.send_message(msg)
        server.quit()
        print(f"成功发送邮件到 {receiver_email} (使用{'Gmail' if is_gmail else 'QQ邮箱'})")
        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

def main():
    """主函数"""
    print(f"开始运行标普500指数45周均线监控... {datetime.datetime.now()}")
    
    # 获取数据
    try:
        data = get_sp500_data()
        print(f"成功获取标普500指数数据，共{len(data)}个交易日")
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return
    
    # 检查信号
    golden_cross, death_cross, signal_date = check_cross_signals(data)
    
    # 如果没有信号，可以选择创建一个定期报告
    if not golden_cross and not death_cross:
        # 检查是否是每周一（工作日=0）可以发送周报
        if datetime.datetime.now().weekday() == 0:
            # 创建图表
            chart_path = create_chart(data)
            
            # 准备周报内容
            latest_price = data['Close'].iloc[-1]
            latest_ma = data['45WMA'].iloc[-1]
            price_vs_ma = "高于" if latest_price > latest_ma else "低于"
            percent_diff = abs(latest_price - latest_ma) / latest_ma * 100
            
            subject = f"标普500指数周报 - {datetime.datetime.now().strftime('%Y-%m-%d')}"
            body = f"""标普500指数周报:

当前价格: {latest_price:.2f}
45周均线: {latest_ma:.2f}
当前价格{price_vs_ma}45周均线 {percent_diff:.2f}%

无金叉或死叉信号。
"""
            
            # 发送周报邮件
            send_email_alert(subject, body, chart_path)
        else:
            print("今日无交叉信号，且不是周一，不发送报告")
        
        return
    
    # 如果有信号，创建带有标记的图表
    chart_path = create_chart(data, signal_date, golden_cross, death_cross)
    
    # 准备邮件内容
    signal_type = "金叉" if golden_cross else "死叉"
    action = "买入" if golden_cross else "卖出"
    
    subject = f"重要! 标普500指数出现{signal_type}信号 - {signal_date.strftime('%Y-%m-%d')}"
    body = f"""标普500指数45周均线监控提醒:

日期: {signal_date.strftime('%Y-%m-%d')}
信号类型: {signal_type}
建议操作: {action}

当前价格: {data['Close'].iloc[-1]:.2f}
45周均线: {data['45WMA'].iloc[-1]:.2f}

* 本邮件由自动监控系统生成，请结合其他指标综合判断。
"""
    
    # 发送提醒邮件
    send_email_alert(subject, body, chart_path)

if __name__ == "__main__":
    main()