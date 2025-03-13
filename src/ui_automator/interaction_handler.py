import time
from typing import Dict, Any, Optional, Tuple, List

class InteractionHandler:
    """处理与UI元素的交互"""
    
    def __init__(self, device, element_dictionary):
        """
        初始化交互处理器
        
        参数:
            device: uiautomator2设备对象
            element_dictionary: 元素字典
        """
        self.device = device
        self.element_dictionary = element_dictionary
    
    def click_element(self, query: str, by: str = 'auto') -> bool:
        """
        点击匹配查询的元素
        
        参数:
            query: 元素查询字符串 (文本、ID等)
            by: 查询方式 ('text', 'resource_id', 'content_desc', 'auto')
            
        返回:
            点击成功返回True，否则返回False
        """
        element = self.element_dictionary.find_element(query, by)
        if element and element.get('clickable', False) and element.get('coords'):
            # 获取元素的中心坐标
            coords = element['coords']
            x, y = coords['center_x'], coords['center_y']
            
            print(f"点击元素: {element['name']} (坐标: {x}, {y})")
            
            # 点击元素
            self.device.click(x, y)
            time.sleep(0.5)  # 短暂等待UI响应
            return True
        else:
            if element:
                print(f"找到元素 '{query}' 但它不可点击或没有坐标")
            else:
                print(f"未找到元素 '{query}'")
            return False
    
    def input_text(self, query: str, text: str, by: str = 'auto') -> bool:
        """
        向匹配查询的输入框输入文本
        
        参数:
            query: 元素查询字符串
            text: 要输入的文本
            by: 查询方式
            
        返回:
            输入成功返回True，否则返回False
        """
        element = self.element_dictionary.find_element(query, by)
        if element and element.get('editable', False):
            # 首先点击元素，然后输入文本
            coords = element['coords']
            x, y = coords['center_x'], coords['center_y']
            
            print(f"在元素 '{element['name']}' 中输入文本: {text}")
            
            # 点击输入框
            self.device.click(x, y)
            time.sleep(0.5)  # 等待键盘弹出
            
            # 清除现有文本（可选）
            self.device.clear_text()
            
            # 输入文本
            self.device.send_keys(text)
            return True
        else:
            if element:
                print(f"找到元素 '{query}' 但它不是可编辑的")
            else:
                print(f"未找到元素 '{query}'")
            return False
    
    def check_element(self, query: str, by: str = 'auto') -> bool:
        """
        检查匹配查询的可选元素
        
        参数:
            query: 元素查询字符串
            by: 查询方式
            
        返回:
            勾选成功返回True，否则返回False
        """
        element = self.element_dictionary.find_element(query, by)
        if element and element.get('checkable', False):
            # 获取元素的中心坐标
            coords = element['coords']
            x, y = coords['center_x'], coords['center_y']
            
            print(f"勾选元素: {element['name']}")
            
            # 点击元素
            self.device.click(x, y)
            return True
        else:
            if element:
                print(f"找到元素 '{query}' 但它不可勾选")
            else:
                print(f"未找到元素 '{query}'")
            return False
    
    def swipe_screen(self, direction: str, speed: str = 'normal') -> bool:
        """
        在屏幕上滑动
        
        参数:
            direction: 方向 ('up', 'down', 'left', 'right')
            speed: 速度 ('slow', 'normal', 'fast')
            
        返回:
            滑动成功返回True
        """
        # 获取屏幕尺寸
        width, height = self.device.window_size()
        center_x, center_y = width // 2, height // 2
        
        # 确定滑动距离（基于屏幕尺寸的百分比）
        distance_factor = 0.5  # 默认滑动屏幕50%
        
        # 确定滑动时间（影响速度）
        duration_map = {
            'slow': 1.0,
            'normal': 0.5,
            'fast': 0.2
        }
        duration = duration_map.get(speed, 0.5)
        
        # 计算起点和终点
        if direction.lower() == 'up':
            start_x, start_y = center_x, int(height * 0.7)
            end_x, end_y = center_x, int(height * 0.3)
        elif direction.lower() == 'down':
            start_x, start_y = center_x, int(height * 0.3)
            end_x, end_y = center_x, int(height * 0.7)
        elif direction.lower() == 'left':
            start_x, start_y = int(width * 0.7), center_y
            end_x, end_y = int(width * 0.3), center_y
        elif direction.lower() == 'right':
            start_x, start_y = int(width * 0.3), center_y
            end_x, end_y = int(width * 0.7), center_y
        else:
            print(f"无效的滑动方向: {direction}")
            return False
        
        print(f"滑动屏幕: {direction} (速度: {speed})")
        
        # 执行滑动
        self.device.swipe(start_x, start_y, end_x, end_y, duration)
        return True
    
    def wait_for_element(self, query: str, by: str = 'auto', timeout: int = 10) -> bool:
        """
        等待元素出现
        
        参数:
            query: 元素查询字符串
            by: 查询方式
            timeout: 超时时间（秒）
            
        返回:
            元素出现返回True，超时返回False
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 先刷新元素字典（可选），确保获取最新的UI状态
            # self.element_dictionary.refresh()
            
            element = self.element_dictionary.find_element(query, by)
            if element and element.get('visible', False):
                print(f"元素 '{query}' 已出现")
                return True
                
            # 等待一段时间再检查
            time.sleep(0.5)
            
        print(f"等待元素 '{query}' 超时")
        return False
    
    def back(self) -> bool:
        """
        按返回键
        
        返回:
            总是返回True
        """
        print("按返回键")
        self.device.press("back")
        return True
    
    def home(self) -> bool:
        """
        按Home键
        
        返回:
            总是返回True
        """
        print("按Home键")
        self.device.press("home")
        return True
    
    def launch_app(self, package_name: str) -> bool:
        """
        启动应用
        
        参数:
            package_name: 应用包名
            
        返回:
            启动成功返回True
        """
        print(f"启动应用: {package_name}")
        try:
            self.device.app_start(package_name)
            return True
        except Exception as e:
            print(f"启动应用失败: {e}")
            return False
    
    def find_and_perform_action(self, action_type: str, target: str, **kwargs) -> bool:
        """
        根据动作类型和目标执行相应的操作
        
        参数:
            action_type: 动作类型 ('OPEN', 'CLICK', 'INPUT', 'SWIPE', 'CHECK')
            target: 目标元素或应用
            **kwargs: 额外参数
            
        返回:
            操作成功返回True，否则返回False
        """
        action_type = action_type.upper()
        
        if action_type == 'OPEN':
            # 判断是否是应用名，如果是应用名则尝试启动应用
            # 这里可以添加应用名与包名的映射表
            app_mapping = {
                '设置': 'com.android.settings',
                '短信': 'com.android.mms',
                '电话': 'com.android.dialer',
                '相机': 'com.android.camera',
                '图库': 'com.android.gallery',
                '浏览器': 'com.android.browser'
            }
            
            package_name = app_mapping.get(target)
            if package_name:
                return self.launch_app(package_name)
            else:
                # 尝试将目标解释为可点击元素
                return self.click_element(target)
                
        elif action_type == 'CLICK':
            return self.click_element(target)
            
        elif action_type == 'INPUT':
            text = kwargs.get('text', '')
            if not text:
                print("输入操作缺少文本参数")
                return False
            return self.input_text(target, text)
            
        elif action_type == 'SWIPE':
            direction = kwargs.get('direction', 'up').lower()
            return self.swipe_screen(direction)
            
        elif action_type == 'CHECK':
            return self.check_element(target)
            
        elif action_type == 'WAIT':
            timeout = kwargs.get('timeout', 10)
            return self.wait_for_element(target, timeout=timeout)
            
        elif action_type == 'BACK':
            return self.back()
            
        elif action_type == 'HOME':
            return self.home()
            
        else:
            print(f"不支持的动作类型: {action_type}")
            return False