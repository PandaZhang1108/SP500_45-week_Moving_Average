import os
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime

class DataFetcher:
    """数据获取类，负责从Yahoo Finance获取标普500指数数据"""
    
    def __init__(self, config):
        """
        初始化DataFetcher
        
        Args:
            config: 配置信息
        """
        self.ticker = config['data']['ticker']
        self.period = config['data']['period']
        self.interval = config['data']['interval']
        self.logger = logging.getLogger(__name__)
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    def fetch_data(self):
        """
        获取股票数据
        
        Returns:
            DataFrame: 股票数据
        """
        self.logger.info(f"正在获取 {self.ticker} 的数据 (周期: {self.period}, 间隔: {self.interval})...")
        
        try:
            data = yf.download(
                self.ticker, 
                period=self.period, 
                interval=self.interval, 
                progress=False
            )
            
            if data.empty:
                self.logger.error(f"未能获取 {self.ticker} 的数据")
                return None
            
            self.logger.info(f"成功获取 {len(data)} 条数据记录")
            return data
            
        except Exception as e:
            self.logger.error(f"获取数据时出错: {str(e)}")
            return None
    
    def save_data(self, data):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的DataFrame数据
            
        Returns:
            str: 保存的文件路径
        """
        if data is None or data.empty:
            self.logger.warning("没有数据可以保存")
            return None
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{self.ticker.replace('^', '')}_data_{timestamp}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        # 保存数据
        data.to_csv(filepath)
        self.logger.info(f"数据已保存到: {filepath}")
        
        # 同时保存一个最新数据的副本
        latest_filepath = os.path.join(self.data_dir, "latest_data.csv")
        data.to_csv(latest_filepath)
        
        return filepath
    
    def load_data(self, filepath=None):
        """
        从CSV文件加载数据
        
        Args:
            filepath: 文件路径，如果为None则加载最新的数据
            
        Returns:
            DataFrame: 加载的数据
        """
        if filepath is None:
            filepath = os.path.join(self.data_dir, "latest_data.csv")
        
        if not os.path.exists(filepath):
            self.logger.warning(f"数据文件不存在: {filepath}")
            return None
        
        try:
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            self.logger.info(f"已从 {filepath} 加载 {len(data)} 条数据记录")
            return data
        except Exception as e:
            self.logger.error(f"加载数据时出错: {str(e)}")
            return None