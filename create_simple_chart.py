import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，避免显示问题
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import datetime

def create_simple_chart(signal_type=None):
    """
    创建一个简单的测试图表，展示S&P 500指数和45周移动平均线
    使用最基本的matplotlib功能，避免兼容性问题
    
    参数:
        signal_type: 可以是'golden_cross'、'death_cross'或None
    """
    # 创建一年的数据点（252个交易日左右）
    days = 252
    x = np.arange(days)
    
    # 创建基础价格数据
    if signal_type == 'golden_cross':
        # 金叉：先下降后上升
        base = np.concatenate([
            np.linspace(4000, 3700, days//2),
            np.linspace(3700, 4300, days//2 + days%2)
        ])
    elif signal_type == 'death_cross':
        # 死叉：先上升后下降
        base = np.concatenate([
            np.linspace(3700, 4200, days//2),
            np.linspace(4200, 3600, days//2 + days%2)
        ])
    else:
        # 普通趋势：稳定上升
        base = np.linspace(3800, 4200, days)
    
    # 添加随机波动
    np.random.seed(42)
    noise = np.random.normal(0, 50, days)
    sp500 = base + noise
    
    # 计算45周移动平均线 (约45*5=225个交易日)
    window = min(225, days)
    ma_45w = np.full_like(sp500, np.nan)
    for i in range(window-1, days):
        ma_45w[i] = np.mean(sp500[i-window+1:i+1])
    
    # 创建图表
    plt.figure(figsize=(10, 6))
    plt.plot(x, sp500, label='S&P 500', color='blue')
    plt.plot(x, ma_45w, label='45-Week MA', color='red', linewidth=2)
    
    # 标记交叉点（如果存在）
    if signal_type:
        cross_idx = None
        for i in range(window, days-1):
            if signal_type == 'golden_cross' and sp500[i-1] < ma_45w[i-1] and sp500[i] > ma_45w[i]:
                cross_idx = i
                break
            elif signal_type == 'death_cross' and sp500[i-1] > ma_45w[i-1] and sp500[i] < ma_45w[i]:
                cross_idx = i
                break
        
        if cross_idx:
            plt.scatter(cross_idx, sp500[cross_idx], 
                       color='green' if signal_type == 'golden_cross' else 'red', 
                       s=100, zorder=5)
            signal_label = 'Golden Cross' if signal_type == 'golden_cross' else 'Death Cross'
            plt.annotate(signal_label, 
                        xy=(cross_idx, sp500[cross_idx]),
                        xytext=(30, 30), textcoords='offset points',
                        arrowprops=dict(facecolor='black', shrink=0.05))
    
    # 添加标题和标签
    plt.title('S&P 500 Index and 45-Week Moving Average', fontsize=14)
    plt.xlabel('Trading Days', fontsize=12)
    plt.ylabel('Index Value', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # 生成日期标签
    today = datetime.datetime.now()
    dates = [(today - datetime.timedelta(days=252-i)).strftime('%Y-%m') for i in range(0, days, 50)]
    positions = list(range(0, days, 50))
    plt.xticks(positions, dates, rotation=45)
    
    # 保存图表
    plt.tight_layout()
    plt.savefig('sp500_45wma_chart.png')
    print(f"Chart saved as 'sp500_45wma_chart.png'")
    plt.close()

if __name__ == "__main__":
    print("Select chart type to generate:")
    print("1. Normal trend")
    print("2. With Golden Cross signal")
    print("3. With Death Cross signal")
    
    choice = input("Enter your choice (1/2/3): ").strip()
    
    if choice == '1':
        print("Generating normal trend chart...")
        create_simple_chart()
    elif choice == '2':
        print("Generating chart with Golden Cross signal...")
        create_simple_chart('golden_cross')
    elif choice == '3':
        print("Generating chart with Death Cross signal...")
        create_simple_chart('death_cross')
    else:
        print("Invalid choice, generating normal trend chart...")
        create_simple_chart()