from ctypes import *
import time

#数据包结构体，Data是储存数据的主要载体
class VCI_CAN_OBJ(Structure):
    _fields_ = [("ID", c_uint),
                ("TimeStamp", c_uint),
                ("TimeFlag", c_ubyte),
                ("SendType", c_ubyte),
                ("RemoteFlag", c_ubyte),
                ("ExternFlag", c_ubyte),
                ("DataLen", c_ubyte),
                ("Data", c_ubyte*8),
                ("Reserved", c_ubyte*3)
                ]

# 打包用到的结构体，每个成员是长度为2000的数组
# ID :数据返回时在CAN所带的ID标记
# byte0~7 :对应VCI_CAN_OBJ的Data中的8个整数
class Packed_Data(Structure):
    _fields_ = [("ID", c_ubyte*2000),
                ("byte0", c_ubyte*2000),
                ("byte1", c_ubyte*2000),
                ("byte2", c_ubyte*2000),
                ("byte3", c_ubyte*2000),
                ("byte4", c_ubyte*2000),
                ("byte5", c_ubyte*2000),
                ("byte6", c_ubyte*2000),
                ("byte7", c_ubyte*2000),
                ]

# 分类并打包用到的结构体，每个成员是长度为2000的数组
class Sorted_Data(Structure):
    _fields_ = [("ID", c_uint*2000),
                ("Time", c_ubyte * 2000),
                ("current_now", c_short*2000),# 当前电流 单位:0.1A
                ("voltage_now", c_short*2000),# 当前电压 单位:0.1V
                ("heart_beat", c_ubyte*2000),# 心跳包字节 每次发送+1
                ]

class CANIO:
    STATUS_OK = 1
    CANindex = 0
    mode = 2
    CANIOPDLLName = './lib/CANIOP.dll'
    ControlCANName = './lib/ControlCAN.dll'
    # C++封装后的调用（建议）
    CANIOP = 0# windll.LoadLibrary(CANIOPDLLName)
    # 官方原生调用（不建议）
    ControlCAN = 0# windll.LoadLibrary(ControlCANName)

    # 初始化CAN卡，将必要参数装入
    # CANindex : CAN卡的序号
    # 返回操作结果，1 = 成功，0 = 失败
    def __init__(self, CANindex = 0):
        self.ControlCAN = windll.LoadLibrary(self.ControlCANName)
        self.CANIOP = windll.LoadLibrary(self.CANIOPDLLName)
        self.CANindex = CANindex
        ret = self.CANIOP.initDevice(self.CANindex)
        if ret != self.STATUS_OK:
            print('初始化Device出错\r\n')
            # exit(666)

    # 析构函数，在销毁对象的时候完成断开连接操作
    def __del__(self):
        self.CANIOP.close(self.CANindex)

    # 初始化CAN卡的通道，默认0，CAN口的工作方式默认2
    # way_index :CAN口序号
    # mode = 0 :正常模式（相当于正常节点）
    # mode = 1 :只听模式（只接收，不影响总线）
    # mode = 2 :回环模式自发自收模式（环回模式）
    # accCode :验收码
    # accMask :屏蔽码, 推荐设置为0xFFFFFFFF，即全部接收
    # filter :滤波方式，0/1 = 接收所有类型 , 2 = 只接收标准帧 , 3 = 只接收扩展帧
    # Timing0, Timing1 用来表示波特率，默认250kbit
    # 返回操作结果，1 = 成功，0 = 失败
    def init_data_way(self,way_index = 0,
                      mode = 0,
                      accCode = 0x80000008,
                      accMask = 0xFFFFFFFF,
                      filter = 0,
                      Timing0 = 0x01,
                      Timing1 = 0x1C):
        self.way_index = way_index
        self.accCode = accCode
        self.accMask = accMask
        self.filter = filter
        self.Timing0 = Timing0
        self.Timing1 = Timing1
        self.mode = mode
        ret = self.CANIOP.initCANPort(self.CANindex, way_index, mode, accCode, accMask, filter, Timing0, Timing1)
        if ret != self.STATUS_OK:
            print('初始化CAN口出错\r\n')
        return ret

    # 原始的发送函数，需要传入已封装好的 vci_can_obj
    # vci_can_obj :要发送的数据包
    # way_index :CAN口序号
    # 返回操作结果，1 = 成功，0 = 失败
    def send0(self, vci_can_obj, way_index = 0):
        ret = self.CANIOP.send(byref(vci_can_obj), self.CANindex, way_index)
        return ret

    # 发送函数，由C++定义，对应手册的第一个传送协议
    # ID : 0x10203010(暂定)
    # device_reset :设备复位, 0：无效, 1：复位,
    # start_stop :设备启动/停止, 1：停机, 3：恒流启动, 4：恒功率, 5：恒阻,
    # special_command :特殊命令, 01:校准电压, 02:校准电流, 03:设置模块地址,
    # special_value :特殊命令参数
    #               命令01:实际电压值,
    #               命令02:实际电流值,
    #               命令03:设置的模块地址(设置模块地址命令时目标模块地址为广播地址且智能接一个模块),
    # addresss :目标模块地址, 地址值0是为广播地址,
    # way_index :CAN口序号,
    # remoteFlag :是否为远程帧,
    # externFlag :是否为扩展帧,
    # sendType :发送类型,默认1 = 不自动重发, 2 = 自动重发,
    # 返回操作结果，1 = 成功，0 = 失败
    def send11(self, ID, device_reset = 0,
               start_stop = 1,
               special_command = 0,
               special_value = 0,
               addresss = 0x10203010,
               way_index = 0,
               remoteFlag = 0,
               externFlag = 1,
               sendType = 1):
        ret = self.CANIOP.send1(ID, device_reset, start_stop, special_command, special_value, addresss, self.CANindex,way_index, remoteFlag, externFlag, sendType)
        return ret

    # 发送函数，由C++定义，对应手册的第二个传送协议
    # ID : 0x10203010(暂定)
    # voltage :电压给定值 单位:0.1V
    # current :电流给定值 单位:0.1A
    # power :功率给定值 单位:0.1kW
    # addresss :目标模块地址, 地址值0是为广播地址,
    # way_index :CAN口序号,
    # remoteFlag :是否为远程帧,
    # externFlag :是否为扩展帧,
    # sendType :发送类型,默认1 = 不自动重发, 2 = 自动重发,
    # 返回操作结果，1 = 成功，0 = 失败
    def send22(self, ID,
               voltage,
               current,
               power,
               addresss=0x10203010,
               way_index = 0,
               remoteFlag=0,
               externFlag=1,
               sendType=1):
        ret = self.CANIOP.send2(ID, voltage, current, power, addresss, self.CANindex, way_index, remoteFlag, externFlag, sendType)
        return ret

    # 发送函数，由C++定义，对应手册的第三个传送协议
    # ID : 0x10203012(暂定)
    # voltage_up :电压上限给定值 单位:0.1V
    # voltage_down :电压下限给定值 单位:0.1V
    # current_up :电流上限给定值 单位:0.1A
    # addresss :目标模块地址, 地址值0是为广播地址,
    # way_index :CAN口序号,
    # remoteFlag :是否为远程帧,
    # externFlag :是否为扩展帧,
    # sendType :发送类型,默认1 = 不自动重发, 2 = 自动重发,
    # 返回操作结果，1 = 成功，0 = 失败
    def send33(self, ID,
               voltage_up,
               voltage_down,
               current_up,
               addresss=0x10203012,
               way_index = 0,
               remoteFlag=0,
               externFlag=1,
               sendType=1):
        ret = self.CANIOP.send3(ID, voltage_up, voltage_down, current_up, addresss, self.CANindex, way_index, remoteFlag, externFlag, sendType)
        return ret

    # 发送函数，由C++定义，对应手册的第四个传送协议
    # ID : 0x10203010(暂定)
    # voltage_calibration :电压校准系数
    # current_calibration :电流校准系数
    # voltage_deviation :电压0点偏移
    # addresss :目标模块地址, 地址值0是为广播地址,
    # way_index :CAN口序号,
    # remoteFlag :是否为远程帧,
    # externFlag :是否为扩展帧,
    # sendType :发送类型,默认1 = 不自动重发, 2 = 自动重发,
    # 返回操作结果，1 = 成功，0 = 失败
    def send44(self, ID,
               voltage_calibration,
               current_calibration,
               voltage_deviation,
               addresss=0x10203010,
               way_index = 0,
               remoteFlag=0,
               externFlag=1,
               sendType=1):
        ret = self.CANIOP.send4(ID, voltage_calibration, current_calibration, voltage_deviation, addresss, self.CANindex, way_index, remoteFlag, externFlag, sendType)
        return ret

    # 接收函数，由C++定义
    # way_index :CAN口序号,
    # size :每次收取的数据条数
    # 返回打包后的数据
    def receive_Packed(self, way_index = 0, size = 2000):
        pdata = Packed_Data()
        self.CANIOP.receive0(byref(pdata),self.CANindex,way_index,size)
        return pdata

    # 接收函数，由C++定义
    # DevID1 : 第一个节点的id
    # way_index :CAN口序号,
    # size :每次收取的数据条数
    # 返回分类并打包后的数据
    def receive_Sorted(self,DevID1 , way_index = 0, size = 2000,alive = True):
        sdata = Sorted_Data()
        ret = self.CANIOP.receive1(DevID1, byref(sdata),self.CANindex,way_index,size)
        i = 0
        while ret < 0 and alive == True and i<3:
            time.sleep(1)
            self.CANIOP.close(self.CANindex)
            self.__init__(self.CANindex)
            self.init_data_way(self.way_index,
                      self.mode,
                      self.accCode,
                      self.accMask,
                      self.filter,
                      self.Timing0,
                      self.Timing1)
            ret = self.CANIOP.receive1(DevID1, byref(sdata), self.CANindex, way_index, size)
            i+=1
        return ret, sdata

    # 设置恒流模式
    # ID = 帧id
    # CANindex = CAN卡在计算机上的序号，一号为０
    # way_index = CAN口的序号，CAN1 = 0 , CAN2 = 1
    # RemoteFlag = 是否为远程帧
    # ExternFlag = 是否为扩展帧
    # SendType = 发送类型，为1时只发送一次，为0时一直发送直到发送成功(不推荐)
    def setCC(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setCC(ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置恒压模式
    def setCV(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setCV(ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置恒功率模式
    def setCP(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setCP(ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置恒阻模式
    def setCR(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setCR(ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置恒流模式的值
    # value = 值 , 单位0.1
    def setCCValue(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setCCValue(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置恒压模式的值
    # value = 值 , 单位0.1
    def setCVValue(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setCVValue(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置恒功率模式的值
    # value = 值 , 单位0.1
    def setCPValue(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setCPValue(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置恒阻模式的值
    # value = 值 , 单位0.1
    def setCRValue(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setCRValue(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 读取Ulim的值
    def readUlimValue(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.readUlimValue( ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置正弦波模式
    def setZX(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setZX( ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置三角波模式
    def setSJ(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setSJ( ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置方波模式
    def setFB(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setFB( ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置自定义模式
    def setZDY(self, ID, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setZDY( ID, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置正弦波频率
    # value = 值 , 单位1
    def setZXPL(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setZXPL(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置正弦波幅度
    # value = 值 , 单位0.1
    def setZXFD(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setZXFD(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置正弦波占空比
    # value = 值 , 单位1
    def setZXZKB(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setZXZKB(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置三角波频率
    # value = 值 , 单位1
    def setSJPL(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setSJPL(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置三角波幅度
    # value = 值 , 单位0.1
    def setSJFD(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setSJFD(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置三角波占空比
    # value = 值 , 单位1
    def setSJZKB(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setSJZKB(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置方波频率
    # value = 值 , 单位1
    def setFBPL(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setFBPL(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置方波幅度
    # value = 值 , 单位0.1
    def setFBFD(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setFBFD(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置方波占空比
    # value = 值 , 单位1
    def setFBZKB(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setFBZKB(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置Ulim的值
    # value = 值 , 单位0.01
    def setUlim(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setUlim(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置Ilim的值
    # value = 值 , 单位0.1
    def setIlim(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setIlim(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置电压的值
    # value = 值 , 单位0.01
    def setU(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setU(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置电流的值
    # value = 值 , 单位0.1
    def setI(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setI(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置电阻的值
    # value = 值 , 单位0.1
    def setR(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setR(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置功率的值
    # value = 值 , 单位1
    def setP(self, ID, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setP(ID, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置自定义方波电流
    # num = 序号 , 可选1 2 3 4 5 6 7
    # value = 值 , 单位0.1
    def setZDYFBCurrent(self, ID, num, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setZDYFBCurrent(ID, num, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)

    # 设置自定义方波周期
    # num = 序号 , 可选1 2 3 4 5 6 7
    # value = 值 , 单位0.1
    def setZDYFBT(self, ID, num, value, CANindex = 0, way_index = 0, RemoteFlag = 0, ExternFlag = 1, SendType = 1):
        return self.CANIOP.setZDYFBT(ID, num, value, CANindex, way_index, RemoteFlag, ExternFlag, SendType)
