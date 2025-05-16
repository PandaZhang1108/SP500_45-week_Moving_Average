#!/usr/bin/env python
"""
邮件模板预览 - 展示不同类型邮件的HTML内容，包含图表可视化
"""

from datetime import datetime
import os
import io
import base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def generate_chart_with_annotations(signal_type='buy'):
    """生成带有数字标注的技术分析图表"""
    # 创建模拟数据，实际应用中这里应该替换为真实数据
    dates = pd.date_range(start='2023-04-01', periods=60, freq='D')
    np.random.seed(42)
    close_prices = np.cumsum(np.random.normal(0, 1, 60)) + 4500
    
    # 计算指标
    ma50 = pd.Series(close_prices).rolling(50).mean()
    ma200 = pd.Series(close_prices).rolling(200).mean()
    
    # RSI计算
    delta = pd.Series(close_prices).diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # MACD计算
    ema12 = pd.Series(close_prices).ewm(span=12).mean()
    ema26 = pd.Series(close_prices).ewm(span=26).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9).mean()
    macd_hist = macd - macd_signal
    
    # 创建数据框
    data = pd.DataFrame({
        'Date': dates,
        'Close': close_prices,
        'MA50': ma50,
        'MA200': ma200,
        'RSI': rsi,
        'MACD': macd,
        'MACD_Signal': macd_signal,
        'MACD_Hist': macd_hist
    })
    
    # 创建图表
    fig = plt.figure(figsize=(10, 8))
    
    # 主图 - K线图
    ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=2)
    
    # 绘制价格和移动平均线
    ax1.plot(data['Date'], data['Close'], 'b-', label='Price')
    ax1.plot(data['Date'], data['MA50'], 'g-', label='50-Day MA')
    ax1.plot(data['Date'], data['MA200'], 'r-', label='200-Day MA')
    
    # 标注当前价格
    latest_price = data['Close'].iloc[-1]
    ax1.annotate(f'Current Price: {latest_price:.2f}', 
                xy=(data['Date'].iloc[-1], latest_price),
                xytext=(-100, 30), textcoords='offset points',
                arrowprops=dict(arrowstyle='->'))
    
    # 模拟信号点
    signal_idx = -10 if signal_type == 'buy' else -15
    signal_date = data['Date'].iloc[signal_idx]
    signal_price = data['Close'].iloc[signal_idx]
    
    # 标注信号点
    color = 'green' if signal_type == 'buy' else 'red'
    signal_text = 'Buy Signal' if signal_type == 'buy' else 'Sell Signal'
    ax1.scatter(signal_date, signal_price, color=color, s=100, zorder=5)
    ax1.annotate(f'{signal_text}: {signal_price:.2f}', 
                xy=(signal_date, signal_price),
                xytext=(30, 30 if signal_type == 'buy' else -30), 
                textcoords='offset points',
                color=color, weight='bold',
                arrowprops=dict(arrowstyle='->', color=color))
    
    ax1.set_title('S&P 500 Price Trend & Moving Averages')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # RSI子图
    ax2 = plt.subplot2grid((4, 1), (2, 0), rowspan=1, sharex=ax1)
    ax2.plot(data['Date'], data['RSI'], color='purple')
    ax2.axhline(70, color='red', linestyle='--')
    ax2.axhline(30, color='green', linestyle='--')
    
    # 标注当前RSI值
    current_rsi = data['RSI'].iloc[-1]
    ax2.annotate(f'RSI: {current_rsi:.2f}', 
                xy=(data['Date'].iloc[-1], current_rsi),
                xytext=(-60, 10), textcoords='offset points')
    
    ax2.fill_between(data['Date'], 70, 100, color='red', alpha=0.1)
    ax2.fill_between(data['Date'], 0, 30, color='green', alpha=0.1)
    ax2.set_ylim(0, 100)
    ax2.set_title('RSI Indicator (Overbought>70, Oversold<30)')
    ax2.grid(True, alpha=0.3)
    
    # MACD子图
    ax3 = plt.subplot2grid((4, 1), (3, 0), rowspan=1, sharex=ax1)
    ax3.plot(data['Date'], data['MACD'], label='MACD', color='blue')
    ax3.plot(data['Date'], data['MACD_Signal'], label='Signal Line', color='orange')
    
    # 绘制MACD柱状图
    for i in range(len(data)):
        if data['MACD_Hist'].iloc[i] >= 0:
            ax3.bar(data['Date'].iloc[i], data['MACD_Hist'].iloc[i], color='green', width=1.0)
        else:
            ax3.bar(data['Date'].iloc[i], data['MACD_Hist'].iloc[i], color='red', width=1.0)
    
    # 标注当前MACD值
    current_macd = data['MACD'].iloc[-1]
    current_signal = data['MACD_Signal'].iloc[-1]
    ax3.annotate(f'MACD: {current_macd:.4f}\nSignal Line: {current_signal:.4f}', 
                xy=(data['Date'].iloc[-1], current_macd),
                xytext=(-120, 20), textcoords='offset points')
    
    ax3.set_title('MACD Indicator')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)
    
    # 设置x轴格式
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # 转换为base64编码的图像，可以嵌入到HTML邮件中
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    
    return image_base64

def create_heatmap_indicators():
    """创建技术指标热点图"""
    # 模拟数据，实际应用中这里应该替换为真实数据
    indicators = {
        'RSI': 65.8,
        'MACD': 0.000432,
        'MACD_Signal': 0.000129,
        'Price/MA50': 1.015,
        'Price/MA200': 1.052,
        'MA50/MA200': 1.036,
        'MA50/MA200_prev': 1.032
    }
    
    # 设置指标和分类
    indicators_df = pd.DataFrame([
        {'指标': 'RSI', '数值': indicators['RSI'], '类别': 'Overbought' if indicators['RSI'] > 70 else 'Oversold' if indicators['RSI'] < 30 else 'Neutral'},
        {'指标': 'MACD', '数值': indicators['MACD'], '类别': 'Bullish' if indicators['MACD'] > indicators['MACD_Signal'] else 'Bearish'},
        {'指标': 'Price/50-Day MA', '数值': indicators['Price/MA50'], '类别': 'Bullish' if indicators['Price/MA50'] > 1 else 'Bearish'},
        {'指标': 'Price/200-Day MA', '数值': indicators['Price/MA200'], '类别': 'Bullish' if indicators['Price/MA200'] > 1 else 'Bearish'},
        {'指标': '50/200 MA Relation', '数值': indicators['MA50/MA200'], '类别': 'Bullish' if indicators['MA50/MA200'] > 1 else 'Bearish'}
    ])
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # 创建热力图的颜色表示
    colors = []
    for cat in indicators_df['类别']:
        if cat in ['Bullish', 'Golden Cross', 'Oversold']:
            colors.append('green')
        elif cat in ['Bearish', 'Death Cross', 'Overbought']:
            colors.append('red')
        else:
            colors.append('orange')
    
    # 绘制带有文本的条形图
    y_pos = range(len(indicators_df['指标']))
    bars = ax.barh(y_pos, [1]*len(y_pos), color=colors, alpha=0.3)
    
    # 添加指标名称和数值
    for i, (index, row) in enumerate(indicators_df.iterrows()):
        ax.text(0.05, i, f"{row['指标']}: {row['数值']:.4f}", va='center')
        ax.text(0.7, i, row['类别'], va='center', color=colors[i], weight='bold')
    
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlim(0, 1)
    ax.set_title('Technical Indicators Status')
    
    # 去除边框
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    
    # 转换为base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    
    return image_base64

def get_buy_signal_email():
    """返回买入信号邮件HTML内容"""
    
    # 模拟数据
    signal_data = {
        'date': '2023-05-15',
        'price': 4520.35,
        'ma_signal': 1,
        'rsi_signal': 1,
        'macd_signal': 1,
        'bb_signal': 0,
        'price_ma_signal': 1,
        'total_signals': 4
    }
    
    market_status = {
        'date': '2023-05-16',
        'price': 4582.64,
        'ma_short': 4510.21,
        'ma_long': 4350.75,
        'rsi': 65.8,
        'macd': 0.000432,
        'macd_signal': 0.000129,
        'macd_histogram': 0.000303,
        'trend': '上升趋势',
        'strength': '偏强',
        'momentum': '看涨'
    }
    
    # 生成图表
    chart_image = generate_chart_with_annotations('buy')
    indicators_image = create_heatmap_indicators()
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
            .section {{ margin-top: 20px; }}
            .section h2 {{ color: #4CAF50; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            table, th, td {{ border: 1px solid #ddd; }}
            th, td {{ padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .positive {{ color: green; }}
            .negative {{ color: red; }}
            .neutral {{ color: orange; }}
            img {{ max-width: 100%; height: auto; margin-top: 10px; }}
            .chart-container {{ margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>标普500指数买入信号</h1>
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
                    <tr><td>移动平均线</td><td class="positive">金叉</td></tr>
                    <tr><td>RSI</td><td class="positive">超卖反转</td></tr>
                    <tr><td>MACD</td><td class="positive">金叉</td></tr>
                    <tr><td>布林带</td><td class="neutral">无信号</td></tr>
                    <tr><td>价格与均线关系</td><td class="positive">突破均线</td></tr>
                </table>
                
                <h3>指标状态可视化</h3>
                <div class="chart-container">
                    <img src="data:image/png;base64,{indicators_image}" alt="指标状态热力图">
                </div>
            </div>
            
            <div class="section">
                <h2>当前市场状态</h2>
                <table>
                    <tr><th>当前价格</th><td>{market_status['price']:.2f}</td></tr>
                    <tr><th>市场趋势</th><td class="positive">{market_status['trend']}</td></tr>
                    <tr><th>市场强弱</th><td class="positive">{market_status['strength']}</td></tr>
                    <tr><th>市场动能</th><td class="positive">{market_status['momentum']}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <p>以下是技术指标的详细数据：</p>
                <table>
                    <tr><th>指标</th><th>数值</th></tr>
                    <tr><td>50日均线</td><td>{market_status['ma_short']:.2f}</td></tr>
                    <tr><td>200日均线</td><td>{market_status['ma_long']:.2f}</td></tr>
                    <tr><td>RSI</td><td>{market_status['rsi']:.2f}</td></tr>
                    <tr><td>MACD</td><td>{market_status['macd']:.6f}</td></tr>
                    <tr><td>MACD信号线</td><td>{market_status['macd_signal']:.6f}</td></tr>
                    <tr><td>MACD柱状图</td><td class="positive">{market_status['macd_histogram']:.6f}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>技术分析图表</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart_image}" alt="技术分析图表">
                </div>
            </div>
            
            <div class="section">
                <p>此邮件由标普500技术指标监控系统自动发送。</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def get_sell_signal_email():
    """返回卖出信号邮件HTML内容"""
    
    # 模拟数据
    signal_data = {
        'date': '2023-05-13',
        'price': 4620.18,
        'ma_signal': -1,
        'rsi_signal': -1,
        'macd_signal': -1,
        'bb_signal': -1,
        'price_ma_signal': 0,
        'total_signals': 4
    }
    
    market_status = {
        'date': '2023-05-16',
        'price': 4582.64,
        'ma_short': 4510.21,
        'ma_long': 4350.75,
        'rsi': 65.8,
        'macd': 0.000432,
        'macd_signal': 0.000129,
        'macd_histogram': 0.000303,
        'trend': '上升趋势',
        'strength': '偏强',
        'momentum': '看涨'
    }
    
    # 生成图表
    chart_image = generate_chart_with_annotations('sell')
    indicators_image = create_heatmap_indicators()
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #F44336; color: white; padding: 10px; text-align: center; }}
            .section {{ margin-top: 20px; }}
            .section h2 {{ color: #F44336; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            table, th, td {{ border: 1px solid #ddd; }}
            th, td {{ padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .positive {{ color: green; }}
            .negative {{ color: red; }}
            .neutral {{ color: orange; }}
            img {{ max-width: 100%; height: auto; margin-top: 10px; }}
            .chart-container {{ margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>标普500指数卖出信号</h1>
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
                    <tr><td>移动平均线</td><td class="negative">死叉</td></tr>
                    <tr><td>RSI</td><td class="negative">超买反转</td></tr>
                    <tr><td>MACD</td><td class="negative">死叉</td></tr>
                    <tr><td>布林带</td><td class="negative">触及上轨</td></tr>
                    <tr><td>价格与均线关系</td><td class="neutral">无信号</td></tr>
                </table>
                
                <h3>指标状态可视化</h3>
                <div class="chart-container">
                    <img src="data:image/png;base64,{indicators_image}" alt="指标状态热力图">
                </div>
            </div>
            
            <div class="section">
                <h2>当前市场状态</h2>
                <table>
                    <tr><th>当前价格</th><td>{market_status['price']:.2f}</td></tr>
                    <tr><th>市场趋势</th><td class="positive">{market_status['trend']}</td></tr>
                    <tr><th>市场强弱</th><td class="positive">{market_status['strength']}</td></tr>
                    <tr><th>市场动能</th><td class="positive">{market_status['momentum']}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <p>以下是技术指标的详细数据：</p>
                <table>
                    <tr><th>指标</th><th>数值</th></tr>
                    <tr><td>50日均线</td><td>{market_status['ma_short']:.2f}</td></tr>
                    <tr><td>200日均线</td><td>{market_status['ma_long']:.2f}</td></tr>
                    <tr><td>RSI</td><td>{market_status['rsi']:.2f}</td></tr>
                    <tr><td>MACD</td><td>{market_status['macd']:.6f}</td></tr>
                    <tr><td>MACD信号线</td><td>{market_status['macd_signal']:.6f}</td></tr>
                    <tr><td>MACD柱状图</td><td class="positive">{market_status['macd_histogram']:.6f}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>技术分析图表</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart_image}" alt="技术分析图表">
                </div>
            </div>
            
            <div class="section">
                <p>此邮件由标普500技术指标监控系统自动发送。</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def get_daily_summary_email():
    """返回每日摘要邮件HTML内容"""
    
    # 模拟数据
    market_status = {
        'date': '2023-05-16',
        'price': 4582.64,
        'ma_short': 4510.21,
        'ma_long': 4350.75,
        'rsi': 65.8,
        'macd': 0.000432,
        'macd_signal': 0.000129,
        'macd_histogram': 0.000303,
        'trend': '上升趋势',
        'strength': '偏强',
        'momentum': '看涨'
    }
    
    recent_signals = {
        'buy': {
            'date': '2023-05-15',
            'price': 4520.35,
            'num_indicators': 4
        },
        'sell': {
            'date': '2023-05-13',
            'price': 4620.18,
            'num_indicators': 4
        }
    }
    
    # 生成图表
    chart_image = generate_chart_with_annotations('buy')  # 日度报告默认用买入类型图表，也可修改为中性
    indicators_image = create_heatmap_indicators()
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2196F3; color: white; padding: 10px; text-align: center; }}
            .section {{ margin-top: 20px; }}
            .section h2 {{ color: #2196F3; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            table, th, td {{ border: 1px solid #ddd; }}
            th, td {{ padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .positive {{ color: green; }}
            .negative {{ color: red; }}
            .neutral {{ color: orange; }}
            .signal-box {{ padding: 10px; border-radius: 5px; margin-top: 10px; }}
            .buy-signal {{ background-color: rgba(76, 175, 80, 0.1); border: 1px solid #4CAF50; }}
            .sell-signal {{ background-color: rgba(244, 67, 54, 0.1); border: 1px solid #F44336; }}
            img {{ max-width: 100%; height: auto; margin-top: 10px; }}
            .chart-container {{ margin-top: 15px; }}
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
                    <tr><th>市场趋势</th><td class="positive">{market_status['trend']}</td></tr>
                    <tr><th>市场强弱</th><td class="positive">{market_status['strength']}</td></tr>
                    <tr><th>市场动能</th><td class="positive">{market_status['momentum']}</td></tr>
                </table>
                
                <h3>指标状态可视化</h3>
                <div class="chart-container">
                    <img src="data:image/png;base64,{indicators_image}" alt="指标状态热力图">
                </div>
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
                    <tr><td>MACD柱状图</td><td class="positive">{market_status['macd_histogram']:.6f}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>最近买入信号</h2>
                <div class="signal-box buy-signal">
                    <table>
                        <tr><th>日期</th><td>{recent_signals['buy']['date']}</td></tr>
                        <tr><th>价格</th><td>{recent_signals['buy']['price']:.2f}</td></tr>
                        <tr><th>确认指标数量</th><td>{recent_signals['buy']['num_indicators']}</td></tr>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>最近卖出信号</h2>
                <div class="signal-box sell-signal">
                    <table>
                        <tr><th>日期</th><td>{recent_signals['sell']['date']}</td></tr>
                        <tr><th>价格</th><td>{recent_signals['sell']['price']:.2f}</td></tr>
                        <tr><th>确认指标数量</th><td>{recent_signals['sell']['num_indicators']}</td></tr>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>技术分析图表</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart_image}" alt="技术分析图表">
                </div>
            </div>
            
            <div class="section">
                <p>此邮件由标普500技术指标监控系统自动发送。</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_email_previews():
    """生成并保存邮件预览到HTML文件"""
    # 确保reports目录存在
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # 生成三种邮件的预览
    buy_signal_email = get_buy_signal_email()
    sell_signal_email = get_sell_signal_email()
    daily_summary_email = get_daily_summary_email()
    
    # 保存到文件
    with open(os.path.join(reports_dir, 'buy_signal_email.html'), 'w') as file:
        file.write(buy_signal_email)
    
    with open(os.path.join(reports_dir, 'sell_signal_email.html'), 'w') as file:
        file.write(sell_signal_email)
    
    with open(os.path.join(reports_dir, 'daily_summary_email.html'), 'w') as file:
        file.write(daily_summary_email)
    
    print(f"买入信号邮件预览已保存到: {os.path.join(reports_dir, 'buy_signal_email.html')}")
    print(f"卖出信号邮件预览已保存到: {os.path.join(reports_dir, 'sell_signal_email.html')}")
    print(f"每日摘要邮件预览已保存到: {os.path.join(reports_dir, 'daily_summary_email.html')}")

if __name__ == "__main__":
    generate_email_previews()