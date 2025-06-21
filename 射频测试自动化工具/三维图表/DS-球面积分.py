import numpy as np
import plotly.graph_objects as go
import math

# 1. 定义手机参数
phone_width = 0.07  # 手机宽度 (米)
phone_height = 0.14  # 手机高度 (米)
phone_thickness = 0.007  # 手机厚度 (米)

# 手机四个天线的位置 (基于几何中心)
antennas = {
    "top_left": np.array([0, -phone_width/2, phone_height/2]),
    "top_right": np.array([0, phone_width/2, phone_height/2]),
    "bottom_left": np.array([0, -phone_width/2, -phone_height/2]),
    "bottom_right": np.array([0, phone_width/2, -phone_height/2])
}

# 2. 创建球坐标网格 (修正后的斐波那契采样)
num_points = 108
indices = np.arange(num_points, dtype=float) + 0.5

phi = np.arccos(1 - 2*indices/num_points)  # 天顶角 [0, π]
theta = (2 * np.pi * indices) / ((1 + np.sqrt(5)) / 2)  # 方位角 [0, 2π]

# 3. 计算信号强度 (修正参数传递)
def calculate_signal_strength(theta, phi, source_ant):
    # 转换为直角坐标
    y = np.sin(phi) * np.cos(theta)  # 修正：使用phi作为天顶角
    z = np.sin(phi) * np.sin(theta)
    x = np.cos(phi)
    
    dir_vec = np.stack([x, y, z], axis=-1)
    source_vec = source_ant / np.linalg.norm(source_ant)
    
    cos_angle = np.sum(dir_vec * source_vec, axis=-1)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    
    angle = np.arccos(cos_angle)
    strength = 26 * np.exp(-10 * angle**2)
    strength += np.random.normal(0, 0.5, strength.shape)
    
    return np.clip(strength, -40, 26)

signal_strength = calculate_signal_strength(theta, phi, antennas["bottom_right"])

# 4. 计算TRP (修正权重计算)
def calculate_trp(signal_dbm, phi):
    signal_mw = 10 ** (signal_dbm / 10)
    
    # 每个点的立体角权重 (4π/num_points)
    weights = 4 * np.pi / num_points * np.sin(phi)
    
    total_power = np.sum(signal_mw * weights)
    trp_dbm = 10 * np.log10(total_power) if total_power > 0 else -np.inf
    return trp_dbm, total_power

trp_dbm, trp_mw = calculate_trp(signal_strength, phi)
print(f"计算得到的TRP: {trp_dbm:.2f} dBm ({trp_mw:.2e} mW)")

# 5. 数据保存 (保持不变)
def save_to_txt(filename, theta, phi, strength):
    with open(filename, 'w') as f:
        f.write("Theta(deg)\tPhi(deg)\tSignal_Strength(dBm)\n")
        for i in range(num_points):
            t_deg = math.degrees(theta[i]) % 360
            p_deg = math.degrees(phi[i])
            f.write(f"{t_deg:.2f}\t{p_deg:.2f}\t{signal_strength[i]:.2f}\n")
    print(f"数据已保存到 {filename}")

save_to_txt("antenna_signal_data.txt", theta, phi, signal_strength)

# 6. 三维可视化 (修正为散点图)
def create_3d_plot():
    # 转换为直角坐标系
    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)
    
    # 创建天线位置标记
    antenna_markers = []
    for name, pos in antennas.items():
        norm = np.linalg.norm(pos)
        pos_normalized = pos / norm if norm > 0 else pos
        antenna_markers.append(
            go.Scatter3d(
                x=[pos_normalized[0]], y=[pos_normalized[1]], z=[pos_normalized[2]],
                mode='markers+text',
                marker=dict(size=8, color='red'),
                text=[name],
                textposition="top center",
                name=f"{name} Antenna"
            )
        )

    # 创建散点图
    scatter = go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(
            size=6,
            color=signal_strength,
            colorscale='Jet',
            cmin=-40,
            cmax=26,
            opacity=0.8,
            colorbar=dict(title='Signal Strength (dBm)')
        ),
        name='Radiation Pattern'
    )
    
    # 创建手机模型框架
    # 简化手机模型为一个小立方体
    phone_frame = go.Mesh3d(
        # 8个顶点
        x=[0, 0, 0, 0, phone_thickness, phone_thickness, phone_thickness, phone_thickness],
        y=[-phone_width/2, -phone_width/2, phone_width/2, phone_width/2,
        -phone_width/2, -phone_width/2, phone_width/2, phone_width/2],
        z=[-phone_height/2, phone_height/2, -phone_height/2, phone_height/2,
        -phone_height/2, phone_height/2, -phone_height/2, phone_height/2],
        
        # 定义12个三角形组成长方体
        i=[7, 0, 0, 0, 4, 4, 6, 6, 5, 5, 1, 6],
        j=[3, 4, 1, 2, 7, 6, 5, 2, 1, 2, 2, 3],
        k=[0, 7, 2, 4, 5, 0, 1, 7, 0, 3, 6, 7],
        opacity=0.3,
        color='lightblue',
        name='Phone Frame',
        flatshading=True
    )
    
    # 创建坐标轴
    axes = [
        go.Scatter3d(x=[0, 0.3], y=[0, 0], z=[0, 0], mode='lines', line=dict(color='red', width=4), name='X-axis'),
        go.Scatter3d(x=[0, 0], y=[0, 0.3], z=[0, 0], mode='lines', line=dict(color='green', width=4), name='Y-axis'),
        go.Scatter3d(x=[0, 0], y=[0, 0], z=[0, 0.3], mode='lines', line=dict(color='blue', width=4), name='Z-axis')
    ]
    
    # 添加标注
    annotations = [
        dict(x=0.32, y=0, z=0, text="Y", showarrow=False, font=dict(color='green')), 
        dict(x=0, y=0, z=0.32, text="Z", showarrow=False, font=dict(color='blue')),  
        dict(x=0, y=0.32, z=0, text="X", showarrow=False, font=dict(color='red'))    
    ]

    fig = go.Figure(data=[scatter, *antenna_markers, phone_frame, *axes])
    
    fig.update_layout(
        title=f'Mobile Antenna Radiation Pattern (离散探头)<br>TRP: {trp_dbm:.2f} dBm',
        scene=dict(
            camera=dict(eye=dict(x=1.5, y=1.5, z=0.8)),
            aspectratio=dict(x=1, y=1, z=1)
        ),
        height=800
    )
    return fig

fig = create_3d_plot()
fig.show()