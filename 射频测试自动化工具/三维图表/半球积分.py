import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.gridspec as gridspec

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei"] #"WenQuanYi Micro Hei", "Heiti TC"
plt.rcParams["axes.unicode_minus"] = False  # 正确显示负号

class Arrow3D(FancyArrowPatch):
    """用于在3D空间中绘制箭头的辅助类"""
    def __init__(self, xs, ys, zs, *args, **kwargs):
        super().__init__((0, 0), (0, 0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def do_3d_projection(self, renderer=None):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
        self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
        return np.min(zs)

class TRPVisualizer:
    def __init__(self, antenna='A'):
        """初始化TRP可视化工具，支持不同天线发射"""
        self.antenna = antenna
        self.antenna_positions = {
            'A': {'x': -0.3, 'y': 0, 'z': 0.3},  # 左上角
            'B': {'x': 0.3, 'y': 0, 'z': 0.3},   # 右上角
            'C': {'x': 0.3, 'y': 0, 'z': -0.3},  # 右下角
            'D': {'x': -0.3, 'y': 0, 'z': -0.3}  # 左下角
        }
        self.phone_size = {
            'width': 0.6,   # X轴方向 (左右)
            'height': 1.2,  # Z轴方向 (上下)
            'thickness': 0.1 # Y轴方向 (前后)
        }
        self.density = 50  # 采样密度
        
    def generate_samples(self):
        """生成球面采样点数据"""
        samples = []
        num_points = self.density * self.density
        
        for i in range(num_points):
            # 黄金螺旋算法生成均匀分布的球面点
            y = 1 - (i / (num_points - 1)) * 2  # y从1到-1
            radius = np.sqrt(1 - y * y)  # 半径
            
            # 黄金角
            theta = 2 * np.pi * i * 0.618033988749895
            
            x = np.cos(theta) * radius
            z = np.sin(theta) * radius
            
            # 转换为球坐标
            r = 1.0  # 单位球
            phi = np.arctan2(z, x)  # 方位角
            theta_sphere = np.arccos(y)  # 天顶角
            
            # 计算信号强度（基于天线位置）
            dbm = self.calculate_signal_strength(theta_sphere, phi)
            
            samples.append({
                'x': x, 'y': y, 'z': z,
                'r': r, 'theta': theta_sphere, 'phi': phi,
                'dbm': dbm
            })
            
        return samples
    
    def calculate_signal_strength(self, theta, phi):
        """计算指定方向的信号强度，离天线越近信号越强"""
        pos = self.antenna_positions[self.antenna]
        ant_x, ant_y, ant_z = pos['x'], pos['y'], pos['z']
        
        # 天线位置转换为球坐标
        ant_r = np.sqrt(ant_x**2 + ant_y**2 + ant_z**2)
        ant_theta = np.arccos(ant_z / ant_r)
        ant_phi = np.arctan2(ant_y, ant_x)
        
        # 计算角距离
        angular_distance = np.arccos(
            np.sin(theta) * np.sin(ant_theta) * np.cos(phi - ant_phi) + 
            np.cos(theta) * np.cos(ant_theta)
        )
        
        # 信号强度计算（距离越近越强）
        dbm = -40 + 45 * np.exp(-8 * angular_distance)
        dbm += np.random.uniform(-2, 2)  # 添加随机噪声
        dbm = max(-40, min(0, dbm))  # 限制在[-40, 0]dBm范围内
        
        return dbm
    
    def calculate_trp(self, samples, half_sphere=False):
        """计算TRP值，half_sphere=True时只计算半圆区域"""
        if not samples:
            return -np.inf
            
        delta_theta = np.pi / (self.density - 1)
        delta_phi = 2 * np.pi / (self.density - 1)
        
        trp = 0
        for point in samples:
            # 筛选半圆区域（X>0）
            if half_sphere and point['x'] <= 0:
                continue
                
            sin_theta = np.sin(point['theta'])
            linear_power = 10 ** (point['dbm'] / 10)  # dBm转线性功率
            trp += linear_power * sin_theta * delta_theta * delta_phi
            
        return 10 * np.log10(trp) if trp > 0 else -np.inf  # 转回dBm
    
    def visualize(self):
        """可视化所有图表"""
        # 生成样本数据
        samples = self.generate_samples()
        
        # 计算TRP值
        total_trp = self.calculate_trp(samples)
        half_sphere_trp = self.calculate_trp(samples, half_sphere=True)
        
        print(f"总TRP值: {total_trp:.2f} dBm")
        print(f"半圆TRP值: {half_sphere_trp:.2f} dBm")
        
        # 创建一个大图
        fig = plt.figure(figsize=(18, 15))
        
        # 使用gridspec创建布局
        gs = gridspec.GridSpec(2, 2, figure=fig, wspace=0.2, hspace=0.3)
        
        # 全球面热力图
        ax1 = fig.add_subplot(gs[0, 0])
        self.plot_heatmap(ax1, samples, "全球面辐射热力图")
        
        # 3D球面图
        ax3 = fig.add_subplot(gs[0,1], projection='3d')
        self.plot_3d_sphere(ax3, samples)
        
        # 坐标系定义
        ax4 = fig.add_subplot(gs[1, 0], projection='3d')
        self.plot_coordinate_system(ax4)
        
        # TRP值对比
        ax5 = fig.add_subplot(gs[1, 1])
        self.plot_trp_comparison(ax5, total_trp)
        
        # 添加主标题
        fig.suptitle(f'天线 {self.antenna} 辐射模式与TRP可视化', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92)  # 为suptitle留出空间
        plt.show()
    
    def plot_heatmap(self, ax, samples, title, half_sphere=False):
        """绘制2D热力图"""
        # 筛选数据
        if half_sphere:
            data = [p for p in samples if p['x'] > 0]
        else:
            data = samples
            
        # 提取坐标和信号强度
        x = [p['x'] for p in data]
        y = [p['y'] for p in data]
        dbm = [p['dbm'] for p in data]

        # 在热力图中添加手机轮廓
        phone = plt.Rectangle((-0.3, -0.6), 0.6, 1.2, 
                                    edgecolor='gray', linewidth=2,
                                    facecolor='none', zorder=10)
        ax.add_patch(phone)
        ax.text(0, -0.7, '手机正面(Y方向)', ha='center', va='top', color='gray')

        # 创建颜色映射（蓝到红）
        cmap = LinearSegmentedColormap.from_list('blue_to_red', ['#3B82F6', '#EF4444'])
        
        # 绘制散点图，颜色和大小随信号强度变化
        scatter = ax.scatter(x, y, c=dbm, s=(np.array(dbm) + 40) * 15, 
                            cmap=cmap, alpha=0.8, edgecolors='none')
        
        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('信号强度 (dBm)', fontsize=12)
        
        # 绘制天线位置
        ant_pos = self.antenna_positions[self.antenna]
        ax.scatter(ant_pos['x'], ant_pos['y'], s=200, c='yellow', marker='*', label='天线位置')
        
        # 设置坐标轴和标题
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal')
        ax.set_xlabel('X轴（垂直手机正面）', fontsize=12)
        ax.set_ylabel('Y轴（平行手机右侧）', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def plot_3d_sphere(self, ax, samples):
        # 在3D图中添加手机框架
        self._draw_3d_phone(ax)
        """绘制3D球面辐射分布"""
        # 提取坐标和信号强度
        x = [p['x'] for p in samples]
        y = [p['y'] for p in samples]
        z = [p['z'] for p in samples]
        dbm = [p['dbm'] for p in samples]
        
        # 创建颜色映射
        cmap = LinearSegmentedColormap.from_list('blue_to_red', ['#3B82F6', '#EF4444'])
        
        # 绘制3D散点图
        scatter = ax.scatter(x, y, z, c=dbm, s=(np.array(dbm) + 40) * 10,
                            cmap=cmap, alpha=0.7, edgecolors='none')
        
        # 绘制天线位置
        ant_pos = self.antenna_positions[self.antenna]
        ax.scatter(ant_pos['x'], ant_pos['y'], ant_pos['z'], s=300, c='yellow', 
                  marker='*', label='天线位置')
        
        # 设置坐标轴标签
        ax.set_xlabel('X轴（垂直手机正面）', fontsize=12)
        ax.set_ylabel('Y轴（平行手机右侧）', fontsize=12)
        ax.set_zlabel('Z轴（平行手机顶部）', fontsize=12)
        ax.set_title('3D球面辐射分布', fontsize=14, fontweight='bold')
        
        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax, pad=0.1)
        cbar.set_label('信号强度 (dBm)', fontsize=12)
        
        # 设置视角
        ax.view_init(elev=30, azim=45)
    
    def plot_coordinate_system(self, ax):
        # 绘制更详细的手机模型
        self._draw_3d_phone(ax, detailed=True)

        """绘制坐标系定义示意图"""
        # 绘制坐标轴
        a = Arrow3D([0, 1], [0, 0], [0, 0], mutation_scale=20,  # X轴
                  lw=2, arrowstyle="-|>", color="r")
        ax.add_artist(a)
    
        a = Arrow3D([0, 0], [0, 1], [0, 0], mutation_scale=20,  # Y轴
                  lw=2, arrowstyle="-|>", color="g")
        ax.add_artist(a)
    
        a = Arrow3D([0, 0], [0, 0], [0, 1], mutation_scale=20,  # Z轴
                  lw=2, arrowstyle="-|>", color="b")
        ax.add_artist(a)
        
        # 添加坐标轴标签
        ax.text(1.1, 0, 0, "X轴", color='red')
        ax.text(0, 1.1, 0, "Y轴", color='green')
        ax.text(0, 0, 1.1, "Z轴", color='blue')
        
        # 绘制手机示意图
        x = [-0.5, 0.5, 0.5, -0.5, -0.5]
        y = [-0.3, -0.3, 0.3, 0.3, -0.3]
        z = [0, 0, 0, 0, 0]
        ax.plot(x, y, z, 'gray', alpha=0.5)
        
        # 绘制半圆区域
        theta = np.linspace(0, np.pi, 100)
        phi = np.linspace(0, np.pi/2, 100)
        theta, phi = np.meshgrid(theta, phi)
        
        x = 0.6 * np.sin(phi) * np.cos(theta)
        y = 0.6 * np.sin(phi) * np.sin(theta)
        z = 0.6 * np.cos(phi)
        
        ax.plot_surface(x, y, z, color='blue', alpha=0.1)
        
        # 设置坐标轴范围
        ax.set_xlim([-1.1, 1.1])
        ax.set_ylim([-1.1, 1.1])
        ax.set_zlim([-1.1, 1.1])
        
        # 设置标题
        ax.set_title('坐标系定义', fontsize=14, fontweight='bold')
        
        # 隐藏坐标轴刻度
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        
        # 设置视角
        ax.view_init(elev=20, azim=-45)
        ax.set_xlim([-1,1])
        ax.set_ylim([-1,1])
        ax.set_zlim([-1,1])
    
    def plot_trp_comparison(self, ax, total_trp):
        """绘制TRP值对比图"""
        # 数据
        trp_values = [total_trp]
        labels = ['全球面TRP', '正面半球TRP']
        colors = ['#3B82F6', '#EF4444']
        
        # 绘制条形图
        bars = ax.bar(labels, trp_values, color=colors, alpha=0.7)
        
        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.2f} dBm', ha='center', va='bottom')
        
        # 设置标题和标签
        ax.set_title('TRP值对比', fontsize=14, fontweight='bold')
        ax.set_ylabel('TRP (dBm)', fontsize=12)
        
        # 设置Y轴范围
        ax.set_ylim(min(trp_values) - 5, max(trp_values) + 5)
        
        # 添加网格线
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    def _draw_3d_phone(self, ax, detailed=False):
        """绘制直立手机模型"""
        w = self.phone_size['width']
        h = self.phone_size['height']
        t = self.phone_size['thickness']

        # 手机框架(X-Z平面)
        x = [-w/2, w/2, w/2, -w/2, -w/2]
        y = [0]*5
        z = [-h/2, -h/2, h/2, h/2, -h/2]
        ax.plot(x, y, z, 'gray', linewidth=2)

        # 添加厚度维度(Y轴方向)
        if detailed:
            # 绘制侧面
            ax.plot([w/2, w/2], [t/2, t/2], [-h/2, h/2], 'gray')
            # 添加文字标注
            ax.text(0, 0, h/2*1.1, '手机顶部', 
                   ha='center', va='bottom', color='gray')
            ax.text(0, 0, -h/2*1.1, '手机底部', 
                   ha='center', va='top', color='gray')

    def plot_trp_single(self, ax, total_trp):
        """单值TRP显示"""
        ax.text(0.5, 0.7, f'总TRP值: {total_trp:.2f} dBm', 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
# 使用示例
if __name__ == "__main__":
    # 可视化天线A的辐射模式
    visualizer = TRPVisualizer(antenna='A')
    visualizer.visualize()
    
    # 也可以切换到其他天线
    # visualizer = TRPVisualizer(antenna='B')
    # visualizer.visualize()