import time

class InteractionHandler:
    def __init__(self, device_controller, element_parser):
        """交互处理器，提供高级交互功能
        
        Args:
            device_controller: 设备控制器实例
            element_parser: 元素解析器实例
        """
        self.device_controller = device_controller
        self.element_parser = element_parser
        self.device = device_controller.device  # 直接使用u2设备对象
    
    def click_by_text(self, text, exact_match=True, retry=3):
        """通过文本点击元素
        
        Args:
            text: 要点击的元素文本
            exact_match: 是否精确匹配
            retry: 重试次数
        """
        for i in range(retry):
            try:
                # 使用元素解析器查找元素，会自动处理不可点击元素的情况
                element_info = self.element_parser.find_element_by_text(text, exact_match)
                
                if element_info:
                    # 直接点击元素中心坐标
                    center_x = element_info["bounds"]["center_x"]
                    center_y = element_info["bounds"]["center_y"]
                    
                    # 使用设备控制器执行点击，确保模拟真实点击
                    self.device_controller.click(center_x, center_y)
                    print(f"点击文本元素: '{text}' 坐标: ({center_x}, {center_y})")
                    
                    # 给UI一些响应时间
                    time.sleep(1)
                    return True
                
                # 未找到元素，等待后重试
                print(f"未找到文本为 '{text}' 的元素，等待后重试 ({i+1}/{retry})")
                time.sleep(1)
            except Exception as e:
                print(f"点击文本元素时发生错误: {e}, 重试 ({i+1}/{retry})")
                time.sleep(1)
        
        print(f"未能找到文本为 '{text}' 的元素")
        return False
    
    def click_by_id(self, resource_id, retry=3):
        """通过资源ID点击元素
        
        Args:
            resource_id: 资源ID
            retry: 重试次数
        """
        for i in range(retry):
            try:
                # 使用元素解析器查找元素，会自动处理不可点击元素的情况
                element_info = self.element_parser.find_element_by_id(resource_id)
                
                if element_info:
                    # 直接点击元素中心坐标
                    center_x = element_info["bounds"]["center_x"]
                    center_y = element_info["bounds"]["center_y"]
                    
                    # 使用设备控制器执行点击，确保模拟真实点击
                    self.device_controller.click(center_x, center_y)
                    print(f"点击ID元素: '{resource_id}' 坐标: ({center_x}, {center_y})")
                    
                    # 给UI一些响应时间
                    time.sleep(1)
                    return True
                
                # 未找到元素，等待后重试
                print(f"未找到ID为 '{resource_id}' 的元素，等待后重试 ({i+1}/{retry})")
                time.sleep(1)
            except Exception as e:
                print(f"点击ID元素时发生错误: {e}, 重试 ({i+1}/{retry})")
                time.sleep(1)
        
        print(f"未能找到ID为 '{resource_id}' 的元素")
        return False
    
    def input_text_to_field(self, field_text=None, field_id=None, input_text=""):
        """向输入框输入文本
        
        Args:
            field_text: 输入框文本标识
            field_id: 输入框资源ID
            input_text: 要输入的文本
        """
        try:
            element_info = None
            
            # 根据文本或ID查找元素
            if field_text:
                element_info = self.element_parser.find_element_by_text(field_text)
            elif field_id:
                element_info = self.element_parser.find_element_by_id(field_id)
            
            if not element_info:
                print("未找到指定的输入框")
                return False
            
            # 获取元素中心坐标
            center_x = element_info["bounds"]["center_x"]
            center_y = element_info["bounds"]["center_y"]
            
            # 点击获取焦点
            self.device_controller.click(center_x, center_y)
            time.sleep(0.5)
            
            # 清空现有文本 (使用长按和删除)
            self.device_controller.long_press(center_x, center_y, 1.0)
            time.sleep(0.5)
            
            # 点击"全选"选项 (如果可见)
            try:
                select_all = self.device(text="全选")
                if select_all.exists:
                    select_all.click()
                    time.sleep(0.3)
            except Exception:
                # 忽略错误，继续尝试删除
                pass
            
            # 点击删除按钮
            self.device_controller.press_key("DEL")
            time.sleep(0.5)
            
            # 输入新文本
            self.device_controller.input_text(input_text)
            print(f"向输入框输入文本: '{input_text}'")
            return True
        
        except Exception as e:
            print(f"输入文本时发生错误: {e}")
            return False
    
    def scroll_down(self):
        """向下滚动屏幕"""
        try:
            # 获取屏幕尺寸
            width, height = self.device_controller.get_screen_size()
            start_x = width // 2
            start_y = height * 2 // 3
            end_y = height // 3
            
            # 执行滚动手势
            print("执行向下滚动手势...")
            self.device_controller.swipe(start_x, start_y, start_x, end_y)
            time.sleep(1)  # 等待滚动完成和UI响应
            print("屏幕向下滚动完成")
            return True
        except Exception as e:
            print(f"向下滚动屏幕时发生错误: {e}")
            return False
    
    def scroll_up(self):
        """向上滚动屏幕"""
        try:
            # 获取屏幕尺寸
            width, height = self.device_controller.get_screen_size()
            start_x = width // 2
            start_y = height // 3
            end_y = height * 2 // 3
            
            # 执行滚动手势
            print("执行向上滚动手势...")
            self.device_controller.swipe(start_x, start_y, start_x, end_y)
            time.sleep(1)  # 等待滚动完成和UI响应
            print("屏幕向上滚动完成")
            return True
        except Exception as e:
            print(f"向上滚动屏幕时发生错误: {e}")
            return False
    
    def scroll_horizontal(self, direction="right_to_left"):
        """水平滚动屏幕
        
        Args:
            direction: 滚动方向，"right_to_left"或"left_to_right"
        """
        try:
            # 获取屏幕尺寸
            width, height = self.device_controller.get_screen_size()
            start_y = height // 2
            
            if direction == "right_to_left":  # 向左滑动（从右向左）
                start_x = width * 3 // 4
                end_x = width // 4
                print("执行从右向左的水平滚动...")
            else:  # 向右滑动（从左向右）
                start_x = width // 4
                end_x = width * 3 // 4
                print("执行从左向右的水平滚动...")
            
            # 执行滚动手势
            self.device_controller.swipe(start_x, start_y, end_x, start_y)
            time.sleep(1)  # 等待滚动完成和UI响应
            print("水平滚动完成")
            return True
        except Exception as e:
            print(f"水平滚动屏幕时发生错误: {e}")
            return False
    
    def find_and_click_element(self, target_text=None, target_id=None, scroll_attempts=3):
        """查找并点击元素，如需要会滚动查找
        
        Args:
            target_text: 目标文本
            target_id: 目标ID
            scroll_attempts: 滚动尝试次数
        """
        # 获取当前页面信息，确定滚动方向
        _, app_info = self.element_parser.parse_ui_hierarchy()
        scroll_direction = app_info.get("recommended_scroll", "vertical")
        
        # 先尝试直接查找
        if target_text:
            if self.click_by_text(target_text):
                return True
        elif target_id:
            if self.click_by_id(target_id):
                return True
        
        print(f"未直接找到元素，开始尝试滚动查找，推荐滚动方向: {scroll_direction}")
        
        # 根据推荐的滚动方向执行滚动查找
        for i in range(scroll_attempts):
            if scroll_direction == "horizontal":
                # 尝试水平滚动
                self.scroll_horizontal("right_to_left")
            else:
                # 默认垂直滚动
                self.scroll_down()
            
            time.sleep(1)  # 等待滚动完成和UI响应
            
            # 尝试查找元素
            if target_text:
                if self.click_by_text(target_text):
                    return True
            elif target_id:
                if self.click_by_id(target_id):
                    return True
            
            print(f"滚动后未找到元素，继续尝试 ({i+1}/{scroll_attempts})")
        
        # 恢复屏幕位置
        for i in range(min(scroll_attempts, 2)):  # 最多恢复2次，避免过度滚动
            if scroll_direction == "horizontal":
                self.scroll_horizontal("left_to_right")
            else:
                self.scroll_up()
            time.sleep(0.5)
        
        print(f"未能找到并点击元素: {target_text or target_id}")
        return False
    
    def go_back(self):
        """返回上一页"""
        try:
            # 使用设备的BACK键
            self.device_controller.press_key("BACK")
            print("返回上一页")
            time.sleep(1)  # 等待页面切换
            return True
        except Exception as e:
            print(f"返回上一页失败: {e}")
            return False
    
    def go_home(self):
        """返回主屏幕"""
        try:
            # 使用设备的HOME键
            self.device_controller.press_key("HOME")
            print("返回主屏幕")
            time.sleep(1)  # 等待页面切换
            return True
        except Exception as e:
            print(f"返回主屏幕失败: {e}")
            return False
    
    def wait(self, seconds):
        """等待指定秒数
        
        Args:
            seconds: 等待秒数
        """
        print(f"等待 {seconds} 秒")
        time.sleep(seconds)
        return True
    
    def click_if_exists(self, target_text=None, target_id=None):
        """如果元素存在则点击，不存在则跳过
        
        Args:
            target_text: 目标文本
            target_id: 目标ID
        """
        if target_text:
            element_info = self.element_parser.find_element_by_text(target_text)
            if element_info:
                center_x = element_info["bounds"]["center_x"]
                center_y = element_info["bounds"]["center_y"]
                self.device_controller.click(center_x, center_y)
                print(f"点击存在的文本元素: '{target_text}'")
                time.sleep(0.5)
                return True
            else:
                print(f"文本元素 '{target_text}' 不存在，跳过点击")
        
        elif target_id:
            element_info = self.element_parser.find_element_by_id(target_id)
            if element_info:
                center_x = element_info["bounds"]["center_x"]
                center_y = element_info["bounds"]["center_y"]
                self.device_controller.click(center_x, center_y)
                print(f"点击存在的ID元素: '{target_id}'")
                time.sleep(0.5)
                return True
            else:
                print(f"ID元素 '{target_id}' 不存在，跳过点击")
        
        return False
    
    def wait_element(self, target_text=None, target_id=None, timeout=10):
        """等待元素出现
        
        Args:
            target_text: 目标文本
            target_id: 目标ID
            timeout: 超时时间（秒）
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if target_text:
                element_info = self.element_parser.find_element_by_text(target_text)
                if element_info:
                    print(f"元素 '{target_text}' a已出现")
                    return True
            
            elif target_id:
                element_info = self.element_parser.find_element_by_id(target_id)
                if element_info:
                    print(f"元素 '{target_id}' 已出现")
                    return True
            
            # 等待0.5秒再检查
            time.sleep(0.5)
            print(f"等待元素 {target_text or target_id} 出现... ({int(time.time() - start_time)}s/{timeout}s)")
        
        print(f"等待超时，元素未出现: {target_text or target_id}")
        return False
    
    def find_element_by_text(self, text, exact_match=True):
        """查找文本元素
        
        Args:
            text: 要查找的文本
            exact_match: 是否精确匹配
        """
        element_info = self.element_parser.find_element_by_text(text, exact_match)
        return element_info is not None
    
    def find_element_by_id(self, resource_id):
        """查找ID元素
        
        Args:
            resource_id: 资源ID
        """
        element_info = self.element_parser.find_element_by_id(resource_id)
        return element_info is not None