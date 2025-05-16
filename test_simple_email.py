#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标普500指数邮件测试简化脚本
此脚本仅测试邮件发送功能，不依赖pandas和matplotlib
"""

import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

def send_test_email():
    """发送测试邮件"""
    # 获取邮箱设置
    sender_email = input("请输入您的邮箱地址: ").strip()
    sender_password = input("请输入您的邮箱密码或授权码: ").strip()
    
    # 创建邮件
    msg = MIMEMultipart()
    
    # 设置邮件内容
    subject = f"标普500指数监控系统测试邮件 - {datetime.datetime.now().strftime('%Y-%m-%d')}"
    body = """S&P 500 Technical Analysis Test Email

This is a test email to verify the email sending functionality.
No chart is included in this simplified test.

The email functionality works if you can see this message.
"""
    
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = sender_email  # 发给自己
    
    # 添加文本内容
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # 添加HTML内容
    html = f"""
    <html>
        <body>
            <h2>S&P 500 Technical Analysis Report (Test Email)</h2>
            <p><pre style="font-family: Arial, sans-serif; font-size: 14px;">{body}</pre></p>
            <p style="color:#666; font-size:12px;">* 这是一封测试邮件，用于验证邮件发送功能 *</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    
    # 尝试发送邮件
    try:
        # 先尝试Gmail
        try:
            print("尝试使用Gmail发送...")
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, sender_password)
            is_gmail = True
        except Exception as e:
            print(f"Gmail登录失败: {str(e)}")
            # 如果Gmail连接失败，尝试QQ邮箱
            try:
                print("尝试使用QQ邮箱发送...")
                server = smtplib.SMTP_SSL('smtp.qq.com', 465)
                server.login(sender_email, sender_password)
                is_gmail = False
            except Exception as e:
                print(f"QQ邮箱登录失败: {str(e)}")
                return False
        
        # 发送邮件
        server.send_message(msg)
        server.quit()
        print(f"成功发送测试邮件到 {sender_email} (使用{'Gmail' if is_gmail else 'QQ邮箱'})")
        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始运行简化版邮件测试程序...")
    send_test_email() 