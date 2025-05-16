import os
import argparse
import pandas as pd
from datetime import datetime

from src.utils import setup_logger, load_config, get_project_root, verify_email_config
from src.data_fetcher import DataFetcher
from src.indicators import TechnicalIndicators
from src.signal_generator import SignalGenerator
from src.analyzer import MarketAnalyzer
from src.notifier import EmailNotifier

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='标普500技术指标监控系统')
    parser.add_argument('--config', type=str, default='config.yaml', 
                        help='配置文件路径')
    parser.add_argument('--mode', type=str, choices=['auto', 'manual'], 
                        help='运行模式: auto(自动) 或 manual(手动)')
    parser.add_argument('--notify', action='store_true', 
                        help='发送通知')
    parser.add_argument('--plot', action='store_true', 
                        help='生成图表')
    parser.add_argument('--save-data', action='store_true', 
                        help='保存数据')
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 获取项目根目录
    root_dir = get_project_root()
    
    # 加载配置
    config_path = os.path.join(root_dir, args.config)
    config = load_config(config_path)
    
    # 设置日志
    logger = setup_logger(config['run']['log_level'])
    logger.info("启动标普500技术指标监控系统...")
    
    # 检查运行模式
    run_mode = args.mode if args.mode else config['run']['mode']
    logger.info(f"运行模式: {run_mode}")
    
    # 初始化组件
    data_fetcher = DataFetcher(config)
    indicator_calculator = TechnicalIndicators(config)
    signal_generator = SignalGenerator(config)
    market_analyzer = MarketAnalyzer(config)
    email_notifier = EmailNotifier(config)
    
    # 验证邮件配置
    if not verify_email_config(config):
        logger.warning("邮件配置无效，将禁用邮件通知")
    
    # 获取数据
    data = data_fetcher.fetch_data()
    if data is None:
        logger.error("无法获取数据，程序终止")
        return
    
    # 保存数据
    save_data = args.save_data if args.save_data else config['run']['save_data']
    if save_data:
        data_fetcher.save_data(data)
    
    # 计算技术指标
    data_with_indicators = indicator_calculator.calculate_all(data)
    if data_with_indicators is None:
        logger.error("计算技术指标失败，程序终止")
        return
    
    # 生成信号
    data_with_signals, signals = signal_generator.generate_signals(data_with_indicators)
    if data_with_signals is None:
        logger.error("生成信号失败，程序终止")
        return
    
    # 分析市场状态
    market_status = market_analyzer.analyze_market_status(data_with_indicators, signals)
    if market_status is None:
        logger.error("分析市场状态失败，程序终止")
        return
    
    # 获取最近的信号
    latest_signals = signal_generator.get_latest_signals(signals)
    
    # 创建摘要报告
    report = market_analyzer.create_summary_report(market_status, latest_signals)
    
    # 打印当前市场状态
    print("\n==== 标普500指数当前市场状态 ====")
    print(f"日期: {market_status['date']}")
    print(f"价格: {market_status['price']:.2f}")
    print(f"50日均线: {market_status['ma_short']:.2f}")
    print(f"200日均线: {market_status['ma_long']:.2f}")
    print(f"14日RSI: {market_status['rsi']:.2f}")
    print(f"MACD: {market_status['macd']:.6f}, 信号线: {market_status['macd_signal']:.6f}")
    print(f"\n市场趋势: {market_status['trend']}")
    print(f"市场强弱: {market_status['strength']}")
    print(f"市场动能: {market_status['momentum']}")
    
    # 生成图表
    chart_path = None
    plot_charts = args.plot if args.plot else config['run']['save_plots']
    if plot_charts:
        chart_path = market_analyzer.plot_indicators(data_with_indicators, signals)
    
    # 检查是否有新的买入或卖出信号
    today = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    # 获取最新的买入和卖出信号
    latest_buy = latest_signals['latest_buy']
    latest_sell = latest_signals['latest_sell']
    
    # 检查是否在今天或昨天产生了新信号
    found_new_signal = False
    
    # 处理买入信号
    if latest_buy and latest_buy['date'] == today:
        logger.info(f"发现今日买入信号: {latest_buy['date']}, 价格: {latest_buy['price']:.2f}")
        
        # 发送买入信号通知
        notify = args.notify if args.notify else config['email']['enabled']
        if notify:
            email_notifier.send_signal_notification('buy', latest_buy, market_status, chart_path)
        
        found_new_signal = True
    
    # 处理卖出信号
    if latest_sell and latest_sell['date'] == today:
        logger.info(f"发现今日卖出信号: {latest_sell['date']}, 价格: {latest_sell['price']:.2f}")
        
        # 发送卖出信号通知
        notify = args.notify if args.notify else config['email']['enabled']
        if notify:
            email_notifier.send_signal_notification('sell', latest_sell, market_status, chart_path)
        
        found_new_signal = True
    
    # 如果没有新信号且在自动模式下，发送每日摘要
    if not found_new_signal and run_mode == 'auto':
        logger.info("没有发现新的交易信号，将发送每日摘要...")
        notify = args.notify if args.notify else config['email']['enabled']
        if notify:
            email_notifier.send_summary_email(market_status, latest_signals, chart_path)
    
    logger.info("标普500技术指标监控系统运行完成")

if __name__ == "__main__":
    main()