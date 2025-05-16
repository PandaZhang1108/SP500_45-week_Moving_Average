import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from datetime import datetime

class EmailNotifier:
    """发送邮件通知的类"""
    
    def __init__(self, config):
        """
        初始化EmailNotifier
        
        Args:
            config: 配置信息
        """
        self.config = config
        self.enabled = config['email']['enabled']
        self.smtp_server = config['email']['smtp_server']
        self.smtp_port = config['email']['smtp_port']
        self.sender_email = config['email']['sender_email']
        self.sender_password = os.environ.get('EMAIL_PASSWORD', '')  # 从环境变量获取密码
        self.recipient_email = config['email']['recipient_email']
        self.logger = logging.getLogger(__name__)
    
    def send_signal_notification(self, signal_type, signal_data, market_status, chart_path=None):
        """
        发送信号通知邮件
        
        Args:
            signal_type: 信号类型 ('buy' 或 'sell')
            signal_data: 信号数据
            market_status: 市场状态
            chart_path: 技术分析图表路径
            
        Returns:
            bool: 是否成功发送
        """
        if not self.enabled:
            self.logger.info("邮件通知未启用")
            return False
        
        if not signal_data:
            self.logger.warning(f"没有可用的{signal_type}信号数据")
            return False
        
        # 检查必要配置
        if not self.sender_password:
            self.logger.error("未设置邮箱密码，请在GitHub Secrets中设置EMAIL_PASSWORD")
            return False
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        
        # 设置邮件主题
        signal_date = signal_data['date']
        signal_price = signal_data['price']
        
        if signal_type == 'buy':
            subject = f"🟢 标普500指数买入信号 - {signal_date} (价格: {signal_price:.2f})"
        else:  # sell
            subject = f"🔴 标普500指数卖出信号 - {signal_date} (价格: {signal_price:.2f})"
        
        msg['Subject'] = subject
        
        # 构建邮件正文
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {'#4CAF50' if signal_type == 'buy' else '#F44336'}; color: white; padding: 10px; text-align: center; }}
                .section {{ margin-top: 20px; }}
                .section h2 {{ color: {'#4CAF50' if signal_type == 'buy' else '#F44336'}; }}
                table {{ width: 100%; border-collapse: collapse; }}
                table, th, td {{ border: 1px solid #ddd; }}
                th, td {{ padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .neutral {{ color: orange; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>标普500指数{'买入' if signal_type == 'buy' else '卖出'}信号</h1>
                </div>
                
                <div class="section">
                    <h2>信号详情</h2>
                    <table>
                        <tr><th>日期</th><td>{signal_data['date']}</td></tr>
                        <tr><th>价格</th><td>{signal_data['price']:.2f}</td></tr>
                        <tr><th>确认指标数量</th><td>{signal_data['total_signals']}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>触发指标</h2>
                    <table>
                        <tr><th>指标</th><th>状态</th></tr>
                        <tr><td>移动平均线</td><td class="{'positive' if signal_data['ma_signal'] > 0 else 'negative' if signal_data['ma_signal'] < 0 else 'neutral'}">{'金叉' if signal_data['ma_signal'] > 0 else '死叉' if signal_data['ma_signal'] < 0 else '无信号'}</td></tr>
                        <tr><td>RSI</td><td class="{'positive' if signal_data['rsi_signal'] > 0 else 'negative' if signal_data['rsi_signal'] < 0 else 'neutral'}">{'超卖反转' if signal_data['rsi_signal'] > 0 else '超买反转' if signal_data['rsi_signal'] < 0 else '无信号'}</td></tr>
                        <tr><td>MACD</td><td class="{'positive' if signal_data['macd_signal'] > 0 else 'negative' if signal_data['macd_signal'] < 0 else 'neutral'}">{'金叉' if signal_data['macd_signal'] > 0 else '死叉' if signal_data['macd_signal'] < 0 else '无信号'}</td></tr>
                        <tr><td>布林带</td><td class="{'positive' if signal_data['bb_signal'] > 0 else 'negative' if signal_data['bb_signal'] < 0 else 'neutral'}">{'触及下轨' if signal_data['bb_signal'] > 0 else '触及上轨' if signal_data['bb_signal'] < 0 else '无信号'}</td></tr>
                        <tr><td>价格与均线关系</td><td class="{'positive' if signal_data['price_ma_signal'] > 0 else 'negative' if signal_data['price_ma_signal'] < 0 else 'neutral'}">{'突破均线' if signal_data['price_ma_signal'] > 0 else '跌破均线' if signal_data['price_ma_signal'] < 0 else '无信号'}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>当前市场状态</h2>
                    <table>
                        <tr><th>当前价格</th><td>{market_status['price']:.2f}</td></tr>
                        <tr><th>市场趋势</th><td class="{'positive' if market_status['trend'] == '上升趋势' else 'negative'}">{market_status['trend']}</td></tr>
                        <tr><th>市场强弱</th><td class="{'positive' if market_status['strength'] in ['偏强', '超买'] else 'negative' if market_status['strength'] in ['偏弱', '超卖'] else 'neutral'}">{market_status['strength']}</td></tr>
                        <tr><th>市场动能</th><td class="{'positive' if market_status['momentum'] == '看涨' else 'negative'}">{market_status['momentum']}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <p>以下是技术指标的详细数据：</p>
                    <table>
                        <tr><th>指标</th><th>数值</th></tr>
                        <tr><td>{market_status['ma_short']:.2f}</td><td>{market_status['ma_short']:.2f}</td></tr>
                        <tr><td>{market_status['ma_long']:.2f}</td><td>{market_status['ma_long']:.2f}</td></tr>
                        <tr><td>RSI</td><td>{market_status['rsi']:.2f}</td></tr>
                        <tr><td>MACD</td><td>{market_status['macd']:.6f}</td></tr>
                        <tr><td>MACD信号线</td><td>{market_status['macd_signal']:.6f}</td></tr>
                        <tr><td>MACD柱状图</td><td class="{'positive' if market_status['macd_histogram'] > 0 else 'negative'}">{market_status['macd_histogram']:.6f}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <p>此邮件由标普500技术指标监控系统自动发送。</p>
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 添加HTML内容
        msg.attach(MIMEText(html_content, 'html'))
        
        # 添加图表附件
        if chart_path and os.path.exists(chart_path):
            with open(chart_path, 'rb') as f:
                img_data = f.read()
            
            img = MIMEImage(img_data, name=os.path.basename(chart_path))
            img.add_header('Content-ID', '<technical_chart>')
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(chart_path))
            msg.attach(img)
        
        # 发送邮件
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # 启用TLS加密
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"{'买入' if signal_type == 'buy' else '卖出'}信号通知邮件发送成功")
            return True
            
        except Exception as e:
            self.logger.error(f"发送邮件时出错: {str(e)}")
            return False
    
    def send_summary_email(self, market_status, latest_signals, chart_path=None):
        """
        发送每日摘要邮件
        
        Args:
            market_status: 市场状态
            latest_signals: 最近的信号
            chart_path: 技术分析图表路径
            
        Returns:
            bool: 是否成功发送
        """
        if not self.enabled:
            self.logger.info("邮件通知未启用")
            return False
        
        # 检查必要配置
        if not self.sender_password:
            self.logger.error("未设置邮箱密码，请在GitHub Secrets中设置EMAIL_PASSWORD")
            return False
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = f"📊 标普500指数每日市场分析 - {market_status['date']}"
        
        # 判断是否有最近的买入或卖出信号
        has_buy_signal = latest_signals['latest_buy'] is not None
        has_sell_signal = latest_signals['latest_sell'] is not None
        
        # 构建邮件正文
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 10px; text-align: center; }}
                .section {{ margin-top: 20px; }}
                .section h2 {{ color: #2196F3; }}
                table {{ width: 100%; border-collapse: collapse; }}
                table, th, td {{ border: 1px solid #ddd; }}
                th, td {{ padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .neutral {{ color: orange; }}
                .signal-box {{ padding: 10px; border-radius: 5px; margin-top: 10px; }}
                .buy-signal {{ background-color: rgba(76, 175, 80, 0.1); border: 1px solid #4CAF50; }}
                .sell-signal {{ background-color: rgba(244, 67, 54, 0.1); border: 1px solid #F44336; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>标普500指数每日市场分析</h1>
                </div>
                
                <div class="section">
                    <h2>当前市场状态</h2>
                    <table>
                        <tr><th>日期</th><td>{market_status['date']}</td></tr>
                        <tr><th>当前价格</th><td>{market_status['price']:.2f}</td></tr>
                        <tr><th>市场趋势</th><td class="{'positive' if market_status['trend'] == '上升趋势' else 'negative'}">{market_status['trend']}</td></tr>
                        <tr><th>市场强弱</th><td class="{'positive' if market_status['strength'] in ['偏强', '超买'] else 'negative' if market_status['strength'] in ['偏弱', '超卖'] else 'neutral'}">{market_status['strength']}</td></tr>
                        <tr><th>市场动能</th><td class="{'positive' if market_status['momentum'] == '看涨' else 'negative'}">{market_status['momentum']}</td></tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>技术指标</h2>
                    <table>
                        <tr><th>指标</th><th>数值</th></tr>
                        <tr><td>50日均线</td><td>{market_status['ma_short']:.2f}</td></tr>
                        <tr><td>200日均线</td><td>{market_status['ma_long']:.2f}</td></tr>
                        <tr><td>RSI</td><td>{market_status['rsi']:.2f}</td></tr>
                        <tr><td>MACD</td><td>{market_status['macd']:.6f}</td></tr>
                        <tr><td>MACD信号线</td><td>{market_status['macd_signal']:.6f}</td></tr>
                        <tr><td>MACD柱状图</td><td class="{'positive' if market_status['macd_histogram'] > 0 else 'negative'}">{market_status['macd_histogram']:.6f}</td></tr>
                    </table>
                </div>
        """
        
        # 如果有最近的买入信号，添加到邮件中
        if has_buy_signal:
            buy_data = latest_signals['latest_buy']
            html_content += f"""
                <div class="section">
                    <h2>最近买入信号</h2>
                    <div class="signal-box buy-signal">
                        <table>
                            <tr><th>日期</th><td>{buy_data['date']}</td></tr>
                            <tr><th>价格</th><td>{buy_data['price']:.2f}</td></tr>
                            <tr><th>确认指标数量</th><td>{buy_data['total_signals']}</td></tr>
                        </table>
                    </div>
                </div>
            """
        
        # 如果有最近的卖出信号，添加到邮件中
        if has_sell_signal:
            sell_data = latest_signals['latest_sell']
            html_content += f"""
                <div class="section">
                    <h2>最近卖出信号</h2>
                    <div class="signal-box sell-signal">
                        <table>
                            <tr><th>日期</th><td>{sell_data['date']}</td></tr>
                            <tr><th>价格</th><td>{sell_data['price']:.2f}</td></tr>
                            <tr><th>确认指标数量</th><td>{sell_data['total_signals']}</td></tr>
                        </table>
                    </div>
                </div>
            """
        
        # 结束HTML
        html_content += f"""
                <div class="section">
                    <p>此邮件由标普500技术指标监控系统自动发送。</p>
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 添加HTML内容
        msg.attach(MIMEText(html_content, 'html'))
        
        # 添加图表附件
        if chart_path and os.path.exists(chart_path):
            with open(chart_path, 'rb') as f:
                img_data = f.read()
            
            img = MIMEImage(img_data, name=os.path.basename(chart_path))
            img.add_header('Content-ID', '<technical_chart>')
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(chart_path))
            msg.attach(img)
        
        # 发送邮件
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # 启用TLS加密
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info("每日摘要邮件发送成功")
            return True
            
        except Exception as e:
            self.logger.error(f"发送邮件时出错: {str(e)}")
            return False