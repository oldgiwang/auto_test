import time
from typing import Optional

class InteractionHandler:
    """简化版交互处理器，提供基本的UI交互功能"""
    
    def __init__(self, device):
        """
        初始化交互处理器
        
        参数:
            device: uiautomator2设备对象
        """
        self.device = device
        self.screen_width, self.screen_height = device.window_size()
        print(f"屏幕尺寸: {self.screen_width}x{self.screen_height}")
    
    def click(self, text: str) -> bool:
        """
        通过文本点击元素
        
        参数:
            text: 元素文本
            
        返回:
            点击成功返回True，否则返回False
        """
        try:
            print(f"尝试点击文本: '{text}'")
            # 多种查找方式，提高鲁棒性
            if self.device(text=text).exists:
                self.device(text=text).click()
                time.sleep(0.5)  # 等待UI响应
                return True
            elif self.device(description=text).exists:
                self.device(description=text).click()
                time.sleep(0.5)
                return True
            elif self.device(resourceId=text).exists:
                self.device(resourceId=text).click()
                time.sleep(0.5)
                return True
            else:
                print(f"找不到文本为 '{text}' 的元素")
                return False
        except Exception as e:
            print(f"点击元素 '{text}' 时出错: {e}")
            return False
    
    def click_by_xpath(self, xpath: str) -> bool:
        """
        通过XPath点击元素
        
        参数:
            xpath: 元素XPath
            
        返回:
            点击成功返回True，否则返回False
        """
        try:
            print(f"尝试通过XPath点击: '{xpath}'")
            if self.device.xpath(xpath).exists:
                self.device.xpath(xpath).click()
                time.sleep(0.5)  # 等待UI响应
                return True
            else:
                print(f"找不到XPath为 '{xpath}' 的元素")
                return False
        except Exception as e:
            print(f"通过XPath点击元素时出错: {e}")
            return False
    
    def click_by_coords(self, x: int, y: int) -> bool:
        """
        通过坐标点击
        
        参数:
            x: X坐标
            y: Y坐标
            
        返回:
            点击成功返回True，否则返回False
        """
        try:
            print(f"点击坐标: ({x}, {y})")
            self.device.click(x, y)
            time.sleep(0.5)  # 等待UI响应
            return True
        except Exception as e:
            print(f"点击坐标 ({x}, {y}) 时出错: {e}")
            return False
    
    def input_text(self, text: str, input_value: str) -> bool:
        """
        在输入框中输入文本
        
        参数:
            text: 输入框文本或描述
            input_value: 要输入的文本
            
        返回:
            输入成功返回True，否则返回False
        """
        try:
            print(f"尝试在 '{text}' 中输入: '{input_value}'")
            if self.device(text=text).exists:
                self.device(text=text).set_text(input_value)
                return True
            elif self.device(description=text).exists:
                self.device(description=text).set_text(input_value)
                return True
            elif self.device(resourceId=text).exists:
                self.device(resourceId=text).set_text(input_value)
                return True
            else:
                print(f"找不到 '{text}' 输入框")
                return False
        except Exception as e:
            print(f"输入文本时出错: {e}")
            return False
    
    def swipe(self, direction: str) -> bool:
        """
        滑动屏幕
        
        参数:
            direction: 滑动方向 ('up', 'down', 'left', 'right')
            
        返回:
            滑动成功返回True，否则返回False
        """
        try:
            direction = direction.lower()
            print(f"滑动屏幕: {direction}")
            
            # 获取屏幕尺寸
            width, height = self.device.window_size()
            center_x, center_y = width // 2, height // 2
            
            # 根据方向设置起点和终点
            if direction == 'up':
                self.device.swipe(center_x, center_y * 1.5, center_x, center_y * 0.5)
            elif direction == 'down':
                self.device.swipe(center_x, center_y * 0.5, center_x, center_y * 1.5)
            elif direction == 'left':
                self.device.swipe(center_x * 1.5, center_y, center_x * 0.5, center_y)
            elif direction == 'right':
                self.device.swipe(center_x * 0.5, center_y, center_x * 1.5, center_y)
            else:
                print(f"无效的滑动方向: {direction}")
                return False
                
            time.sleep(0.5)  # 等待UI响应
            return True
        except Exception as e:
            print(f"滑动屏幕时出错: {e}")
            return False
    
    def back(self) -> bool:
        """
        按返回键
        
        返回:
            操作成功返回True，否则返回False
        """
        try:
            print("按返回键")
            self.device.press("back")
            time.sleep(0.5)  # 等待UI响应
            return True
        except Exception as e:
            print(f"按返回键时出错: {e}")
            return False
    
    def home(self) -> bool:
        """
        回到主界面，优先使用Home键，失败时尝试手势
        
        返回:
            操作成功返回True，否则返回False
        """
        try:
            print("尝试通过Home键回到主界面")
            self.device.press("home")
            time.sleep(0.8)  # 等待UI响应
            
            # 检查是否成功回到主界面
            if self.is_on_home_screen():
                return True
                
            print("Home键可能失败，尝试通过手势回到主界面")
            # 从底部向上滑动（模拟手势导航）
            self.device.swipe(self.screen_width // 2, self.screen_height - 100, 
                              self.screen_width // 2, self.screen_height // 2, 
                              duration=0.3)
            time.sleep(0.8)
            
            if self.is_on_home_screen():
                return True
                
            # 再尝试一次不同的手势
            print("再次尝试不同手势")
            self.device.swipe(self.screen_width // 2, self.screen_height - 50, 
                              self.screen_width // 2, 100, 
                              duration=0.5)
            time.sleep(0.8)
            
            return self.is_on_home_screen()
        except Exception as e:
            print(f"回到主界面时出错: {e}")
            return False
    
    def is_on_home_screen(self) -> bool:
        """
        检查是否在主屏幕上
        
        返回:
            在主屏幕上返回True，否则返回False
        """
        # 检查常见的主屏幕标志
        try:
            # 检查常见的主屏幕元素
            home_indicators = [
                self.device(resourceId="com.miui.home:id/workspace").exists,
                self.device(resourceId="com.android.launcher3:id/workspace").exists,
                self.device(resourceId="com.google.android.apps.nexuslauncher:id/workspace").exists,
                # 检查底部的dock栏
                self.device(resourceId="com.miui.home:id/hotseat").exists,
                self.device(resourceId="com.android.launcher3:id/hotseat").exists
            ]
            
            if any(home_indicators):
                print("检测到主屏幕标志")
                return True
                
            print("未检测到主屏幕标志")
            return False
        except Exception as e:
            print(f"检查主屏幕时出错: {e}")
            return False
    
    def tap_back_gesture(self) -> bool:
        """
        执行返回手势（从左边缘向右滑动）
        
        返回:
            操作成功返回True，否则返回False
        """
        try:
            print("执行返回手势")
            self.device.swipe(10, self.screen_height // 2, 
                             self.screen_width // 3, self.screen_height // 2, 
                             duration=0.3)
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"执行返回手势时出错: {e}")
            return False