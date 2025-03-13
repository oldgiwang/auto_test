import uiautomator2 as u2
import time
import os

class DeviceController:
    def __init__(self):
        """初始化设备控制器"""
        self.device = None
    
    def connect(self, device_id=None):
        """
        连接到设备
        
        参数:
            device_id: 可选的设备ID，如果为None则自动连接
            
        返回:
            连接成功返回True，否则返回False
        """
        try:
            self.device = u2.connect(device_id)
            return True
        except Exception as e:
            print(f"连接设备失败: {e}")
            return False
    
    def get_device(self):
        """获取当前设备对象"""
        return self.device
    
    def click(self, x, y):
        """点击屏幕上的坐标"""
        if self.device:
            self.device.click(x, y)
    
    def click_element(self, xpath):
        """点击匹配XPath的元素"""
        if self.device:
            self.device.xpath(xpath).click()
    
    def input_text(self, xpath, text):
        """向匹配XPath的输入框输入文本"""
        if self.device:
            self.device.xpath(xpath).set_text(text)
    
    def swipe(self, fx, fy, tx, ty, duration=0.5):
        """从一个点滑动到另一个点"""
        if self.device:
            self.device.swipe(fx, fy, tx, ty, duration=duration)
    
    def press_key(self, key):
        """按下特定键"""
        if self.device:
            self.device.press(key)
    
    def app_start(self, package_name):
        """启动应用"""
        if self.device:
            self.device.app_start(package_name)
    
    def app_stop(self, package_name):
        """停止应用"""
        if self.device:
            self.device.app_stop(package_name)
    
    def app_clear(self, package_name):
        """清除应用数据"""
        if self.device:
            self.device.app_clear(package_name)