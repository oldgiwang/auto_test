import time
import os
import tempfile
import uiautomator2 as u2

class DeviceController:
    def __init__(self, device_id=None):
        """设备控制器，负责底层设备交互
        
        Args:
            device_id: 设备ID，默认使用连接的唯一设备
        """
        self.device_id = device_id
        self.temp_dir = tempfile.gettempdir()  # 使用系统临时目录
        self.device = None  # 初始化device属性
        self._connect_device()
    
    def _connect_device(self):
        """连接设备"""
        try:
            if self.device_id:
                self.device = u2.connect(self.device_id)
                print(f"正在连接设备: {self.device_id}")
            else:
                self.device = u2.connect()  # 默认连接
                print("正在连接默认设备")
            
            # 检查设备是否正常连接
            info = self.device.info
            print(f"设备连接正常: {info.get('productName', '未知设备')}")
        except Exception as e:
            print(f"设备连接失败: {str(e)}")
            raise Exception(f"设备连接失败，请检查uiautomator2连接: {str(e)}")
    
    def click(self, x, y):
        """点击屏幕坐标
        
        Args:
            x: x坐标
            y: y坐标
        """
        self.device.click(x, y)
        time.sleep(0.5)  # 等待UI响应
        print(f"点击坐标: ({x}, {y})")
    
    def long_press(self, x, y, duration=1.0):
        """长按屏幕坐标
        
        Args:
            x: x坐标
            y: y坐标
            duration: 持续时间(秒)
        """
        self.device.long_click(x, y, duration)
        time.sleep(0.5)  # 等待UI响应
        print(f"长按坐标: ({x}, {y}), 持续{duration}秒")
    
    def swipe(self, x1, y1, x2, y2, duration=0.5):
        """滑动屏幕
        
        Args:
            x1: 起始x坐标
            y1: 起始y坐标
            x2: 结束x坐标
            y2: 结束y坐标
            duration: 持续时间(秒)
        """
        self.device.swipe(x1, y1, x2, y2, duration=duration)
        time.sleep(0.5)  # 等待UI响应
        print(f"滑动: ({x1}, {y1}) -> ({x2}, {y2})")
    
    def input_text(self, text):
        """输入文本
        
        Args:
            text: 要输入的文本
        """
        self.device.send_keys(text)
        time.sleep(0.5)  # 等待UI响应
        print(f"输入文本: {text}")
    
    def press_key(self, keycode):
        """按下按键
        
        Args:
            keycode: 按键代码（如BACK, HOME）
        """
        try:
            # 处理特定键名
            if keycode == "KEYCODE_BACK" or keycode == "BACK":
                self.device.press("back")
            elif keycode == "KEYCODE_HOME" or keycode == "HOME":
                self.device.press("home")
            elif keycode == "KEYCODE_MENU" or keycode == "MENU":
                self.device.press("menu")
            elif keycode == "KEYCODE_POWER" or keycode == "POWER":
                self.device.press("power")
            elif keycode == "KEYCODE_VOLUME_UP" or keycode == "VOLUME_UP":
                self.device.press("volume_up")
            elif keycode == "KEYCODE_VOLUME_DOWN" or keycode == "VOLUME_DOWN":
                self.device.press("volume_down")
            elif keycode == "KEYCODE_DEL" or keycode == "DEL":
                self.device.press("delete")
            else:
                # 尝试直接使用keycode
                self.device.press(keycode)
            
            time.sleep(0.5)  # 等待UI响应
            print(f"按键: {keycode}")
        except Exception as e:
            print(f"按键操作失败 {keycode}: {e}")
    
    def get_screen_size(self):
        """获取屏幕尺寸
        
        Returns:
            (width, height): 屏幕尺寸元组
        """
        try:
            info = self.device.info
            width = info.get('displayWidth', 1080)
            height = info.get('displayHeight', 1920)
            return width, height
        except Exception as e:
            print(f"获取屏幕尺寸失败: {e}")
            # 默认值
            print("使用默认屏幕尺寸: 1080x1920")
            return 1080, 1920
    
    def dump_ui_hierarchy(self):
        """获取UI层次结构
        
        Returns:
            XML格式的UI层次结构
        """
        try:
            # 使用uiautomator2直接获取XML
            xml_content = self.device.dump_hierarchy()
            
            # 保存到本地文件
            xml_path = os.path.join("data", "element.xml")
            os.makedirs(os.path.dirname(xml_path), exist_ok=True)
            
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_content)
            
            print(f"已获取UI层次结构并保存到 {xml_path}")
            return xml_content
        except Exception as e:
            print(f"获取UI层次结构失败: {e}")
            
            # 尝试备用方法：截图并保存
            try:
                screenshot_path = os.path.join("data", "screen.png")
                self.device.screenshot(screenshot_path)
                print(f"已保存屏幕截图到 {screenshot_path}")
            except Exception as se:
                print(f"截图保存失败: {se}")
            
            return None
    
    def get_current_app_info(self):
        """获取当前应用信息
        
        Returns:
            包含应用包名和活动名的字典
        """
        try:
            current_app = self.device.app_current()
            app_info = {
                "current_package": current_app["package"],
                "current_activity": current_app.get("activity", ""),
                "device_info": self.device.info
            }
            return app_info
        except Exception as e:
            print(f"获取当前应用信息失败: {e}")
            return {}