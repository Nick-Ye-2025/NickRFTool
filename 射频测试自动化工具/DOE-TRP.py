import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# 生成球坐标网格 (θ, φ)
N_theta, N_phi = 90, 360
theta = np.linspace(0, np.pi, N_theta)  # 0~π
phi = np.linspace(0, 2*np.pi, N_phi)    # 0~2π
THETA, PHI = np.meshgrid(theta, phi, indexing='ij')

# 虚拟辐射模型 (两个热点)
def generate_radiation(θ, φ):
    # 正面左上角热点 (θ=π/4, φ=3π/4)
    front_hot = np.exp(-((θ - np.pi/4)**2/(0.3)**2 + (φ - 3*np.pi/4)**2/(0.4)**2))
    
    # 背面右上角热点 (θ=3π/4, φ=π/4)
    back_hot = np.exp(-((θ - 3*np.pi/4)**2/(0.3)**2 + (φ - np.pi/4)**2/(0.4)**2))
    
    # 合成辐射模式 (dBm)
    radiation = 10*np.log10(0.5*front_hot + 0.5*back_hot + 1e-6)
    return np.clip(radiation, -40, 10)  # 限制在-40~10dBm

dBm = generate_radiation(THETA, PHI)

# 转换为线性功率 (mW)
P_mW = 10**(dBm/10)

# 计算TRP
dθ = np.pi/(N_theta-1)
dφ = 2*np.pi/(N_phi-1)
dΩ = np.sin(THETA) * dθ * dφ  # 立体角微元

TRP_mW = np.sum(P_mW * dΩ)
TRP_dBm = 10*np.log10(TRP_mW)
print(f"Calculated TRP = {TRP_dBm:.2f} dBm")

# 投影函数：球坐标 → 直角坐标 (热力图投影)
def project_hemisphere(θ, φ, dBm):
    x = np.sin(θ) * np.cos(φ)
    y = np.sin(θ) * np.sin(φ)
    return x, y, dBm

# 分割正反面数据
front_mask = THETA <= np.pi/2
back_mask = THETA >= np.pi/2

# 正面投影
x_front, y_front, dBm_front = project_hemisphere(
    THETA[front_mask], 
    PHI[front_mask], 
    dBm[front_mask]
)

# 背面投影 (θ' = π - θ)
x_back, y_back, dBm_back = project_hemisphere(
    np.pi - THETA[back_mask],  # 关键：θ转换为θ'
    PHI[back_mask],
    dBm[back_mask]
)

# 创建红-蓝渐变色谱
cmap = LinearSegmentedColormap.from_list('custom_blue_red', [
    '#0000FF', '#0080FF', '#00FFFF', 
    '#FFFF00', '#FF8000', '#FF0000'
])

# 绘制热力图
plt.figure(figsize=(12, 5))

# 正面热力图
plt.subplot(121)
sc = plt.scatter(x_front, y_front, c=dBm_front, cmap=cmap, s=8, alpha=0.8)
plt.colorbar(sc, label='Radiation (dBm)')
plt.title('Front Radiation Pattern\n(Hotspot: Top-Left)')
plt.xlabel('X (Right)')
plt.ylabel('Y (Top)')
plt.grid(alpha=0.3)
plt.axis('equal')

# 背面热力图
plt.subplot(122)
sc = plt.scatter(x_back, y_back, c=dBm_back, cmap=cmap, s=8, alpha=0.8)
plt.colorbar(sc, label='Radiation (dBm)')
plt.title('Back Radiation Pattern\n(Hotspot: Top-Right)')
plt.xlabel('X (Right)')
plt.ylabel('Y (Top)')
plt.grid(alpha=0.3)
plt.axis('equal')

plt.tight_layout()
plt.savefig('antenna_radiation.png', dpi=300)
plt.show()