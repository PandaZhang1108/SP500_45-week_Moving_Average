import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging
from datetime import datetime

class MarketAnalyzer:
    """市场分析和可视化类"""
    
    def __init__(self, config):
        """
        初始化MarketAnalyzer
        
        Args:
            config: 配置信息
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def analyze_market_status(self, data, signals):
        """
        分析当前市场状态
        
        Args:
            data: 带有技术指标的数据
            signals: 买入卖出信号数据
            
        Returns:
            dict: 市场状态分析结果
        """
        if data is None or data.empty:
            self.logger.error("没有可用于分析的数据")
            return None
        
        # 获取最新数据
        latest = data.iloc[-1]
        latest_date = latest.name
        
        # 获取指标参数
        ma_short = self.config['indicators']['ma']['short']
        ma_long = self.config['indicators']['ma']['long']
        rsi_period = self.config['indicators']['rsi']['period_short']
        
        # 当前的技术指标值
        current_price = latest['Close']
        ma_short_value = latest[f'MA{ma_short}']
        ma_long_value = latest[f'MA{ma_long}']
        rsi_value = latest[f'RSI{rsi_period}']
        macd_value = latest['MACD']
        macd_signal_value = latest['MACD_Signal']
        macd_histogram = latest['MACD_Histogram']
        
        # 判断市场趋势
        if current_price > ma_long_value:
            trend = "上升趋势"
        else:
            trend = "下降趋势"
        
        # 判断市场强弱
        rsi_overbought = self.config['indicators']['rsi']['overbought']
        rsi_oversold = self.config['indicators']['rsi']['oversold']
        
        if rsi_value > rsi_overbought:
            strength = "超买"
        elif rsi_value < rsi_oversold:
            strength = "超卖"
        elif rsi_value > 50:
            strength = "偏强"
        else:
            strength = "偏弱"
        
        # 判断市场动能
        if macd_value > macd_signal_value:
            momentum = "看涨"
        else:
            momentum = "看跌"
        
        # 综合分析
        status = {
            'date': latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else str(latest_date),
            'price': current_price,
            'ma_short': ma_short_value,
            'ma_long': ma_long_value,
            'rsi': rsi_value,
            'macd': macd_value,
            'macd_signal': macd_signal_value,
            'macd_histogram': macd_histogram,
            'trend': trend,
            'strength': strength,
            'momentum': momentum
        }
        
        self.logger.info(f"市场分析完成: 趋势={trend}, 强弱={strength}, 动能={momentum}")
        
        return status
    
    def create_summary_report(self, market_status, latest_signals):
        """
        创建摘要报告
        
        Args:
            market_status: 市场状态分析结果
            latest_signals: 最近的信号
            
        Returns:
            dict: 报告数据
        """
        if market_status is None:
            self.logger.error("没有可用于创建报告的市场状态数据")
            return None
        
        # 创建报告数据
        report = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_status': market_status,
            'latest_signals': latest_signals
        }
        
        # 保存报告到JSON文件
        report_path = os.path.join(self.reports_dir, 'latest_report.json')
        pd.Series(report).to_json(report_path)
        
        # 保存信号到CSV文件
        if latest_signals['latest_buy'] is not None:
            latest_buy = pd.Series(latest_signals['latest_buy'])
            latest_buy.to_csv(os.path.join(self.reports_dir, 'latest_buy_signal.csv'))
        
        if latest_signals['latest_sell'] is not None:
            latest_sell = pd.Series(latest_signals['latest_sell'])
            latest_sell.to_csv(os.path.join(self.reports_dir, 'latest_sell_signal.csv'))
        
        self.logger.info(f"摘要报告已保存到: {report_path}")
        
        return report
    
    def plot_indicators(self, data, signals, days=120):
        """
        绘制技术指标图表
        
        Args:
            data: 带有技术指标的数据
            signals: 买入卖出信号数据
            days: 显示的天数
            
        Returns:
            str: 保存的图表文件路径
        """
        if data is None or data.empty:
            self.logger.error("没有可用于绘图的数据")
            return None
        
        # 获取参数
        ma_short = self.config['indicators']['ma']['short']
        ma_long = self.config['indicators']['ma']['long']
        
        # 获取最近的数据
        recent_data = data.tail(days)
        recent_signals = signals.tail(days) if signals is not None else None
        
        # 创建图表
        plt.style.use('ggplot')
        fig, axs = plt.subplots(3, 1, figsize=(12, 16), gridspec_kw={'height_ratios': [2, 1, 1]})
        fig.suptitle('标普500指数技术分析', fontsize=16)
        
        # 1. 价格和移动平均线图
        axs[0].plot(recent_data.index, recent_data['Close'], label='价格', color='black', linewidth=1.5)
        axs[0].plot(recent_data.index, recent_data[f'MA{ma_short}'], label=f'{ma_short}日均线', color='blue', linewidth=1)
        axs[0].plot(recent_data.index, recent_data[f'MA{ma_long}'], label=f'{ma_long}日均线', color='red', linewidth=1)
        axs[0].plot(recent_data.index, recent_data['BB_Upper'], label='布林上轨', color='gray', linestyle='--', linewidth=0.8)
        axs[0].plot(recent_data.index, recent_data['BB_Middle'], label='布林中轨', color='gray', linestyle='-', linewidth=0.8)
        axs[0].plot(recent_data.index, recent_data['BB_Lower'], label='布林下轨', color='gray', linestyle='--', linewidth=0.8)
        
        # 标记买入卖出信号
        if recent_signals is not None:
            buy_signals = recent_signals[recent_signals['Buy_Signal'] == 1]
            sell_signals = recent_signals[recent_signals['Sell_Signal'] == 1]
            
            if not buy_signals.empty:
                axs[0].scatter(buy_signals.index, buy_signals['Price'], color='green', marker='^', s=100, label='买入信号')
            
            if not sell_signals.empty:
                axs[0].scatter(sell_signals.index, sell_signals['Price'], color='red', marker='v', s=100, label='卖出信号')
        
        axs[0].set_title('价格和移动平均线')
        axs[0].set_ylabel('价格')
        axs[0].grid(True)
        axs[0].legend(loc='upper left')
        
        # 设置x轴日期格式
        axs[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        axs[0].xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(axs[0].xaxis.get_majorticklabels(), rotation=45)
        
        # 2. RSI图
        rsi_period = self.config['indicators']['rsi']['period_short']
        rsi_period_long = self.config['indicators']['rsi']['period_long']
        axs[1].plot(recent_data.index, recent_data[f'RSI{rsi_period}'], label=f'{rsi_period}日RSI', color='purple')
        axs[1].plot(recent_data.index, recent_data[f'RSI{rsi_period_long}'], label=f'{rsi_period_long}日RSI', color='blue')
        axs[1].axhline(y=70, color='red', linestyle='--')
        axs[1].axhline(y=30, color='green', linestyle='--')
        axs[1].axhline(y=50, color='black', linestyle='-')
        axs[1].fill_between(recent_data.index, 70, 100, alpha=0.2, color='red')
        axs[1].fill_between(recent_data.index, 0, 30, alpha=0.2, color='green')
        axs[1].set_title('相对强弱指数(RSI)')
        axs[1].set_ylabel('RSI值')
        axs[1].set_ylim(0, 100)
        axs[1].grid(True)
        axs[1].legend(loc='upper left')
        
        # 3. MACD图
        axs[2].plot(recent_data.index, recent_data['MACD'], label='MACD', color='blue')
        axs[2].plot(recent_data.index, recent_data['MACD_Signal'], label='信号线', color='red')
        
        # 为MACD柱状图着色
        for i in range(len(recent_data)):
            if i == 0:
                continue
            if recent_data['MACD_Histogram'].iloc[i] >= 0:
                axs[2].bar(recent_data.index[i], recent_data['MACD_Histogram'].iloc[i], color='green', width=1)
            else:
                axs[2].bar(recent_data.index[i], recent_data['MACD_Histogram'].iloc[i], color='red', width=1)
        
        axs[2].axhline(y=0, color='black', linestyle='-')
        axs[2].set_title('MACD')
        axs[2].set_ylabel('MACD值')
        axs[2].grid(True)
        axs[2].legend(loc='upper left')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.95)
        
        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.reports_dir, f'technical_analysis_{timestamp}.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        # 同时保存一个最新图表的副本
        latest_filepath = os.path.join(self.reports_dir, 'latest_technical_analysis.png')
        plt.savefig(latest_filepath, dpi=300, bbox_inches='tight')
        
        self.logger.info(f"技术分析图表已保存到: {filepath}")
        
        return filepath