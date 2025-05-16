"""
一个非常简单的脚本，生成静态的S&P 500和45周移动平均线图表
不依赖于matplotlib，只使用PIL库创建一个基本图像
"""

from PIL import Image, ImageDraw, ImageFont
import random
import os

def create_static_chart(signal_type=None):
    """
    创建一个静态图表，展示S&P 500指数和45周移动平均线的示意图
    
    参数:
        signal_type: 可以是'golden_cross'、'death_cross'或None
    """
    # 创建一个空白图像
    width, height = 800, 600
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 尝试加载字体，如果失败则使用默认字体
    try:
        font_title = ImageFont.truetype("Arial", 24)
        font_label = ImageFont.truetype("Arial", 16)
    except IOError:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
    
    # 绘制标题
    draw.text((width//2 - 180, 20), "S&P 500指数与45周移动平均线", fill=(0, 0, 0), font=font_title)
    
    # 绘制坐标轴
    margin = 60
    axis_left = margin
    axis_right = width - margin
    axis_top = margin
    axis_bottom = height - margin
    
    # 绘制X和Y轴
    draw.line([(axis_left, axis_bottom), (axis_right, axis_bottom)], fill=(0, 0, 0), width=2)  # X轴
    draw.line([(axis_left, axis_top), (axis_left, axis_bottom)], fill=(0, 0, 0), width=2)  # Y轴
    
    # 绘制X轴标签
    months = ["2023-05", "2023-07", "2023-09", "2023-11", "2024-01", "2024-03", "2024-05"]
    for i, month in enumerate(months):
        x = axis_left + (axis_right - axis_left) * i // (len(months) - 1)
        draw.text((x - 20, axis_bottom + 10), month, fill=(0, 0, 0), font=font_label)
        draw.line([(x, axis_bottom), (x, axis_bottom + 5)], fill=(0, 0, 0), width=1)
    
    # 绘制Y轴标签
    values = ["3600", "3800", "4000", "4200", "4400"]
    for i, value in enumerate(values):
        y = axis_bottom - (axis_bottom - axis_top) * i // (len(values) - 1)
        draw.text((axis_left - 50, y - 10), value, fill=(0, 0, 0), font=font_label)
        draw.line([(axis_left - 5, y), (axis_left, y)], fill=(0, 0, 0), width=1)
    
    # 生成数据点
    points = 252  # 约一年的交易日
    x_step = (axis_right - axis_left) / (points - 1)
    
    # 创建S&P 500数据点
    sp500_points = []
    ma_points = []
    
    # 根据信号类型生成不同的曲线
    if signal_type == 'golden_cross':
        # 金叉：先下降后上升的曲线
        for i in range(points):
            x = axis_left + i * x_step
            # 前半段下降，后半段上升
            if i < points // 2:
                y = axis_bottom - (axis_bottom - axis_top) * (0.5 - 0.2 * i / (points // 2))
            else:
                y = axis_bottom - (axis_bottom - axis_top) * (0.3 + 0.4 * (i - points // 2) / (points // 2))
            
            # 添加一些随机波动
            y += random.randint(-10, 10)
            sp500_points.append((x, y))
            
            # 移动平均线滞后于价格线
            if i < points // 2 + 20:
                ma_y = axis_bottom - (axis_bottom - axis_top) * (0.5 - 0.15 * i / (points // 2))
            else:
                ma_y = axis_bottom - (axis_bottom - axis_top) * (0.35 + 0.25 * (i - points // 2 - 20) / (points // 2))
            ma_points.append((x, ma_y))
        
        # 标记金叉位置
        cross_x = axis_left + (points // 2 + 20) * x_step
        cross_y = sp500_points[points // 2 + 20][1]
        draw.ellipse([(cross_x - 8, cross_y - 8), (cross_x + 8, cross_y + 8)], fill=(0, 255, 0))
        draw.text((cross_x + 10, cross_y - 30), "金叉信号", fill=(0, 100, 0), font=font_label)
        
    elif signal_type == 'death_cross':
        # 死叉：先上升后下降的曲线
        for i in range(points):
            x = axis_left + i * x_step
            # 前半段上升，后半段下降
            if i < points // 2:
                y = axis_bottom - (axis_bottom - axis_top) * (0.3 + 0.4 * i / (points // 2))
            else:
                y = axis_bottom - (axis_bottom - axis_top) * (0.7 - 0.3 * (i - points // 2) / (points // 2))
            
            # 添加一些随机波动
            y += random.randint(-10, 10)
            sp500_points.append((x, y))
            
            # 移动平均线滞后于价格线
            if i < points // 2 + 20:
                ma_y = axis_bottom - (axis_bottom - axis_top) * (0.35 + 0.3 * i / (points // 2))
            else:
                ma_y = axis_bottom - (axis_bottom - axis_top) * (0.65 - 0.2 * (i - points // 2 - 20) / (points // 2))
            ma_points.append((x, ma_y))
        
        # 标记死叉位置
        cross_x = axis_left + (points // 2 + 20) * x_step
        cross_y = sp500_points[points // 2 + 20][1]
        draw.ellipse([(cross_x - 8, cross_y - 8), (cross_x + 8, cross_y + 8)], fill=(255, 0, 0))
        draw.text((cross_x + 10, cross_y - 30), "死叉信号", fill=(150, 0, 0), font=font_label)
        
    else:
        # 普通趋势：稳定上升的曲线
        for i in range(points):
            x = axis_left + i * x_step
            # 稳定上升的趋势
            y = axis_bottom - (axis_bottom - axis_top) * (0.2 + 0.5 * i / points)
            
            # 添加一些随机波动
            y += random.randint(-15, 15)
            sp500_points.append((x, y))
            
            # 移动平均线更平滑，波动更小
            if i < 45:  # 无足够数据计算移动平均线
                ma_y = axis_bottom - 10  # 接近底部
            else:
                ma_y = axis_bottom - (axis_bottom - axis_top) * (0.2 + 0.45 * (i - 45) / (points - 45))
                ma_y += random.randint(-5, 5)  # 移动平均线波动较小
            ma_points.append((x, ma_y))
    
    # 绘制S&P 500曲线
    for i in range(1, len(sp500_points)):
        draw.line([sp500_points[i-1], sp500_points[i]], fill=(0, 0, 255), width=2)
    
    # 绘制45周移动平均线
    for i in range(1, len(ma_points)):
        draw.line([ma_points[i-1], ma_points[i]], fill=(255, 0, 0), width=2)
    
    # 绘制图例
    legend_x = axis_right - 200
    legend_y = axis_top + 30
    draw.line([(legend_x, legend_y), (legend_x + 30, legend_y)], fill=(0, 0, 255), width=2)
    draw.text((legend_x + 40, legend_y - 10), "S&P 500指数", fill=(0, 0, 255), font=font_label)
    
    legend_y += 30
    draw.line([(legend_x, legend_y), (legend_x + 30, legend_y)], fill=(255, 0, 0), width=2)
    draw.text((legend_x + 40, legend_y - 10), "45周移动平均线", fill=(255, 0, 0), font=font_label)
    
    # 保存图表
    image.save("sp500_45wma_chart.png")
    print(f"图表已保存为 'sp500_45wma_chart.png'")
    
    return "sp500_45wma_chart.png"

if __name__ == "__main__":
    print("请选择要生成的图表类型：")
    print("1. 普通趋势图")
    print("2. 带金叉信号的图表")
    print("3. 带死叉信号的图表")
    
    choice = input("请输入选择（1/2/3）: ").strip()
    
    if choice == '1':
        print("生成普通趋势图...")
        create_static_chart()
    elif choice == '2':
        print("生成带金叉信号的图表...")
        create_static_chart('golden_cross')
    elif choice == '3':
        print("生成带死叉信号的图表...")
        create_static_chart('death_cross')
    else:
        print("无效选择，将生成普通趋势图")
        create_static_chart()