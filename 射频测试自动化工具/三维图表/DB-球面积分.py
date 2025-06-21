import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def calculate_signal_strength(theta, phi, phone_dimensions):
    """根据角度计算信号强度，靠近右下角天线的位置信号更强"""
    # 将球坐标转换为直角坐标
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)
    
    # 手机四个角落在球坐标系中的位置（近似）
    corners = {
        'upper_left': np.array([-phone_dimensions[0]/2, phone_dimensions[1]/2, 0]),
        'lower_left': np.array([-phone_dimensions[0]/2, -phone_dimensions[1]/2, 0]),
        'upper_right': np.array([phone_dimensions[0]/2, phone_dimensions[1]/2, 0]),
        'lower_right': np.array([phone_dimensions[0]/2, -phone_dimensions[1]/2, 0])
    }
    
    # 计算当前点到右下角天线的距离
    distance = np.sqrt(
        (x - corners['lower_right'][0])**2 + 
        (y - corners['lower_right'][1])**2 + 
        (z - corners['lower_right'][2])**2
    )
    
    # 信号强度模型：距离越近，信号越强
    max_strength = 26  # 最大信号强度(dBm)
    min_strength = 10  # 最小信号强度(dBm)
    
    # 将距离归一化并转换为信号强度
    normalized_distance = np.clip(distance / np.sqrt(2), 0, 1)
    signal_strength = max_strength - normalized_distance * (max_strength - min_strength)
    
    return signal_strength

def generate_spherical_points(n_points, phone_dimensions):
    """生成球面上的随机点，并计算每个点的信号强度"""
    # 生成均匀分布的球面点
    phi = np.random.uniform(0, 2 * np.pi, n_points)
    cos_theta = np.random.uniform(-1, 1, n_points)
    theta = np.arccos(cos_theta)
    
    # 计算信号强度
    signal_strength = calculate_signal_strength(theta, phi, phone_dimensions)
    
    # 计算直角坐标
    r = np.ones(n_points)  # 单位球面
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    
    return theta, phi, r, signal_strength, x, y, z

def calculate_trp(signal_strength, theta, phi):
    """根据信号强度计算TRP (Total Radiated Power)"""
    # 将dBm转换为mW
    power_mw = 10 ** (signal_strength / 10)
    
    # 使用球面积分近似计算TRP
    # 对于均匀分布的点，可以使用平均值乘以立体角
    solid_angle = 4 * np.pi  # 整个球面的立体角
    avg_power = np.mean(power_mw)
    trp = avg_power * solid_angle
    
    # 转换回dBm
    trp_dbm = 10 * np.log10(trp)
    
    return trp, trp_dbm

def save_to_file(theta, phi, r, signal_strength, filename='antenna_data.txt'):
    """将数据保存到文本文件"""
    # 创建保存目录（如果不存在）
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # 保存数据
    with open(filename, 'w') as f:
        f.write("# theta (rad), phi (rad), r, signal_strength (dBm)\n")
        for t, p, r_val, s in zip(theta, phi, r, signal_strength):
            f.write(f"{t:.6f}, {p:.6f}, {r_val:.6f}, {s:.6f}\n")
    
    print(f"数据已保存到 {filename}")

def plot_radiation_pattern(theta, phi, x, y, z, signal_strength, phone_dimensions):
    """绘制辐射模式图"""
    # 创建一个包含两个子图的图形
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}]],
        subplot_titles=('辐射模式 (3D)', '辐射模式 (球面)')
    )
    
    # 添加3D直角坐标系中的散点图
    scatter1 = go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(
            size=5,
            color=signal_strength,
            colorscale='Viridis',
            colorbar=dict(title='信号强度 (dBm)'),
            opacity=0.8
        ),
        name='信号强度'
    )
    fig.add_trace(scatter1, row=1, col=1)
    
    # 添加手机位置（简化为一个立方体）
    corners = [
        [-phone_dimensions[0]/2, -phone_dimensions[1]/2, 0],  # 左下
        [phone_dimensions[0]/2, -phone_dimensions[1]/2, 0],   # 右下
        [phone_dimensions[0]/2, phone_dimensions[1]/2, 0],    # 右上
        [-phone_dimensions[0]/2, phone_dimensions[1]/2, 0],   # 左上
    ]
    
    # 绘制手机轮廓线
    for i in range(4):
        fig.add_trace(go.Scatter3d(
            x=[corners[i][0], corners[(i+1)%4][0]],
            y=[corners[i][1], corners[(i+1)%4][1]],
            z=[corners[i][2], corners[(i+1)%4][2]],
            mode='lines',
            line=dict(color='red', width=3),
            showlegend=False
        ), row=1, col=1)
    
    # 在球面坐标系中绘制
    # 转换为球面坐标
    r_sphere = signal_strength / np.max(signal_strength)  # 归一化信号强度作为半径
    x_sphere = r_sphere * np.sin(theta) * np.cos(phi)
    y_sphere = r_sphere * np.sin(theta) * np.sin(phi)
    z_sphere = r_sphere * np.cos(theta)
    
    scatter2 = go.Scatter3d(
        x=x_sphere, y=y_sphere, z=z_sphere,
        mode='markers',
        marker=dict(
            size=5,
            color=signal_strength,
            colorscale='Viridis',
            colorbar=dict(title='信号强度 (dBm)'),
            opacity=0.8
        ),
        name='信号强度'
    )
    fig.add_trace(scatter2, row=1, col=2)
    
    # 添加球面轮廓线
    u = np.linspace(0, np.pi, 30)
    v = np.linspace(0, 2 * np.pi, 30)
    U, V = np.meshgrid(u, v)
    
    X = np.sin(U) * np.cos(V)
    Y = np.sin(U) * np.sin(V)
    Z = np.cos(U)
    
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0.1)']],
        showscale=False,
        opacity=0.3
    ), row=1, col=2)
    
    # 更新布局
    fig.update_layout(
        title_text='手机右下角天线辐射模式',
        height=700,
        width=1400,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='cube'
        ),
        scene2=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='cube'
        )
    )
    
    return fig

def main():
    # 参数设置
    n_points = 1000  # 采样点数量
    phone_dimensions = [0.15, 0.07, 0.01]  # 手机尺寸 (m)
    
    # 生成数据
    print("正在生成模拟数据...")
    theta, phi, r, signal_strength, x, y, z = generate_spherical_points(n_points, phone_dimensions)
    
    # 计算TRP
    print("正在计算TRP...")
    trp, trp_dbm = calculate_trp(signal_strength, theta, phi)
    print(f"计算得到的TRP: {trp:.4f} mW ({trp_dbm:.2f} dBm)")
    
    # 保存数据
    save_to_file(theta, phi, r, signal_strength)
    
    # 绘制辐射模式图
    print("正在绘制辐射模式图...")
    fig = plot_radiation_pattern(theta, phi, x, y, z, signal_strength, phone_dimensions)
    
    # 显示图形
    fig.show()

if __name__ == "__main__":
    main()    