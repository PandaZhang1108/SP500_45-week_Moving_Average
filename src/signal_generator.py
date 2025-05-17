import pandas as pd
import numpy as np
import logging
from datetime import datetime

class SignalGenerator:
    """生成买入卖出信号的类"""
    
    def __init__(self, config):
        """
        初始化SignalGenerator
        
        Args:
            config: 配置信息
        """
        self.config = config
        self.min_confirm = config['signals']['min_confirm']
        self.logger = logging.getLogger(__name__)
    
    def generate_signals(self, data):
        """
        生成买入卖出信号
        
        Args:
            data: 带有技术指标的数据DataFrame
            
        Returns:
            DataFrame: 带有买入卖出信号的数据
        """
        if data is None or data.empty:
            self.logger.error("没有可用于生成信号的数据")
            return None, None
        
        # 创建数据副本并确保所有NaN值都被删除
        df = data.copy().dropna()
        
        # 初始化信号列
        signals = pd.DataFrame(index=df.index)
        signals['Price'] = df['Close']
        signals['Date'] = signals.index
        
        # 初始化所有信号为0 (0=无信号, 1=买入信号, -1=卖出信号)
        signals['MA_Signal'] = 0
        signals['RSI_Signal'] = 0
        signals['MACD_Signal'] = 0
        signals['BB_Signal'] = 0
        signals['Price_MA_Relation'] = 0
        
        # 获取参数
        ma_short = self.config['indicators']['ma']['short']
        ma_long = self.config['indicators']['ma']['long']
        rsi_period = self.config['indicators']['rsi']['period_short']
        rsi_oversold = self.config['indicators']['rsi']['oversold']
        rsi_overbought = self.config['indicators']['rsi']['overbought']
        
        # 1. 计算移动平均线交叉信号
        # 金叉: 短期均线上穿长期均线
        ma_crossover = (df[f'MA{ma_short}'] > df[f'MA{ma_long}']) & (df[f'MA{ma_short}'].shift(1) <= df[f'MA{ma_long}'].shift(1))
        
        # 死叉: 短期均线下穿长期均线
        ma_crossunder = (df[f'MA{ma_short}'] < df[f'MA{ma_long}']) & (df[f'MA{ma_short}'].shift(1) >= df[f'MA{ma_long}'].shift(1))
        
        signals.loc[ma_crossover, 'MA_Signal'] = 1
        signals.loc[ma_crossunder, 'MA_Signal'] = -1
        
        # 2. 计算RSI信号
        # 超卖反转: RSI从低于30上升到高于30
        rsi_oversold_signal = (df[f'RSI{rsi_period}'] > rsi_oversold) & (df[f'RSI{rsi_period}'].shift(1) <= rsi_oversold)
        
        # 超买反转: RSI从高于70下降到低于70
        rsi_overbought_signal = (df[f'RSI{rsi_period}'] < rsi_overbought) & (df[f'RSI{rsi_period}'].shift(1) >= rsi_overbought)
        
        signals.loc[rsi_oversold_signal, 'RSI_Signal'] = 1
        signals.loc[rsi_overbought_signal, 'RSI_Signal'] = -1
        
        # 3. 计算MACD信号
        # 金叉: MACD线上穿信号线
        macd_crossover = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        
        # 死叉: MACD线下穿信号线
        macd_crossunder = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        
        signals.loc[macd_crossover, 'MACD_Signal'] = 1
        signals.loc[macd_crossunder, 'MACD_Signal'] = -1
        
        # 4. 计算布林带信号 - 使用最简单安全的方式
        try:
            # 逐行遍历数据以避免任何对齐问题
            for i in range(1, len(df)):
                # 安全获取当前和前一个时间点的值
                curr_idx = df.index[i]
                prev_idx = df.index[i-1]
                
                # 下轨信号
                if df.loc[prev_idx, 'Close'] <= df.loc[prev_idx, 'BB_Lower'] and df.loc[curr_idx, 'Close'] > df.loc[curr_idx, 'BB_Lower']:
                    signals.loc[curr_idx, 'BB_Signal'] = 1
                
                # 上轨信号
                if df.loc[prev_idx, 'Close'] >= df.loc[prev_idx, 'BB_Upper'] and df.loc[curr_idx, 'Close'] < df.loc[curr_idx, 'BB_Upper']:
                    signals.loc[curr_idx, 'BB_Signal'] = -1
        except Exception as e:
            self.logger.error(f"计算布林带信号时出错: {str(e)}")
            # 如果出错，将BB_Signal设为0
            signals['BB_Signal'] = 0
        
        # 5. 价格与移动平均线关系 - 使用最简单安全的方式
        try:
            # 逐行遍历数据以避免任何对齐问题
            for i in range(1, len(df)):
                # 安全获取当前和前一个时间点的值
                curr_idx = df.index[i]
                prev_idx = df.index[i-1]
                
                # 价格站上长期均线
                if df.loc[curr_idx, 'Close'] > df.loc[curr_idx, f'MA{ma_long}'] and df.loc[prev_idx, 'Close'] <= df.loc[prev_idx, f'MA{ma_long}']:
                    signals.loc[curr_idx, 'Price_MA_Relation'] = 1
                
                # 价格跌破长期均线
                if df.loc[curr_idx, 'Close'] < df.loc[curr_idx, f'MA{ma_long}'] and df.loc[prev_idx, 'Close'] >= df.loc[prev_idx, f'MA{ma_long}']:
                    signals.loc[curr_idx, 'Price_MA_Relation'] = -1
        except Exception as e:
            self.logger.error(f"计算价格与均线关系时出错: {str(e)}")
            # 如果出错，将Price_MA_Relation设为0
            signals['Price_MA_Relation'] = 0
        
        # 综合信号: 至少需要min_confirm个指标同时给出买入或卖出信号
        signal_columns = ['MA_Signal', 'RSI_Signal', 'MACD_Signal', 'BB_Signal', 'Price_MA_Relation']
        signals['Total_Buy_Signals'] = signals[signal_columns].apply(lambda x: (x > 0).sum(), axis=1)
        signals['Total_Sell_Signals'] = signals[signal_columns].apply(lambda x: (x < 0).sum(), axis=1)
        
        # 生成最终的买入卖出信号
        signals['Buy_Signal'] = (signals['Total_Buy_Signals'] >= self.min_confirm).astype(int)
        signals['Sell_Signal'] = (signals['Total_Sell_Signals'] >= self.min_confirm).astype(int)
        
        # 只保留有信号的日期
        buy_signals = signals[signals['Buy_Signal'] == 1]
        sell_signals = signals[signals['Sell_Signal'] == 1]
        
        # 统计信号
        self.logger.info(f"生成的信号统计: 买入信号: {len(buy_signals)}, 卖出信号: {len(sell_signals)}")
        
        # 合并结果
        result = pd.concat([df, signals[['MA_Signal', 'RSI_Signal', 'MACD_Signal', 
                                         'BB_Signal', 'Price_MA_Relation', 
                                         'Buy_Signal', 'Sell_Signal']]], axis=1)
        
        return result, signals
    
    def get_latest_signals(self, signals, lookback=None):
        """
        获取最近的买入卖出信号
        
        Args:
            signals: 信号DataFrame
            lookback: 回看的天数，如果为None则使用配置中的值
            
        Returns:
            dict: 包含最近买入和卖出信号的字典
        """
        if lookback is None:
            lookback = self.config['signals']['lookback']
        
        # 获取最近的数据
        recent_signals = signals.tail(lookback)
        
        # 查找买入信号
        buy_signals = recent_signals[recent_signals['Buy_Signal'] == 1]
        
        # 查找卖出信号
        sell_signals = recent_signals[recent_signals['Sell_Signal'] == 1]
        
        result = {
            'latest_buy': None,
            'latest_sell': None
        }
        
        if not buy_signals.empty:
            latest_buy = buy_signals.iloc[-1]
            buy_date = latest_buy.name
            
            result['latest_buy'] = {
                'date': buy_date.strftime('%Y-%m-%d') if hasattr(buy_date, 'strftime') else str(buy_date),
                'price': latest_buy['Price'],
                'ma_signal': latest_buy['MA_Signal'],
                'rsi_signal': latest_buy['RSI_Signal'],
                'macd_signal': latest_buy['MACD_Signal'],
                'bb_signal': latest_buy['BB_Signal'],
                'price_ma_signal': latest_buy['Price_MA_Relation'],
                'total_signals': latest_buy['Total_Buy_Signals']
            }
        
        if not sell_signals.empty:
            latest_sell = sell_signals.iloc[-1]
            sell_date = latest_sell.name
            
            result['latest_sell'] = {
                'date': sell_date.strftime('%Y-%m-%d') if hasattr(sell_date, 'strftime') else str(sell_date),
                'price': latest_sell['Price'],
                'ma_signal': latest_sell['MA_Signal'],
                'rsi_signal': latest_sell['RSI_Signal'],
                'macd_signal': latest_sell['MACD_Signal'],
                'bb_signal': latest_sell['BB_Signal'],
                'price_ma_signal': latest_sell['Price_MA_Relation'],
                'total_signals': latest_sell['Total_Sell_Signals']
            }
        
        return result