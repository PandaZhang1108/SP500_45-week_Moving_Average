#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S&P 500 45-Week Moving Average Strategy Monitoring Script
Automatically detects golden cross and death cross signals, and sends email alerts
"""

import os
import time
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
import requests

# 设置中文字体（MacOS可用"Arial Unicode MS"或"PingFang SC"）
try:
    # 尝试加载中文字体
    chinese_font = FontProperties(family='PingFang SC')
except:
    # 如果失败，使用系统默认字体
    chinese_font = FontProperties()

def get_sp500_data(max_retries=5, retry_delay=5):
    """获取标普500指数数据，添加重试机制"""
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            # 下载近两年的数据（确保有足够的历史数据计算均线）
            print(f"尝试获取标普500数据 (尝试 {retries + 1}/{max_retries})")
            df = yf.download('^GSPC', period='2y')
            
            # 同时获取VIX恐慌指数数据
            print("尝试获取VIX恐慌指数数据")
            vix_df = yf.download('^VIX', period='2y')
            
            # 验证数据是否有效
            if df is None or len(df) == 0:
                raise ValueError("获取的标普500数据为空")
                
            if vix_df is None or len(vix_df) == 0:
                print("警告: VIX数据为空，将继续执行但不包含VIX分析")
            else:
                # 将VIX数据合并到主数据集中
                df['VIX'] = vix_df['Close']
            
            # 添加各种移动平均线和技术指标
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
            
            print(f"成功获取标普500指数数据，共{len(df)}个交易日")
            return df
            
        except Exception as e:
            last_error = e
            print(f"获取数据失败: {str(e)}, 将在{retry_delay}秒后重试...")
            retries += 1
            time.sleep(retry_delay)
    
    # 如果所有重试都失败，尝试直接使用requests获取数据
    try:
        print("使用替代方法获取数据...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=2y&interval=1d"
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # 解析JSON数据
        timestamps = data['chart']['result'][0]['timestamp']
        quotes = data['chart']['result'][0]['indicators']['quote'][0]
        
        # 创建DataFrame
        df = pd.DataFrame({
            'Open': quotes['open'],
            'High': quotes['high'],
            'Low': quotes['low'],
            'Close': quotes['close'],
            'Volume': quotes['volume']
        }, index=pd.to_datetime([datetime.datetime.fromtimestamp(x) for x in timestamps]))
        
        # 添加指标 (与上方相同的指标)
        # 45周均线
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
        
        # 尝试单独获取VIX数据
        try:
            vix_url = f"https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=2y&interval=1d"
            vix_response = requests.get(vix_url, headers=headers)
            vix_data = vix_response.json()
            
            # 解析VIX数据
            vix_timestamps = vix_data['chart']['result'][0]['timestamp']
            vix_quotes = vix_data['chart']['result'][0]['indicators']['quote'][0]
            
            # 创建VIX DataFrame
            vix_df = pd.DataFrame({
                'VIX': vix_quotes['close']
            }, index=pd.to_datetime([datetime.datetime.fromtimestamp(x) for x in vix_timestamps]))
            
            # 将VIX数据合并到主数据集
            df = df.join(vix_df, how='left')
        except Exception as e:
            print(f"获取VIX数据失败: {str(e)}")
        
        print(f"成功使用替代方法获取标普500指数数据，共{len(df)}个交易日")
        return df
        
    except Exception as e:
        print(f"所有尝试都失败，无法获取数据: {str(e)}")
        raise RuntimeError(f"无法获取标普500数据，最后的错误: {str(last_error)}")

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

def check_all_signals(df):
    """检查所有技术指标的信号"""
    # 确保数据不为空
    if df is None or len(df) < 3:
        print("警告: 数据不足，无法检查技术指标信号")
        return {}, df.index[-1] if len(df) > 0 else None
    
    # 当前日期和前一天
    today = df.index[-1]
    yesterday = df.index[-2]
    day_before_yesterday = df.index[-3]
    
    # 初始化信号字典
    signals = {}
    
    # 1. 检查45周均线交叉信号
    if df['Close'][yesterday] < df['45WMA'][yesterday] and df['Close'][today] > df['45WMA'][today]:
        signals['45WMA'] = {'type': 'Golden Cross', 'action': 'Buy', 'strength': 'strong'}
    elif df['Close'][yesterday] > df['45WMA'][yesterday] and df['Close'][today] < df['45WMA'][today]:
        signals['45WMA'] = {'type': 'Death Cross', 'action': 'Sell', 'strength': 'strong'}
    
    # 2. 检查50日均线和200日均线交叉信号
    # 50MA金叉200MA (中期金叉)
    if df['50MA'][yesterday] < df['200MA'][yesterday] and df['50MA'][today] > df['200MA'][today]:
        signals['50_200MA'] = {'type': 'Golden Cross', 'action': 'Buy', 'strength': 'strong', 'desc': '50-day MA crosses above 200-day MA'}
    # 50MA死叉200MA (中期死叉)
    elif df['50MA'][yesterday] > df['200MA'][yesterday] and df['50MA'][today] < df['200MA'][today]:
        signals['50_200MA'] = {'type': 'Death Cross', 'action': 'Sell', 'strength': 'strong', 'desc': '50-day MA crosses below 200-day MA'}
    
    # 3. 价格与50日均线的关系
    if df['Close'][yesterday] < df['50MA'][yesterday] and df['Close'][today] > df['50MA'][today]:
        signals['price_50MA'] = {'type': 'Golden Cross', 'action': 'Buy', 'strength': 'medium', 'desc': 'Price crosses above 50-day MA'}
    elif df['Close'][yesterday] > df['50MA'][yesterday] and df['Close'][today] < df['50MA'][today]:
        signals['price_50MA'] = {'type': 'Death Cross', 'action': 'Sell', 'strength': 'medium', 'desc': 'Price crosses below 50-day MA'}
    
    # 4. 价格与200日均线的关系
    if df['Close'][yesterday] < df['200MA'][yesterday] and df['Close'][today] > df['200MA'][today]:
        signals['price_200MA'] = {'type': 'Golden Cross', 'action': 'Buy', 'strength': 'strong', 'desc': 'Price crosses above 200-day MA'}
    elif df['Close'][yesterday] > df['200MA'][yesterday] and df['Close'][today] < df['200MA'][today]:
        signals['price_200MA'] = {'type': 'Death Cross', 'action': 'Sell', 'strength': 'strong', 'desc': 'Price crosses below 200-day MA'}
    
    # 5. 检查布林带信号
    # 价格突破上轨
    if df['Close'][yesterday] < df['BB_Upper'][yesterday] and df['Close'][today] > df['BB_Upper'][today]:
        signals['bollinger'] = {'type': 'Upper Breakout', 'action': 'Cautious', 'strength': 'weak', 'desc': 'Price breaks Bollinger Upper Band'}
    # 价格跌破下轨
    elif df['Close'][yesterday] > df['BB_Lower'][yesterday] and df['Close'][today] < df['BB_Lower'][today]:
        signals['bollinger'] = {'type': 'Lower Breakdown', 'action': 'Watch', 'strength': 'weak', 'desc': 'Price breaks Bollinger Lower Band'}
    # 价格从下轨反弹
    elif df['Close'][day_before_yesterday] <= df['BB_Lower'][day_before_yesterday] and \
         df['Close'][yesterday] <= df['BB_Lower'][yesterday] and \
         df['Close'][today] > df['BB_Lower'][today]:
        signals['bollinger'] = {'type': 'Lower Bounce', 'action': 'Watch', 'strength': 'medium', 'desc': 'Price bounces from Bollinger Lower Band'}
    
    # 6. 检查RSI信号
    # RSI超卖反弹
    if df['RSI'][yesterday] < 30 and df['RSI'][today] > 30:
        signals['rsi'] = {'type': 'Rebound from Oversold', 'action': 'Consider Long Position', 'strength': 'medium', 'desc': 'RSI rebounds from oversold territory'}
    # RSI超买回落
    elif df['RSI'][yesterday] > 70 and df['RSI'][today] < 70:
        signals['rsi'] = {'type': 'Pullback from Overbought', 'action': 'Consider Short Position', 'strength': 'medium', 'desc': 'RSI falls from overbought territory'}
    # RSI极度超卖
    elif df['RSI'][today] < 20:
        signals['rsi'] = {'type': 'Extremely Oversold', 'action': 'Watch Rebound', 'strength': 'strong', 'desc': 'RSI extremely oversold'}
    # RSI极度超买
    elif df['RSI'][today] > 80:
        signals['rsi'] = {'type': 'Extremely Overbought', 'action': 'Watch Pullback', 'strength': 'strong', 'desc': 'RSI extremely overbought'}
    
    # 7. 检查MACD信号
    # MACD金叉 (MACD线上穿信号线)
    if df['MACD'][yesterday] < df['MACD_Signal'][yesterday] and df['MACD'][today] > df['MACD_Signal'][today]:
        signals['macd'] = {'type': 'Golden Cross', 'action': 'Buy', 'strength': 'medium', 'desc': 'MACD crosses above Signal Line'}
    # MACD死叉 (MACD线下穿信号线)
    elif df['MACD'][yesterday] > df['MACD_Signal'][yesterday] and df['MACD'][today] < df['MACD_Signal'][today]:
        signals['macd'] = {'type': 'Death Cross', 'action': 'Sell', 'strength': 'medium', 'desc': 'MACD crosses below Signal Line'}
    # MACD柱状图由负转正
    elif df['MACD_Hist'][yesterday] < 0 and df['MACD_Hist'][today] > 0:
        signals['macd_hist'] = {'type': 'Histogram Turns Positive', 'action': 'Watch Long', 'strength': 'weak', 'desc': 'MACD Histogram turns positive'}
    # MACD柱状图由正转负
    elif df['MACD_Hist'][yesterday] > 0 and df['MACD_Hist'][today] < 0:
        signals['macd_hist'] = {'type': 'Histogram Turns Negative', 'action': 'Watch Short', 'strength': 'weak', 'desc': 'MACD Histogram turns negative'}
    
    # 8. 检查VIX恐慌指数信号 (如果数据可用)
    if 'VIX' in df.columns and not pd.isna(df['VIX'][today]):
        # VIX超过30 (市场恐慌)
        if df['VIX'][today] > 30:
            signals['vix'] = {'type': 'High Fear', 'action': 'Cautious', 'strength': 'strong', 'desc': f'VIX Fear Index high ({df["VIX"][today]:.2f})'}
        # VIX在20-30之间 (市场担忧)
        elif df['VIX'][today] > 20:
            signals['vix'] = {'type': 'Moderate Fear', 'action': 'Watch', 'strength': 'medium', 'desc': f'VIX Fear Index moderate ({df["VIX"][today]:.2f})'}
        # VIX低于12 (市场过度乐观)
        elif df['VIX'][today] < 12:
            signals['vix'] = {'type': 'Excessive Optimism', 'action': 'Alert', 'strength': 'medium', 'desc': f'VIX Fear Index low ({df["VIX"][today]:.2f})'}
        # VIX快速上升 (超过30%)
        if yesterday in df.index and df['VIX'][yesterday] > 0:
            vix_change = (df['VIX'][today] - df['VIX'][yesterday]) / df['VIX'][yesterday] * 100
            if vix_change > 30:
                signals['vix_surge'] = {'type': 'VIX Surge', 'action': 'Alert', 'strength': 'strong', 
                                         'desc': f'VIX Fear Index surging ({vix_change:.2f}%)'}
    
    return signals, today

def create_chart(df, signal_date=None, is_golden=False, is_death=False, signals=None):
    """创建综合技术分析图表，包含多个指标"""
    # 只绘制最近一年的数据
    plot_data = df.iloc[-252:].copy() if len(df) > 252 else df.copy()
    
    # 创建子图布局：主图(标普500价格和均线)，子图(MACD, RSI, VIX)
    fig = plt.figure(figsize=(14, 10))
    
    # 使用英文字体
    plt.rcParams['font.family'] = 'Arial'
    
    # 价格图
    ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=2)
    
    # 绘制标普500和移动平均线
    ax1.plot(plot_data.index, plot_data['Close'], label='S&P 500 Index', color='blue', linewidth=1.5)
    ax1.plot(plot_data.index, plot_data['45WMA'], label='45-Week MA', color='red', linewidth=1)
    ax1.plot(plot_data.index, plot_data['50MA'], label='50-Day MA', color='orange', linewidth=1)
    ax1.plot(plot_data.index, plot_data['200MA'], label='200-Day MA', color='purple', linewidth=1)
    
    # 绘制布林带
    ax1.plot(plot_data.index, plot_data['BB_Upper'], label='Bollinger Upper', color='gray', linestyle='--', alpha=0.5)
    ax1.plot(plot_data.index, plot_data['BB_Middle'], label='Bollinger Middle', color='gray', linestyle='-', alpha=0.5)
    ax1.plot(plot_data.index, plot_data['BB_Lower'], label='Bollinger Lower', color='gray', linestyle='--', alpha=0.5)
    
    # 设置标题和标签
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    ax1.set_title(f'S&P 500 Technical Analysis (as of {current_date})', fontsize=15)
    ax1.set_ylabel('Price')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left', fontsize=8)
    
    # 标记45周均线的金叉或死叉信号
    if signal_date is not None and signal_date in plot_data.index:
        if is_golden:
            ax1.scatter(signal_date, plot_data.loc[signal_date, 'Close'], 
                      s=100, color='gold', zorder=5, marker='^')
            ax1.annotate('45W Golden Cross', (signal_date, plot_data.loc[signal_date, 'Close']),
                       xytext=(10, 30), textcoords='offset points',
                       color='green',
                       arrowprops=dict(arrowstyle='->', color='green'))
        elif is_death:
            ax1.scatter(signal_date, plot_data.loc[signal_date, 'Close'], 
                      s=100, color='black', zorder=5, marker='v')
            ax1.annotate('45W Death Cross', (signal_date, plot_data.loc[signal_date, 'Close']),
                       xytext=(10, -30), textcoords='offset points',
                       color='red',
                       arrowprops=dict(arrowstyle='->', color='red'))
    
    # 如果有其他信号，也标记在图上
    if signals and signal_date in plot_data.index:
        offset = 0
        for sig_key, sig_details in signals.items():
            if sig_key in ['45WMA', 'price_50MA', 'price_200MA', '50_200MA', 'bollinger']:
                sig_type = sig_details.get('type', '')
                sig_desc = sig_details.get('desc', '')
                
                # 信号类型中英文对照
                sig_type_en = {
                    'Golden Cross': 'Golden Cross',
                    'Death Cross': 'Death Cross',
                    'Upper Breakout': 'Upper Breakout',
                    'Lower Breakdown': 'Lower Breakdown',
                    'Lower Bounce': 'Lower Bounce'
                }.get(sig_type, sig_type)
                
                # 信号描述中英文对照
                if '50-day MA crosses above 200-day MA' in sig_desc:
                    sig_desc_en = '50-day MA crosses above 200-day MA'
                elif '50-day MA crosses below 200-day MA' in sig_desc:
                    sig_desc_en = '50-day MA crosses below 200-day MA'
                elif 'Price crosses above 50-day MA' in sig_desc:
                    sig_desc_en = 'Price crosses above 50-day MA'
                elif 'Price crosses below 50-day MA' in sig_desc:
                    sig_desc_en = 'Price crosses below 50-day MA'
                elif 'Price crosses above 200-day MA' in sig_desc:
                    sig_desc_en = 'Price crosses above 200-day MA'
                elif 'Price crosses below 200-day MA' in sig_desc:
                    sig_desc_en = 'Price crosses below 200-day MA'
                elif 'Price breaks Bollinger Upper Band' in sig_desc:
                    sig_desc_en = 'Price breaks Bollinger Upper Band'
                elif 'Price breaks Bollinger Lower Band' in sig_desc:
                    sig_desc_en = 'Price breaks Bollinger Lower Band'
                elif 'Price bounces from Bollinger Lower Band' in sig_desc:
                    sig_desc_en = 'Price bounces from Bollinger Lower Band'
                else:
                    sig_desc_en = sig_desc
                
                # 根据信号类型选择颜色和标记
                if 'Golden Cross' in sig_type or 'Crosses above' in sig_type or 'Bounces from' in sig_type:
                    color = 'green'
                    marker = '^'
                    text_offset = (10, 30 + offset)
                elif 'Death Cross' in sig_type or 'Crosses below' in sig_type or 'Breaks' in sig_type:
                    color = 'red'
                    marker = 'v'
                    text_offset = (10, -30 - offset)
                else:
                    color = 'blue'
                    marker = 'o'
                    text_offset = (10, 30 + offset)
                
                ax1.scatter(signal_date, plot_data.loc[signal_date, 'Close'], 
                          s=80, color=color, zorder=5, marker=marker)
                ax1.annotate(f'{sig_desc_en}', (signal_date, plot_data.loc[signal_date, 'Close']),
                           xytext=text_offset, textcoords='offset points',
                           color=color, fontsize=8,
                           arrowprops=dict(arrowstyle='->', color=color))
                offset += 20
    
    # MACD子图
    ax2 = plt.subplot2grid((4, 1), (2, 0), rowspan=1, sharex=ax1)
    ax2.plot(plot_data.index, plot_data['MACD'], label='MACD', color='blue', linewidth=1.2)
    ax2.plot(plot_data.index, plot_data['MACD_Signal'], label='Signal Line', color='red', linewidth=1)
    ax2.bar(plot_data.index, plot_data['MACD_Hist'], label='Histogram', color=plot_data['MACD_Hist'].apply(
        lambda x: 'green' if x > 0 else 'red'), width=0.5, alpha=0.5)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.set_ylabel('MACD')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', fontsize=8)
    
    # 标记MACD信号
    if signals and signal_date in plot_data.index:
        for sig_key, sig_details in signals.items():
            if sig_key in ['macd', 'macd_hist']:
                sig_type = sig_details.get('type', '')
                sig_desc = sig_details.get('desc', '')
                
                # 信号描述中英文对照
                if 'MACD crosses above Signal Line' in sig_desc:
                    sig_desc_en = 'MACD crosses above Signal Line'
                elif 'MACD crosses below Signal Line' in sig_desc:
                    sig_desc_en = 'MACD crosses below Signal Line'
                elif 'MACD Histogram turns positive' in sig_desc:
                    sig_desc_en = 'MACD Histogram turns positive'
                elif 'MACD Histogram turns negative' in sig_desc:
                    sig_desc_en = 'MACD Histogram turns negative'
                else:
                    sig_desc_en = sig_desc
                
                if sig_key == 'macd':
                    y_value = plot_data.loc[signal_date, 'MACD']
                else:
                    y_value = plot_data.loc[signal_date, 'MACD_Hist']
                
                # 根据信号类型选择颜色
                color = 'green' if 'Golden Cross' in sig_type or 'Crosses above' in sig_type else 'red'
                
                ax2.scatter(signal_date, y_value, s=80, color=color, zorder=5)
                ax2.annotate(f'{sig_desc_en}', (signal_date, y_value),
                           xytext=(10, 10), textcoords='offset points',
                           color=color, fontsize=8,
                           arrowprops=dict(arrowstyle='->', color=color))
    
    # RSI和VIX子图
    ax3 = plt.subplot2grid((4, 1), (3, 0), rowspan=1, sharex=ax1)
    
    # 绘制RSI
    color_rsi = 'tab:blue'
    ax3.set_ylabel('RSI', color=color_rsi)
    ax3.plot(plot_data.index, plot_data['RSI'], label='RSI(14)', color=color_rsi)
    ax3.axhline(y=70, color=color_rsi, linestyle='--', alpha=0.3)  # 超买线
    ax3.axhline(y=30, color=color_rsi, linestyle='--', alpha=0.3)  # 超卖线
    ax3.tick_params(axis='y', labelcolor=color_rsi)
    ax3.text(plot_data.index[0], 70, 'Overbought', color=color_rsi, fontsize=8)
    ax3.text(plot_data.index[0], 30, 'Oversold', color=color_rsi, fontsize=8)
    
    # 标记RSI信号
    if signals and signal_date in plot_data.index:
        for sig_key, sig_details in signals.items():
            if sig_key == 'rsi':
                sig_desc = sig_details.get('desc', '')
                y_value = plot_data.loc[signal_date, 'RSI']
                
                # 信号描述中英文对照
                if 'Rebound from Oversold' in sig_desc:
                    sig_desc_en = 'Rebound from oversold territory'
                elif 'Pullback from Overbought' in sig_desc:
                    sig_desc_en = 'Pullback from overbought territory'
                elif 'Extremely Oversold' in sig_desc:
                    sig_desc_en = 'Extremely oversold'
                elif 'Extremely Overbought' in sig_desc:
                    sig_desc_en = 'Extremely overbought'
                else:
                    sig_desc_en = sig_desc
                
                # 根据信号描述选择颜色
                color = 'green' if 'Rebound from' in sig_desc else 'red'
                
                ax3.scatter(signal_date, y_value, s=80, color=color, zorder=5)
                ax3.annotate(f'{sig_desc_en}', (signal_date, y_value),
                           xytext=(10, 10), textcoords='offset points',
                           color=color, fontsize=8,
                           arrowprops=dict(arrowstyle='->', color=color))
    
    # 如果有VIX数据，在RSI子图上添加第二个Y轴显示VIX
    if 'VIX' in plot_data.columns and not plot_data['VIX'].isnull().all():
        ax3_twin = ax3.twinx()
        color_vix = 'tab:orange'
        ax3_twin.set_ylabel('VIX', color=color_vix)
        ax3_twin.plot(plot_data.index, plot_data['VIX'], label='VIX Fear Index', color=color_vix)
        ax3_twin.axhline(y=30, color=color_vix, linestyle='--', alpha=0.3)  # 恐慌线
        ax3_twin.axhline(y=20, color=color_vix, linestyle='--', alpha=0.3)  # 警戒线
        ax3_twin.tick_params(axis='y', labelcolor=color_vix)
        
        # 标记VIX信号
        if signals and signal_date in plot_data.index:
            for sig_key, sig_details in signals.items():
                if 'vix' in sig_key:
                    sig_desc = sig_details.get('desc', '')
                    y_value = plot_data.loc[signal_date, 'VIX']
                    
                    # VIX信号描述中英文对照
                    if 'High Fear' in sig_desc:
                        sig_desc_en = f'VIX high ({plot_data.loc[signal_date, "VIX"]:.2f})'
                    elif 'Moderate Fear' in sig_desc:
                        sig_desc_en = f'VIX moderate ({plot_data.loc[signal_date, "VIX"]:.2f})'
                    elif 'Excessive Optimism' in sig_desc:
                        sig_desc_en = f'VIX low ({plot_data.loc[signal_date, "VIX"]:.2f})'
                    elif 'VIX surging' in sig_desc:
                        pct_change = (plot_data.loc[signal_date, 'VIX'] - plot_data.loc[signal_date - pd.Timedelta(days=1), 'VIX']) / plot_data.loc[signal_date - pd.Timedelta(days=1), 'VIX'] * 100
                        sig_desc_en = f'VIX surging ({pct_change:.2f}%)'
                    else:
                        sig_desc_en = sig_desc
                    
                    # 为VIX信号选择颜色
                    color = 'red' if 'High' in sig_desc or 'Surge' in sig_desc else 'blue'
                    
                    ax3_twin.scatter(signal_date, y_value, s=80, color=color, zorder=5)
                    ax3_twin.annotate(f'{sig_desc_en}', (signal_date, y_value),
                                  xytext=(10, -20), textcoords='offset points',
                                  color=color, fontsize=8,
                                  arrowprops=dict(arrowstyle='->', color=color))
        
        # 添加VIX的图例
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)
    else:
        ax3.legend(loc='upper left', fontsize=8)
    
    ax3.grid(True, alpha=0.3)
    ax3.set_xlabel('Date')
    
    # 设置x轴日期格式
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    
    plt.tight_layout()
    fig.autofmt_xdate()  # 自动格式化x轴日期标签
    
    # 保存图表
    chart_path = 'sp500_45wma_chart.png'
    plt.savefig(chart_path, dpi=100)
    plt.close()
    
    return chart_path

def compose_signal_analysis(df, signals):
    """生成技术指标分析文本"""
    if not signals:
        return "No significant signals detected at the moment."
    
    # 获取最新数据
    latest = df.iloc[-1]
    
    analysis_text = "Technical Indicators Analysis:\n\n"
    
    # 添加当前市场状态摘要
    analysis_text += "【Market Status Summary】\n"
    analysis_text += f"S&P 500 Current Price: {latest['Close']:.2f}\n"
    
    # 移动均线状态
    ma_status = []
    if latest['Close'] > latest['45WMA']:
        ma_status.append("Price above 45-week MA")
    else:
        ma_status.append("Price below 45-week MA")
    
    if latest['Close'] > latest['50MA']:
        ma_status.append("Price above 50-day MA")
    else:
        ma_status.append("Price below 50-day MA")
        
    if latest['Close'] > latest['200MA']:
        ma_status.append("Price above 200-day MA")
    else:
        ma_status.append("Price below 200-day MA")
        
    if latest['50MA'] > latest['200MA']:
        ma_status.append("50-day MA above 200-day MA")
    else:
        ma_status.append("50-day MA below 200-day MA")
    
    analysis_text += "Moving Averages: " + ", ".join(ma_status) + "\n"
    
    # 其他指标状态
    analysis_text += f"RSI Value: {latest['RSI']:.2f} "
    if latest['RSI'] > 70:
        analysis_text += "(Overbought)\n"
    elif latest['RSI'] < 30:
        analysis_text += "(Oversold)\n"
    else:
        analysis_text += "(Neutral)\n"
    
    analysis_text += f"MACD Value: {latest['MACD']:.4f}, Signal Line: {latest['MACD_Signal']:.4f}, Histogram: {latest['MACD_Hist']:.4f}\n"
    
    if 'VIX' in latest and not pd.isna(latest['VIX']):
        analysis_text += f"VIX Fear Index: {latest['VIX']:.2f} "
        if latest['VIX'] > 30:
            analysis_text += "(High Market Fear)\n"
        elif latest['VIX'] > 20:
            analysis_text += "(Market Concern)\n"
        elif latest['VIX'] < 12:
            analysis_text += "(Excessive Optimism)\n"
        else:
            analysis_text += "(Normal Volatility Range)\n"
    
    # 添加检测到的信号
    analysis_text += "\n【Detected Signals】\n"
    
    # 按强度对信号进行排序
    strength_order = {'strong': 1, 'medium': 2, 'weak': 3}
    sorted_signals = sorted(
        signals.items(), 
        key=lambda x: (strength_order.get(x[1].get('strength', 'weak'), 4), x[0])
    )
    
    for sig_key, sig_details in sorted_signals:
        sig_type = sig_details.get('type', '')
        sig_desc = sig_details.get('desc', '')
        sig_action = sig_details.get('action', '')
        sig_strength = sig_details.get('strength', '')
        
        # 信号类型英文对照
        sig_type_en = {
            'Golden Cross': 'Golden Cross',
            'Death Cross': 'Death Cross',
            'Overbought': 'Overbought',
            'Oversold': 'Oversold',
            'Upper Breakout': 'Upper Band Breakout',
            'Lower Breakdown': 'Lower Band Breakdown',
            'Lower Bounce': 'Bounce from Lower Band',
            'Rebound from Oversold': 'Rebound from Oversold',
            'Pullback from Overbought': 'Pullback from Overbought',
            'Bearish Divergence': 'Bearish Divergence',
            'Bullish Divergence': 'Bullish Divergence',
            'Moderate Fear': 'Moderate Fear',
            'High Fear': 'High Fear',
            'Excessive Optimism': 'Excessive Optimism'
        }.get(sig_type, sig_type)
        
        # 信号描述英文对照
        if '50-day MA crosses above 200-day MA' in sig_desc:
            sig_desc_en = '50-day MA crosses above 200-day MA'
        elif '50-day MA crosses below 200-day MA' in sig_desc:
            sig_desc_en = '50-day MA crosses below 200-day MA'
        elif 'Price crosses above 50-day MA' in sig_desc:
            sig_desc_en = 'Price crosses above 50-day MA'
        elif 'Price crosses below 50-day MA' in sig_desc:
            sig_desc_en = 'Price crosses below 50-day MA'
        elif 'Price crosses above 200-day MA' in sig_desc:
            sig_desc_en = 'Price crosses above 200-day MA'
        elif 'Price crosses below 200-day MA' in sig_desc:
            sig_desc_en = 'Price crosses below 200-day MA'
        elif 'RSI rebounds from oversold territory' in sig_desc:
            sig_desc_en = 'RSI rebounds from oversold territory'
        elif 'RSI pullback from overbought territory' in sig_desc:
            sig_desc_en = 'RSI pullback from overbought territory'
        elif 'MACD crosses above Signal Line' in sig_desc:
            sig_desc_en = 'MACD crosses above Signal Line'
        elif 'MACD crosses below Signal Line' in sig_desc:
            sig_desc_en = 'MACD crosses below Signal Line'
        elif 'MACD Histogram turns positive' in sig_desc:
            sig_desc_en = 'MACD Histogram turns positive'
        elif 'MACD Histogram turns negative' in sig_desc:
            sig_desc_en = 'MACD Histogram turns negative'
        elif 'VIX high' in sig_desc:
            sig_desc_en = f'VIX high ({latest["VIX"]:.2f})'
        elif 'VIX moderate' in sig_desc:
            sig_desc_en = f'VIX moderate ({latest["VIX"]:.2f})'
        elif 'VIX low' in sig_desc:
            sig_desc_en = f'VIX low ({latest["VIX"]:.2f})'
        elif not sig_desc:
            sig_desc_en = sig_type_en
        else:
            sig_desc_en = sig_desc
        
        # 信号操作建议英文对照
        sig_action_en = {
            'Buy': 'Buy',
            'Sell': 'Sell',
            'Hold': 'Hold',
            'Watch': 'Watch',
            'Consider Long Position': 'Consider Long Position',
            'Consider Short Position': 'Consider Short Position',
            'Reduce Position': 'Reduce Position',
            'Increase Position': 'Increase Position'
        }.get(sig_action, sig_action)
        
        strength_text = {
            'strong': 'Strong Signal',
            'medium': 'Medium Signal',
            'weak': 'Weak Signal'
        }.get(sig_strength, '')
        
        analysis_text += f"- {sig_desc_en} [{strength_text}]\n"
        analysis_text += f"  Recommendation: {sig_action_en}\n"
    
    # 添加指标说明
    analysis_text += "\n【Indicator Explanations】\n"
    analysis_text += "• 45-Week Moving Average: Used for long-term trend identification. Golden cross indicates entering an uptrend, death cross indicates entering a downtrend\n"
    analysis_text += "• 50/200-Day MA: Golden cross (50 above 200) is a bullish signal, death cross (50 below 200) is a bearish signal\n"
    analysis_text += "• RSI(14): Oscillator between 0-100, below 30 is oversold, above 70 is overbought\n"
    analysis_text += "• MACD(12,26,9): Trend indicator, MACD crossing above signal line forms golden cross, crossing below forms death cross\n"
    analysis_text += "• Bollinger Bands: Volatility indicator based on standard deviation, price hitting upper band may indicate overbought, hitting lower band may indicate oversold\n"
    analysis_text += "• VIX Fear Index: Market volatility expectation indicator, above 30 indicates market panic, below 12 indicates excessive optimism\n"
    
    # 添加免责声明
    analysis_text += "\n【Disclaimer】\n"
    analysis_text += "This analysis is for reference only and does not constitute investment advice. Investment decisions should be made considering personal risk tolerance and market research.\n"
    
    return analysis_text

def send_email_alert(subject, body, chart_path=None):
    """发送邮件提醒"""
    # 从环境变量获取邮箱设置
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASS')
    receiver_email = os.environ.get('EMAIL_USER')  # 发给自己
    
    if not sender_email or not sender_password:
        print("Error: Email environment variables EMAIL_USER or EMAIL_PASS not set")
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
                <h2>S&P 500 Technical Analysis Report</h2>
                <p><pre style="font-family: Arial, sans-serif; font-size: 14px;">{body}</pre></p>
                <p><img src="cid:chart" style="width:100%;max-width:1000px"></p>
                <p style="color:#666; font-size:12px;">* This email was sent by an automated monitoring system. Please do not reply directly. *</p>
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
                print(f"Email login failed: {str(e)}")
                return False
        
        # 发送邮件
        server.send_message(msg)
        server.quit()
        print(f"Successfully sent email to {receiver_email} (using {'Gmail' if is_gmail else 'QQ Mail'})")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def main():
    """主函数"""
    print(f"Starting S&P 500 technical analysis monitoring... {datetime.datetime.now()}")
    
    # 获取数据
    try:
        data = get_sp500_data()
        if data is None or len(data) == 0:
            # 发送错误报告邮件
            error_subject = f"S&P 500 Monitoring System Error - {datetime.datetime.now().strftime('%Y-%m-%d')}"
            error_body = "Data retrieval failed, returned data is empty. The system will try again on the next scheduled run."
            send_email_alert(error_subject, error_body)
            print("Data is empty, sent error report email")
            return
    except Exception as e:
        # 发送错误报告邮件
        error_subject = f"S&P 500 Monitoring System Error - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        error_body = f"Error occurred while retrieving data: {str(e)}\nThe system will try again on the next scheduled run."
        send_email_alert(error_subject, error_body)
        print(f"Failed to retrieve data, sent error report email: {str(e)}")
        return
    
    # 检查传统的45周均线金叉死叉信号（向下兼容）
    golden_cross, death_cross, simple_signal_date = check_cross_signals(data)
    
    # 检查所有技术指标信号
    all_signals, signal_date = check_all_signals(data)
    
    # 如果没有任何信号，检查是否应该发送周报
    if not all_signals and not golden_cross and not death_cross:
        # 检查是否是每周一（工作日=0）可以发送周报
        if datetime.datetime.now().weekday() == 0:
            # 创建图表
            chart_path = create_chart(data)
            
            # 准备周报内容
            latest_price = data['Close'].iloc[-1]
            latest_ma45 = data['45WMA'].iloc[-1]
            latest_ma50 = data['50MA'].iloc[-1]
            latest_ma200 = data['200MA'].iloc[-1]
            latest_rsi = data['RSI'].iloc[-1]
            
            # 生成周报分析内容
            subject = f"S&P 500 Weekly Report - {datetime.datetime.now().strftime('%Y-%m-%d')}"
            body = f"""S&P 500 Weekly Technical Analysis:

Current Price: {latest_price:.2f}
45-Week MA: {latest_ma45:.2f}
50-Day MA: {latest_ma50:.2f}
200-Day MA: {latest_ma200:.2f}
RSI(14): {latest_rsi:.2f}

{compose_signal_analysis(data, {})}
"""
            
            # 发送周报邮件
            send_email_alert(subject, body, chart_path)
        else:
            print("No crossing signals today and it's not Monday, no report will be sent")
        
        return
    
    # 如果有信号，创建带有标记的图表
    chart_path = create_chart(data, signal_date, golden_cross, death_cross, all_signals)
    
    # 构建邮件主题 - 使用最重要的信号
    important_signals = [sig for sig_key, sig in all_signals.items() 
                        if sig.get('strength') == 'strong']
    
    if important_signals:
        # 有强信号
        subject_signal = "Multiple Strong Signals"
        if golden_cross or death_cross:
            subject_signal = "45-Week MA " + ("Golden Cross" if golden_cross else "Death Cross")
        elif '50_200MA' in all_signals:
            subject_signal = "50/200-Day MA " + all_signals['50_200MA']['type']
        elif 'vix' in all_signals and all_signals['vix']['strength'] == 'strong':
            subject_signal = "VIX Fear Index Abnormal"
    else:
        # 只有中等或弱信号
        subject_signal = "Technical Indicators Change"
        if golden_cross or death_cross:
            subject_signal = "45-Week MA " + ("Golden Cross" if golden_cross else "Death Cross")
    
    subject = f"S&P 500 Alert - {subject_signal} - {signal_date.strftime('%Y-%m-%d')}"
    
    # 生成邮件正文
    body = f"""S&P 500 Technical Analysis Alert:

Date: {signal_date.strftime('%Y-%m-%d')}
Current Price: {data['Close'].iloc[-1]:.2f}

{compose_signal_analysis(data, all_signals)}
"""
    
    # 发送提醒邮件
    send_email_alert(subject, body, chart_path)
    print(f"Signal alert email sent: {subject}")

if __name__ == "__main__":
    main()