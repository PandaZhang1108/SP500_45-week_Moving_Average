import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import matplotlib.font_manager as fm

def create_test_chart(signal_type=None):
    """
    创建一个测试图表，展示S&P 500指数和45周移动平均线
    
    参数:
        signal_type: 可以是'golden_cross'、'death_cross'或None
    """
    # 设置中文字体
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号
    except:
        print("无法设置中文字体，将使用默认字体")
    
    # 创建一年的日期范围（约250个交易日）
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365)
    dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days)]
    
    # 创建一些随机但有趋势的价格数据
    np.random.seed(42)  # 为了可重复性
    
    # 基础趋势线，取决于信号类型
    if signal_type == 'golden_cross':
        # 金叉：先下降后上升
        trend = np.concatenate([
            np.linspace(4000, 3700, len(dates)//2),
            np.linspace(3700, 4300, len(dates)//2 + len(dates)%2)
        ])
    elif signal_type == 'death_cross':
        # 死叉：先上升后下降
        trend = np.concatenate([
            np.linspace(3700, 4200, len(dates)//2),
            np.linspace(4200, 3600, len(dates)//2 + len(dates)%2)
        ])
    else:
        # 普通趋势：稳定上升
        trend = np.linspace(3800, 4200, len(dates))
    
    # 添加随机波动
    noise = np.random.normal(0, 50, len(dates))
    sp500_prices = trend + noise
    
    # 计算45周移动平均线 (约225个交易日)
    window_size = min(225, len(dates))
    ma_45w = np.concatenate([
        [np.nan] * (window_size - 1),
        [np.mean(sp500_prices[i-window_size+1:i+1]) for i in range(window_size-1, len(dates))]
    ])
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    plt.plot(dates, sp500_prices, label='S&P 500指数', color='blue')
    plt.plot(dates, ma_45w, label='45周移动平均线', color='red', linewidth=2)
    
    # 如果有信号，在图表上标记
    if signal_type == 'golden_cross' or signal_type == 'death_cross':
        # 找到移动平均线和价格线的交叉点
        cross_idx = None
        for i in range(window_size, len(dates)-1):
            if signal_type == 'golden_cross' and sp500_prices[i-1] < ma_45w[i-1] and sp500_prices[i] > ma_45w[i]:
                cross_idx = i
                break
            elif signal_type == 'death_cross' and sp500_prices[i-1] > ma_45w[i-1] and sp500_prices[i] < ma_45w[i]:
                cross_idx = i
                break
        
        if cross_idx:
            plt.scatter(dates[cross_idx], sp500_prices[cross_idx], color='green' if signal_type == 'golden_cross' else 'red', s=100, zorder=5)
            signal_text = '金叉信号' if signal_type == 'golden_cross' else '死叉信号'
            plt.annotate(signal_text, 
                         xy=(dates[cross_idx], sp500_prices[cross_idx]),
                         xytext=(20, 20), textcoords='offset points',
                         arrowprops=dict(facecolor='black', shrink=0.05, width=2))
    
    # 格式化图表
    plt.title('S&P 500指数与45周移动平均线', fontsize=16)
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('指数值', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best', fontsize=12)
    
    # 格式化日期轴
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.gcf().autofmt_xdate()
    
    # 保存图表
    plt.tight_layout()
    plt.savefig('sp500_45wma_chart.png', dpi=300)
    print(f"图表已保存为 'sp500_45wma_chart.png'")
    
    plt.close()

if __name__ == "__main__":
    print("请选择要生成的图表类型：")
    print("1. 普通趋势图")
    print("2. 带金叉信号的图表")
    print("3. 带死叉信号的图表")
    
    choice = input("请输入选择（1/2/3）: ").strip()
    
    if choice == '1':
        print("生成普通趋势图...")
        create_test_chart()
    elif choice == '2':
        print("生成带金叉信号的图表...")
        create_test_chart('golden_cross')
    elif choice == '3':
        print("生成带死叉信号的图表...")
        create_test_chart('death_cross')
    else:
        print("无效选择，将生成普通趋势图")
        create_test_chart()