# 设备控制模块
# -*- coding: utf-8 -*-
# 设备控制模块

import serial
import time
from config import DIAG_PORT, DIAG_BAUDRATE

class DeviceController:
    def __init__(self):
        self.ser = None
        self.is_connected = False
        
    def connect(self):
        """连接手机诊断端口"""
        try:
            self.ser = serial.Serial(DIAG_PORT, DIAG_BAUDRATE, timeout=1)
            self.is_connected = True
            print("手机连接成功")
            return True
        except Exception as e:
            print(f"手机连接失败: {e}")
            return False
            
    def setup_non_signaling(self, freq, band, power_level=10):
        """设置非信令发射模式"""
        if not self.is_connected:
            raise ConnectionError("手机未连接")
        
        # 发送高通DIAG命令示例 (实际命令需参考芯片文档)
        commands = [
            f'RF_SET_TX_CONT_FREQ {band} {freq}',
            f'RF_SET_TX_POWER_LEVEL {power_level}',
            'RF_ENABLE_TX_CONT 1'
        ]
        
        for cmd in commands:
            self._send_command(cmd)
            
    def _send_command(self, command):
        """发送命令并获取响应"""
        self.ser.write((command + '\r').encode())
        time.sleep(0.1)  # 等待响应
        
        response = b''
        while self.ser.in_waiting > 0:
            response += self.ser.read(self.ser.in_waiting)
            time.sleep(0.1)
            
        decoded = response.decode(errors='ignore').strip()
        print(f"CMD: {command} -> RESP: {decoded}")
        
        if 'ERROR' in decoded or 'FAIL' in decoded:
            raise RuntimeError(f"命令失败: {command}")
            
        return decoded
        
    def close(self):
        """关闭连接"""
        if self.ser and self.ser.is_open:
            # 退出非信令模式
            try:
                self._send_command('RF_ENABLE_TX_CONT 0')
            except:
                pass
                
            self.ser.close()
        self.is_connected = False
        print("手机连接已关闭")