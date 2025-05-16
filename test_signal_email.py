#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试标普500指数金叉信号邮件发送功能
不使用pandas和numpy，避免版本兼容性问题
"""

import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

def send_signal_email():
    """发送金叉信号测试邮件"""
    print("准备发送金叉信号测试邮件...")
    
    # 手动输入邮箱信息
    sender_email = input("请输入你的邮箱地址: ")
    sender_password = input("请输入你的邮箱密码或授权码: ")
    
    # 邮件内容
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    subject = f"重要! 标普500指数出现金叉信号 - {current_date} [测试]"
    
    # 模拟数据
    price = 4873.45
    ma_value = 4820.35
    percentage = ((price - ma_value) / ma_value * 100)
    
    body = f"""标普500指数技术指标监控提醒 [测试模式]:

日期: {current_date}
信号类型: 金叉
建议操作: 买入

当前价格: {price:.2f}
45周均线: {ma_value:.2f}
当前价格高于45周均线 {percentage:.2f}%

金叉信号表明市场可能进入上升趋势，但请结合其他指标综合判断。

* 这是一封测试邮件 *
* 本邮件由自动监控系统生成 *
"""
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = sender_email  # 发给自己
    
    # 添加文本内容
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 使用示例图片文件，如果存在的话
    chart_path = "sp500_45wma_chart.png"
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
                <p>{body.replace('\n', '<br>')}</p>
                <p><img src="cid:chart" style="width:100%;max-width:800px"></p>
                <p>* 本邮件由自动监控系统发送，仅供测试 *</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        print(f"已添加图表附件: {chart_path}")
    else:
        print(f"警告: 未找到图表文件 {chart_path}，将只发送文本邮件")
        # 添加简单的HTML内容
        html = f"""
        <html>
            <body>
                <p>{body.replace('\n', '<br>')}</p>
                <p><b>注意：未找到图表文件，此为纯文本测试邮件</b></p>
                <p>* 本邮件由自动监控系统发送，仅供测试 *</p>
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
        print(f"成功发送金叉信号测试邮件到 {sender_email} (使用{'Gmail' if is_gmail else 'QQ邮箱'})")
        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== 标普500指数技术指标监控系统金叉信号邮件测试 ===\n")
    send_signal_email() 