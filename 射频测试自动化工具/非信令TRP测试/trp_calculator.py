# TRP计算模块
# -*- coding: utf-8 -*-
# TRP计算模块

import numpy as np
import logging
from config import CHAMBER_CAL_FILES, THETA_STEP, PHI_ANGLES

class TRPCalculator:
    def __init__(self):
        self.cal_data = {}
        self.load_calibration_data()
        self.logger = logging.getLogger('TRPCalculator')
        
    def load_calibration_data(self):
        """加载暗室校准数据"""
        for freq_key, file_path in CHAMBER_CAL_FILES.items():
            try:
                self.cal_data[freq_key] = np.load(file_path)
                print(f"已加载校准数据: {freq_key}")
            except Exception as e:
                print(f"加载校准数据失败 ({freq_key}): {e}")
                # 创建空校准表
                num_phi = len(PHI_ANGLES)
                num_theta = 360 // THETA_STEP
                cal_matrix = np.zeros((num_phi, num_theta))
                cal_matrix += np.random.uniform(-0.5, 0.5, size=(num_phi, num_theta))
                np.save(r'd:\Nick\射频测试自动化工具\非信令TRP测试\calibration\cal_800MHz.npy', cal_matrix)
                np.save(r'd:\Nick\射频测试自动化工具\非信令TRP测试\calibration\cal_2.6GHz.npy', cal_matrix)
                # self.cal_data[freq_key] = np.zeros((num_phi, num_theta))
                

                
    def apply_chamber_cal(self, raw_power, theta, phi, freq):
        """应用暗室校准因子"""
        # 确定频率组
        freq_key = '800MHz' if freq < 1000 else '2.6GHz'
        cal_table = self.cal_data.get(freq_key)
        
        if cal_table is None:
            self.logger.warning(f"无 {freq_key} 校准数据，使用默认值")
            return raw_power
            
        # 计算角度索引
        theta_idx = int(theta // THETA_STEP) % cal_table.shape[1]
        phi_idx = PHI_ANGLES.index(phi) if phi in PHI_ANGLES else 0
        
        if phi_idx >= cal_table.shape[0]:
            phi_idx = 0
            
        # 获取校准因子 (dB)
        cal_factor = cal_table[phi_idx, theta_idx]
        
        # 应用校准 (mw转dBm计算)
        cal_power_mw = 10**(raw_power/10) * 10**(cal_factor/10)
        return 10 * np.log10(cal_power_mw)
        
    def calculate_trp(self, power_readings, theta_steps, phi_angles):
        """计算TRP值 (球面积分)"""
        # 重构为矩阵 [phi, theta]
        num_phi = len(phi_angles)
        num_theta = len(theta_steps)
        
        if len(power_readings) != num_phi * num_theta:
            raise ValueError("功率数据与角度设置不匹配")
            
        power_matrix = np.array(power_readings).reshape(num_phi, num_theta)
        
        # 角度转换为弧度
        theta_rad = np.deg2rad(theta_steps)
        d_theta = np.deg2rad(THETA_STEP)
        
        # 球面积分权重
        weights = np.sin(theta_rad) * d_theta * (2 * np.pi / num_theta)
        
        # 数值积分
        weighted_powers = np.sum(power_matrix * weights[np.newaxis, :], axis=1)
        avg_power = np.mean(weighted_powers)
        
        return 10 * np.log10(avg_power/1000)  # 转换为dBm
    
    def generate_report(self, results, filename="TRP_Report.txt"):
        """生成测试报告"""
        with open(filename, 'w') as f:
            f.write("TRP测试报告\n")
            f.write("="*50 + "\n")
            f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"频率: {TEST_FREQUENCY} MHz\n")
            f.write(f"TRP结果: {results['trp']:.2f} dBm\n\n")
            
            f.write("角度详细数据:\n")
            f.write("Phi\tTheta\tPower(dBm)\n")
            for phi, theta, power in results['details']:
                f.write(f"{phi}\t{theta}\t{power:.2f}\n")
                
        print(f"报告已生成: {filename}")
