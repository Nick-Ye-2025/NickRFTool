# 配置文件
# -*- coding: utf-8 -*-
# 配置文件：硬件地址、校准数据路径等

# 仪器地址
CMW500_ADDR = 'TCPIP0::192.168.10.20::INSTR'
TURNTABLE_ADDR = 'ASRL::/dev/ttyS0::INSTR'

# 手机控制端口
DIAG_PORT = '/dev/ttyUSB1'
DIAG_BAUDRATE = 115200

# 暗室校准数据路径
CHAMBER_CAL_FILES = {
    '800MHz': '射频测试自动化工具\非信令TRP测试\calibration\cal_800MHz.npy',
    '2.6GHz': '射频测试自动化工具\非信令TRP测试\calibration\cal_2.6GHz.npy'
}

# 测试参数
THETA_STEP = 15  # 水平角度步进(度)
PHI_ANGLES = [0, 90]  # 俯仰角度(度)
TEST_FREQUENCY = 2600  # MHz
TEST_BAND = 3  # LTE Band3