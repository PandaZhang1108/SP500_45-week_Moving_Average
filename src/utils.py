import os
import logging
import yaml
import sys
from datetime import datetime

def setup_logger(log_level='INFO'):
    """
    设置日志记录器
    
    Args:
        log_level: 日志级别
        
    Returns:
        logging.Logger: 日志记录器
    """
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 获取当前日期作为日志文件名
    log_date = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f'monitor_{log_date}.log')
    
    # 配置日志级别
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # 配置日志处理器
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 创建一个指向最新日志文件的符号链接
    latest_log = os.path.join(log_dir, 'latest.log')
    try:
        if os.path.exists(latest_log):
            os.remove(latest_log)
        os.symlink(log_file, latest_log)
    except Exception as e:
        logging.warning(f"无法创建最新日志的符号链接: {str(e)}")
    
    return logging.getLogger()

def load_config(config_path):
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        dict: 配置信息
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        raise Exception(f"加载配置文件时出错: {str(e)}")

def get_project_root():
    """
    获取项目根目录
    
    Returns:
        str: 项目根目录的绝对路径
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def verify_email_config(config):
    """
    验证邮件配置
    
    Args:
        config: 配置信息
        
    Returns:
        bool: 配置是否有效
    """
    if not config['email']['enabled']:
        return True  # 如果邮件功能未启用，则不需要验证
    
    required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'recipient_email']
    for field in required_fields:
        if not config['email'].get(field):
            logging.error(f"邮件配置缺少必要字段: {field}")
            return False
    
    # 检查密码是否在环境变量中设置
    if 'EMAIL_PASSWORD' not in os.environ:
        logging.warning("未设置邮箱密码环境变量 EMAIL_PASSWORD，邮件功能可能无法正常工作")
    
    return True