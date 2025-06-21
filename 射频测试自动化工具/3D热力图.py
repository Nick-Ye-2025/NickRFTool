# 完整程序：T677射频测试与3D热力图可视化
import pyvisa
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import serial
from typing import List, Dict, Tuple

class T677Controller:
    def __init__(self, resource_name: str):
        """初始化T677控制器"""
        self.rm = pyvisa.ResourceManager()
        print("[NICK DEBUG] 正在扫描VISA设备...")
        available_res=self.rm.list_resources() #资源存在性检查
        print(f"[NICK DEBUG] 可用设备列表: {available_res}")
        if not available_res:
            raise RuntimeError("未检测到任何测试设备，请连接设备后重试")
        if resource_name not in available_res:
            raise ValueError(
                f"目标设备 {resource_name} 未连接\n"
                f"可用设备列表: {available_res}\n"
                "请检查以下可能原因:\n"
                "1. 设备电源未开启\n"
                "2. 连接线缆松动\n"
                "3. 驱动程序未正确安装"
            )
        try:
            self.instrument = self.rm.open_resource(resource_name)  #返回一个Instrument对象，提供 query() / write() 等方法进行仪器控制
            self.instrument.timeout = 10000  # 设置超时时间为10秒
            idn=self.instrument.query('*IDN?').strip()
            print(f"设备握手成功: {idn}")
        except pyvisa.VisaIOError as e:
            raise RuntimeError(
                f"设备连接异常: {resource_name}\n"
                f"错误详情: {str(e)}\n"
                "请检查设备连接状态和驱动程序"
            )

        # 初始化仪器
        self.instrument.write("*RST")  # 重置仪器  SCPI(Standard Commands for Programmable Instruments)标准命令
        self.instrument.write("*CLS")  # 清除状态寄存器
        error=self.instrument.query("SYST:ERR?").strip()  # 查询错误信息
        error_code,error_msg=error.split(',',1) if ',' in error else ('0',error)
        if (error_code)!='0':
            raise Exception(f"仪器初始化错误: 代码{error_code} - {error_msg}")
        print(f"仪器标识: {self.instrument.query('*IDN?').strip()}")
        print(f"已连接到仪器: {self.instrument.query('*IDN?')}") # 查询设备身份
    

    def close(self):
        """关闭与仪器的连接"""
        self.instrument.close()
    
    def configure_trp_test(self, frequency: float, power: float):
        """配置TRP测试参数"""
        self.instrument.write(f"FREQ {frequency}Hz")  # 设置频率
        self.instrument.write(f"POWER {power}dBm")  # 设置功率
        self.instrument.write("MEAS:TYPE TRP")  # 设置测量类型为TRP
        time.sleep(1)  # 等待仪器配置完成
    
    def configure_tis_test(self, frequency: float):
        """配置TIS测试参数"""
        self.instrument.write(f"FREQ {frequency}Hz")  # 设置频率
        self.instrument.write("MEAS:TYPE TIS")  # 设置测量类型为TIS
        time.sleep(1)  # 等待仪器配置完成
    
    def measure_trp(self) -> float:
        """执行TRP测量并返回结果"""
        self.instrument.write("INIT")  # 开始测量
        self.instrument.write("*WAI")  # 等待测量完成
        result = float(self.instrument.query("FETCH?").strip())
        return result
    
    def measure_tis(self) -> float:
        """执行TIS测量并返回结果"""
        self.instrument.write("INIT")  # 开始测量
        self.instrument.write("*WAI")  # 等待测量完成
        result = float(self.instrument.query("FETCH?").strip())
        return result

class HolderController:
    def __init__(self, port: str):
        """初始化Holder控制器"""
        self.ser = serial.Serial(port, baudrate=9600, timeout=1)
        print(f"已连接到Holder控制器: {port}")
    
    def close(self):
        """关闭与Holder控制器的连接"""
        self.ser.close()
    
    def rotate_to_angle(self, angle: float):
        """将Holder旋转到指定角度"""
        command = f"ROTATE {angle}\r\n"
        self.ser.write(command.encode())
        response = self.ser.readline().decode().strip()
        if response != "OK":
            raise Exception(f"Holder旋转失败，角度: {angle}, 响应: {response}")
        print(f"Holder已旋转到角度: {angle}°")

def perform_3d_rf_test(
    t677_controllers: List[T677Controller],
    holder_controller: HolderController,
    frequencies: List[float],
    azimuth_angles: List[float],
    elevation_angles: List[float]
) -> Dict[str, pd.DataFrame]:
    """执行3D射频测试，采集TRP和TIS数据"""
    # 初始化数据存储结构
    trp_data = []
    tis_data = []
    
    # 遍历所有频率点
    for freq in frequencies:
        print(f"\n正在测试频率: {freq/1e6} MHz")
        
        # 遍历所有方位角
        for azimuth in azimuth_angles:
            # 旋转Holder到指定方位角
            holder_controller.rotate_to_angle(azimuth)
            time.sleep(2)  # 等待Holder稳定
            
            # 遍历所有仰角（由不同的T677仪器覆盖）
            for elev_idx, elev in enumerate(elevation_angles):
                # 选择对应的T677仪器
                t677 = t677_controllers[elev_idx % len(t677_controllers)]
                
                # 配置并测量TRP
                t677.configure_trp_test(freq, power=23.0)  # 设置发射功率为23dBm
                trp = t677.measure_trp()
                
                # 配置并测量TIS
                t677.configure_tis_test(freq)
                tis = t677.measure_tis()
                
                # 存储数据
                trp_data.append({
                    "frequency": freq,
                    "azimuth": azimuth,
                    "elevation": elev,
                    "trp": trp
                })
                
                tis_data.append({
                    "frequency": freq,
                    "azimuth": azimuth,
                    "elevation": elev,
                    "tis": tis
                })
                
                print(f"频率: {freq/1e6} MHz, 方位角: {azimuth}°, 仰角: {elev}°, TRP: {trp:.2f} dBm, TIS: {tis:.2f} dBm")
    
    # 转换为DataFrame
    trp_df = pd.DataFrame(trp_data)
    tis_df = pd.DataFrame(tis_data)
    
    return {"trp": trp_df, "tis": tis_df}

def generate_3d_heatmap(data: pd.DataFrame, measurement_type: str, frequency: float = None):
    """生成3D热力图"""
    # 筛选特定频率的数据（如果指定）
    if frequency is not None:
        plot_data = data[data['frequency'] == frequency].copy()
        freq_mhz = frequency / 1e6
        title = f"{measurement_type.upper()} 3D热力图 ({freq_mhz} MHz)"
    else:
        plot_data = data.copy()
        title = f"{measurement_type.upper()} 3D热力图 (所有频率)"
    
    # 将角度转换为弧度
    plot_data['az_rad'] = np.radians(plot_data['azimuth'])
    plot_data['elev_rad'] = np.radians(plot_data['elevation'])
    
    # 计算3D坐标
    max_value = plot_data[measurement_type].max()
    min_value = plot_data[measurement_type].min()
    
    # 规范化数据用于颜色映射
    plot_data['norm_value'] = (plot_data[measurement_type] - min_value) / (max_value - min_value)
    
    # 计算3D坐标（球面坐标转笛卡尔坐标）
    plot_data['radius'] = 1 + 0.5 * plot_data['norm_value']  # 添加基线1，使最小值也能看到
    plot_data['x'] = plot_data['radius'] * np.cos(plot_data['az_rad']) * np.cos(plot_data['elev_rad'])
    plot_data['y'] = plot_data['radius'] * np.sin(plot_data['az_rad']) * np.cos(plot_data['elev_rad'])
    plot_data['z'] = plot_data['radius'] * np.sin(plot_data['elev_rad'])
    
    # 创建3D散点图
    fig = go.Figure(data=go.Scatter3d(
        x=plot_data['x'],
        y=plot_data['y'],
        z=plot_data['z'],
        mode='markers',
        marker=dict(
            size=8,
            color=plot_data[measurement_type],
            colorscale='Viridis',  # 可以选择其他颜色方案，如'Jet'或'RdBu'
            colorbar=dict(title=f'{measurement_type.upper()} (dBm)'),
            opacity=0.8
        ),
        text=[f"方位角: {az}°, 仰角: {elev}°, {measurement_type.upper()}: {val:.2f} dBm" 
              for az, elev, val in zip(plot_data['azimuth'], plot_data['elevation'], plot_data[measurement_type])]
    ))
    
    # 设置布局
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='cube'  # 保持坐标轴比例一致
        ),
        width=800,
        height=700,
        margin=dict(l=0, r=0, b=0, t=50)
    )
    
    # 添加球面网格以帮助理解3D空间
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x_sphere = np.cos(u) * np.sin(v)
    y_sphere = np.sin(u) * np.sin(v)
    z_sphere = np.cos(v)
    
    fig.add_trace(go.Surface(
        x=x_sphere, y=y_sphere, z=z_sphere,
        colorscale=[[0, 'rgba(200,200,200,0.1)'], [1, 'rgba(200,200,200,0.1)']],
        showscale=False,
        opacity=0.3
    ))
    
    return fig

def generate_comparison_heatmaps(trp_data: pd.DataFrame, tis_data: pd.DataFrame, frequency: float):
    """生成TRP和TIS的对比热力图"""
    # 创建子图
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'scatter3d'}, {'type': 'scatter3d'}]],
        subplot_titles=(f'TRP 3D热力图 ({frequency/1e6} MHz)', f'TIS 3D热力图 ({frequency/1e6} MHz)')
    )
    
    # 筛选特定频率的数据
    trp_plot_data = trp_data[trp_data['frequency'] == frequency].copy()
    tis_plot_data = tis_data[tis_data['frequency'] == frequency].copy()
    
    # 将角度转换为弧度
    trp_plot_data['az_rad'] = np.radians(trp_plot_data['azimuth'])
    trp_plot_data['elev_rad'] = np.radians(trp_plot_data['elevation'])
    tis_plot_data['az_rad'] = np.radians(tis_plot_data['azimuth'])
    tis_plot_data['elev_rad'] = np.radians(tis_plot_data['elevation'])
    
    # 计算3D坐标
    trp_max = trp_plot_data['trp'].max()
    trp_min = trp_plot_data['trp'].min()
    tis_max = tis_plot_data['tis'].max()
    tis_min = tis_plot_data['tis'].min()
    
    # 规范化数据用于颜色映射
    trp_plot_data['norm_value'] = (trp_plot_data['trp'] - trp_min) / (trp_max - trp_min)
    tis_plot_data['norm_value'] = (tis_plot_data['tis'] - tis_min) / (tis_max - tis_min)
    
    # 计算3D坐标（球面坐标转笛卡尔坐标）
    trp_plot_data['radius'] = 1 + 0.5 * trp_plot_data['norm_value']
    trp_plot_data['x'] = trp_plot_data['radius'] * np.cos(trp_plot_data['az_rad']) * np.cos(trp_plot_data['elev_rad'])
    trp_plot_data['y'] = trp_plot_data['radius'] * np.sin(trp_plot_data['az_rad']) * np.cos(trp_plot_data['elev_rad'])
    trp_plot_data['z'] = trp_plot_data['radius'] * np.sin(trp_plot_data['elev_rad'])
    
    tis_plot_data['radius'] = 1 + 0.5 * (1 - tis_plot_data['norm_value'])  # TIS越小越好，所以反转
    tis_plot_data['x'] = tis_plot_data['radius'] * np.cos(tis_plot_data['az_rad']) * np.cos(tis_plot_data['elev_rad'])
    tis_plot_data['y'] = tis_plot_data['radius'] * np.sin(tis_plot_data['az_rad']) * np.cos(tis_plot_data['elev_rad'])
    tis_plot_data['z'] = tis_plot_data['radius'] * np.sin(tis_plot_data['elev_rad'])
    
    # 添加TRP散点图
    fig.add_trace(
        go.Scatter3d(
            x=trp_plot_data['x'],
            y=trp_plot_data['y'],
            z=trp_plot_data['z'],
            mode='markers',
            marker=dict(
                size=8,
                color=trp_plot_data['trp'],
                colorscale='Viridis',
                colorbar=dict(title='TRP (dBm)'),
                opacity=0.8
            ),
            text=[f"方位角: {az}°, 仰角: {elev}°, TRP: {val:.2f} dBm" 
                  for az, elev, val in zip(trp_plot_data['azimuth'], trp_plot_data['elevation'], trp_plot_data['trp'])]
        ),
        row=1, col=1
    )
    
    # 添加TIS散点图
    fig.add_trace(
        go.Scatter3d(
            x=tis_plot_data['x'],
            y=tis_plot_data['y'],
            z=tis_plot_data['z'],
            mode='markers',
            marker=dict(
                size=8,
                color=tis_plot_data['tis'],
                colorscale='RdBu_r',  # 反转颜色方案，使越小的值越亮
                colorbar=dict(title='TIS (dBm)'),
                opacity=0.8
            ),
            text=[f"方位角: {az}°, 仰角: {elev}°, TIS: {val:.2f} dBm" 
                  for az, elev, val in zip(tis_plot_data['azimuth'], tis_plot_data['elevation'], tis_plot_data['tis'])]
        ),
        row=1, col=2
    )
    
    # 设置布局
    fig.update_layout(
        title=f'TRP和TIS 3D热力图对比 ({frequency/1e6} MHz)',
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
        ),
        width=1200,
        height=600,
        margin=dict(l=0, r=0, b=0, t=50)
    )
    
    # 添加球面网格
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x_sphere = np.cos(u) * np.sin(v)
    y_sphere = np.sin(u) * np.sin(v)
    z_sphere = np.cos(v)
    
    fig.add_trace(go.Surface(
        x=x_sphere, y=y_sphere, z=z_sphere,
        colorscale=[[0, 'rgba(200,200,200,0.1)'], [1, 'rgba(200,200,200,0.1)']],
        showscale=False,
        opacity=0.3
    ), row=1, col=1)
    
    fig.add_trace(go.Surface(
        x=x_sphere, y=y_sphere, z=z_sphere,
        colorscale=[[0, 'rgba(200,200,200,0.1)'], [1, 'rgba(200,200,200,0.1)']],
        showscale=False,
        opacity=0.3
    ), row=1, col=2)
    
    return fig

def main():
    """主函数：执行测试并生成可视化结果"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='T677射频测试与3D热力图可视化')
    parser.add_argument('--test', action='store_true', help='执行测试并采集数据')
    parser.add_argument('--visualize', action='store_true', help='生成可视化结果')
    parser.add_argument('--frequency', type=float, default=2450e6, help='测试频率 (Hz)，默认为2.45GHz')
    args = parser.parse_args()
    print(type(args))
    if args.test==False:
        print("请选择测试模式，使用 --test")
    print('[NICK DEBUG] args.test实际值:', args.test)
    # 测试参数
    frequencies = [args.frequency]  # 测试频率
    azimuth_angles = np.arange(0, 360, 15).tolist()  # 方位角从0到359度，间隔15度
    elevation_angles = [-30, 0, 30]  # 仰角覆盖-30°到+30°
    
    if args.test:
        print("[NICK DEBUG] 正在进入测试模式...")
        try:
            #打印当前系统检测到的设备
            rm = pyvisa.ResourceManager()
            print("[NICK DEBUG] 当前系统检测到的VISA设备:", rm.list_resources())
            
            print("[NICK DEBUG] 正在尝试连接T677仪器...")
            # 连接到T677仪器（假设有3台仪器覆盖不同仰角）
            t677_controllers = [
                T677Controller("GPIB0::18::INSTR"),  # 仰角-30°
                T677Controller("GPIB0::19::INSTR"),  # 仰角0°
                T677Controller("GPIB0::20::INSTR")   # 仰角+30°
            ]
            print("[NICK DEBUG] 正在尝试连接Holder控制器...")
            # 连接到Holder控制器
            holder_controller = HolderController("COM3")
        
            try:
                # 执行测试
                print("[NICK DEBUG] 开始执行测试流程...")
                test_results = perform_3d_rf_test(
                    t677_controllers, 
                    holder_controller, 
                    frequencies, 
                    azimuth_angles, 
                    elevation_angles
                )
                
                # 保存数据
                for meas_type, df in test_results.items():
                    df.to_csv(f"{meas_type}_data.csv", index=False)
                    print(f"{meas_type.upper()}数据已保存到 {meas_type}_data.csv")
                    
            finally:
                # 关闭所有连接
                print("[NICK DEBUG] 正在关闭所有设备连接...")
                for controller in t677_controllers:
                    controller.close()
                holder_controller.close()
                print("[NICK DEBUG] 所有连接已安全关闭")
    
        except Exception as e:
            print("\n[错误] 程序执行中断！以下是错误详情：")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("\n故障排查建议：")
            print("1. 确认所有测试设备电源已开启")
            print("2. 检查GPIB/USB连接线是否插紧")
            print("3. 验证设备地址是否正确（见下方检测到的设备列表）")
            print("4. 检查PyVISA驱动是否正确安装\n")
            raise  # 重新抛出异常以便查看完整堆栈跟踪

    if args.visualize:
        try:
            # 加载测试数据
            trp_data = pd.read_csv("trp_data.csv")
            tis_data = pd.read_csv("tis_data.csv")
            
            # 生成并显示单个热力图
            freq_to_plot = args.frequency
            
            trp_fig = generate_3d_heatmap(trp_data, "trp", freq_to_plot)
            trp_fig.show()
            
            tis_fig = generate_3d_heatmap(tis_data, "tis", freq_to_plot)
            tis_fig.show()
            
            # 生成并显示对比热力图
            comparison_fig = generate_comparison_heatmaps(trp_data, tis_data, freq_to_plot)
            comparison_fig.show()
            
            # 保存图表为HTML文件（可选）
            trp_fig.write_html("trp_heatmap.html")
            tis_fig.write_html("tis_heatmap.html")
            comparison_fig.write_html("trp_tis_comparison.html")
            print("热力图已保存为HTML文件")
            
        except FileNotFoundError:
            print("找不到数据文件，请先运行数据采集程序")

if __name__ == "__main__":
    main()