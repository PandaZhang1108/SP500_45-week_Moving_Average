import pandas as pd
import numpy as np
import logging

class TechnicalIndicators:
    """计算技术指标的类"""
    
    def __init__(self, config):
        """
        初始化TechnicalIndicators
        
        Args:
            config: 配置信息
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_all(self, data):
        """
        计算所有技术指标
        
        Args:
            data: 价格数据DataFrame
            
        Returns:
            DataFrame: 带有计算出的指标的数据
        """
        if data is None or data.empty:
            self.logger.error("没有可用于计算指标的数据")
            return None
        
        # 创建数据副本
        df = data.copy()
        
        # 计算移动平均线
        df = self.calculate_moving_averages(df)
        
        # 计算RSI
        df = self.calculate_rsi(df)
        
        # 计算MACD
        df = self.calculate_macd(df)
        
        # 计算布林带
        df = self.calculate_bollinger_bands(df)
        
        return df
    
    def calculate_moving_averages(self, data):
        """
        计算移动平均线
        
        Args:
            data: 价格数据DataFrame
            
        Returns:
            DataFrame: 带有MA的数据
        """
        df = data.copy()
        
        # 获取配置参数
        short_period = self.config['indicators']['ma']['short']
        long_period = self.config['indicators']['ma']['long']
        
        # 计算短期和长期移动平均线
        df[f'MA{short_period}'] = df['Close'].rolling(window=short_period).mean()
        df[f'MA{long_period}'] = df['Close'].rolling(window=long_period).mean()
        
        self.logger.debug(f"已计算 MA{short_period} 和 MA{long_period}")
        
        return df
    
    def calculate_rsi(self, data):
        """
        计算相对强弱指数(RSI)
        
        Args:
            data: 价格数据DataFrame
            
        Returns:
            DataFrame: 带有RSI的数据
        """
        df = data.copy()
        
        # 获取配置参数
        short_period = self.config['indicators']['rsi']['period_short']
        long_period = self.config['indicators']['rsi']['period_long']
        
        # 计算价格变化
        delta = df['Close'].diff()
        
        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        # 计算短期RSI
        avg_gain_short = gain.rolling(window=short_period).mean()
        avg_loss_short = loss.rolling(window=short_period).mean()
        rs_short = avg_gain_short / avg_loss_short.replace(0, np.finfo(float).eps)  # 避免除零错误
        df[f'RSI{short_period}'] = 100 - (100 / (1 + rs_short))
        
        # 计算长期RSI
        avg_gain_long = gain.rolling(window=long_period).mean()
        avg_loss_long = loss.rolling(window=long_period).mean()
        rs_long = avg_gain_long / avg_loss_long.replace(0, np.finfo(float).eps)  # 避免除零错误
        df[f'RSI{long_period}'] = 100 - (100 / (1 + rs_long))
        
        self.logger.debug(f"已计算 RSI{short_period} 和 RSI{long_period}")
        
        return df
    
    def calculate_macd(self, data):
        """
        计算MACD指标
        
        Args:
            data: 价格数据DataFrame
            
        Returns:
            DataFrame: 带有MACD的数据
        """
        df = data.copy()
        
        # 获取配置参数
        fast_period = self.config['indicators']['macd']['fast']
        slow_period = self.config['indicators']['macd']['slow']
        signal_period = self.config['indicators']['macd']['signal']
        
        # 计算快速和慢速EMA
        df['EMA_fast'] = df['Close'].ewm(span=fast_period, adjust=False).mean()
        df['EMA_slow'] = df['Close'].ewm(span=slow_period, adjust=False).mean()
        
        # 计算MACD线和信号线
        df['MACD'] = df['EMA_fast'] - df['EMA_slow']
        df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
        
        # 计算MACD柱状图
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        self.logger.debug(f"已计算 MACD ({fast_period}, {slow_period}, {signal_period})")
        
        return df
    
    def calculate_bollinger_bands(self, data):
        """
        计算布林带
        
        Args:
            data: 价格数据DataFrame
            
        Returns:
            DataFrame: 带有布林带的数据
        """
        df = data.copy()
        
        # 获取配置参数
        period = self.config['indicators']['bollinger']['period']
        std_dev = self.config['indicators']['bollinger']['std_dev']
        
        # 计算中轨(SMA)
        df['BB_Middle'] = df['Close'].rolling(window=period).mean()
        
        # 计算标准差
        df['BB_Std'] = df['Close'].rolling(window=period).std()
        
        # 计算上轨和下轨
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * std_dev)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * std_dev)
        
        self.logger.debug(f"已计算布林带 (周期: {period}, 标准差: {std_dev})")
        
        return df