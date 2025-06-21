# 主程序入口
# -*- coding: utf-8 -*-
# 主程序入口
import time
import numpy as np
from chamber_controller import ChamberController
from device_controller import DeviceController
from trp_calculator import TRPCalculator
from config import THETA_STEP, PHI_ANGLES, TEST_FREQUENCY, TEST_BAND

def main():
    print("=== 非信令TRP测试系统启动 ===")
    
    # 初始化控制器
    chamber = ChamberController()
    device = DeviceController()
    trp_calculator = TRPCalculator()
    
    # 连接设备
    if not chamber.connect():
        print("仪器连接失败，终止测试")
        return
    
    if not device.connect():
        print("机台连接失败，终止测试")
        chamber.close()
        return
    
    try:
        # 设置测试参数
        theta_steps = np.arange(0, 360, THETA_STEP)
        power_readings = []
        test_details = []  # 存储详细测试数据
        
        # 配置仪器和手机
        chamber.setup_non_signaling(TEST_FREQUENCY, TEST_BAND)
        device.setup_non_signaling(TEST_FREQUENCY, TEST_BAND)
        
        print("开始TRP测试...")
        start_time = time.time()
        
        # 遍历所有角度
        for phi in PHI_ANGLES:
            for theta in theta_steps:
                # 设置转台角度
                chamber.set_angles(theta, phi)
                
                # 测量功率
                raw_power = chamber.measure_tx_power()
                if raw_power is None:
                    print(f"角度({theta},{phi})测量失败，跳过")
                    continue
                
                # 应用暗室校准
                cal_power = trp_calculator.apply_chamber_cal(
                    raw_power, theta, phi, TEST_FREQUENCY
                )
                
                # 记录结果
                power_readings.append(cal_power)
                test_details.append((phi, theta, cal_power))
                print(f"角度: θ={theta}°, φ={phi}° => 功率: {cal_power:.2f} dBm")
        
        # 计算TRP
        trp_value = trp_calculator.calculate_trp(power_readings, theta_steps, PHI_ANGLES)
        
        # 生成测试结果
        test_time = time.time() - start_time
        results = {
            'trp': trp_value,
            'frequency': TEST_FREQUENCY,
            'test_time': test_time,
            'details': test_details
        }
        
        print("\n测试完成!")
        print(f"TRP结果: {trp_value:.2f} dBm")
        print(f"总测试时间: {test_time:.2f} 秒")
        print(f"平均每个角度: {test_time/len(power_readings):.2f} 秒")
        
        # 生成报告
        trp_calculator.generate_report(results)
        
        # TODO: 这里可以添加结果上传MES系统的代码
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 清理资源
        device.close()
        chamber.close()

if __name__ == "__main__":
    main()