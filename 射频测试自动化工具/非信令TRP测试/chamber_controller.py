# 暗室仪器控制模块
# -*- coding: utf-8 -*-
# 暗室仪器控制模块

import pyvisa
import time
import numpy as np
from config import CMW500_ADDR, TURNTABLE_ADDR

class ChamberController:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.cmw = None
        self.turntable = None
        self.is_connected = False
        
    def connect(self):
        """连接仪器"""
        try:
            self.cmw = self.rm.open_resource(CMW500_ADDR)
            self.cmw.timeout = 10000  # 10秒超时
            self.turntable = self.rm.open_resource(TURNTABLE_ADDR)
            self.is_connected = True
            print("仪器连接成功")
            return True
        except Exception as e:
            print(f"仪器连接失败: {e}")
            return False
            
    def set_angles(self, theta, phi):
        """设置转台角度"""
        if not self.is_connected:
            raise ConnectionError("仪器未连接")
            
        # 设置俯仰角phi
        self.turntable.write(f'PHI {phi}')
        time.sleep(0.5)  # 等待稳定
        
        # 设置水平角theta
        self.turntable.write(f'THETA {theta}')
        time.sleep(0.5)
        
        # 等待转台到位
        while int(self.turntable.query('MOVING?')):
            time.sleep(0.1)
        
    def measure_tx_power(self):
        """测量发射功率（非信令模式）"""
        if not self.is_connected:
            raise ConnectionError("仪器未连接")
            
        self.cmw.write('INIT:IMM; *WAI')  # 触发测量并等待完成
        result_str = self.cmw.query('FETCH:NSIG:TX:POW?')
        
        try:
            # 假设返回格式为 "0.0, -23.4" (第一个值为主通道功率)
            power = float(result_str.split(',')[0])
            return power
        except:
            print(f"功率解析失败: {result_str}")
            return None
            
    def setup_non_signaling(self, freq, band):
        """配置测试仪非信令模式"""
        self.cmw.write('SYST:PRES')  # 重置仪器
        time.sleep(2)
        
        # 配置非信令模式
        self.cmw.write(f'CONF:NSIG:TX:FRAM CONT')  # 连续发射模式
        self.cmw.write(f'CONF:NSIG:TX:FREQ {freq}MHz')
        self.cmw.write('CONF:NSIG:TX:MOD QPSK')  # 固定调制方式
        self.cmw.write('CONF:NSIG:TX:POW:LEV MAX')  # 最大功率等级
        self.cmw.write('INIT:CONT ON')  # 连续测量模式
        
    def close(self):
        """关闭连接"""
        if self.cmw:
            self.cmw.close()
        if self.turntable:
            self.turntable.close()
        self.is_connected = False
        print("仪器连接已关闭")