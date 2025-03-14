import os
import json
import time
import xml.etree.ElementTree as ET
import re
import uiautomator2 as u2
from PIL import Image
import io

class ElementParser:
    def __init__(self, device_controller):
        """元素解析器，解析UI层次结构并转为可操作格式
        
        Args:
            device_controller: 设备控制器实例
        """
        self.device_controller = device_controller
        self.device = device_controller.device  # 直接使用u2设备对象
    
    def _analyze_screen_state(self, app_info):
        """分析屏幕状态，确定当前界面类型
    
        Args:
            app_info: 应用信息字典
        
        Returns:
            包含页面状态信息的字典
        """
        result = {}
    
        # 获取包名和活动名
        current_package = app_info.get("current_package", "")
        current_activity = app_info.get("current_activity", "")
    
        # 识别常见界面状态
        if current_package == "com.miui.home" and ".launcher.Launcher" in current_activity:
            result["screen_state"] = "主屏幕"
        elif current_package == "com.android.settings":
            if "network" in current_activity.lower() or "wifi" in current_activity.lower():
                result["screen_state"] = "WLAN设置界面"
            else:
                result["screen_state"] = "设置界面"
        else:
            result["screen_state"] = "未知界面"
    
        return result

    def parse_ui_hierarchy(self):
        """解析UI层次结构，生成XML和JSON表示
    
        Returns:
            (xml_content, app_info): XML内容和应用信息
        """
        try:
            # 获取UI层次XML
            print("正在获取UI层次结构...")
            xml_content = self.device.dump_hierarchy()
            print(f"成功获取UI层次，大小: {len(xml_content)} 字节")
        
            # 确保数据目录存在
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
        
            # 保存XML到文件
            xml_path = os.path.join(data_dir, "element.xml")
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_content)
        
            # 获取应用基本信息
            app_basic_info = self.device_controller.get_current_app_info()
            screen_width, screen_height = self.device_controller.get_screen_size()
        
            # 构建完整的应用信息
            app_info = {
                "screen_width": screen_width,
                "screen_height": screen_height
            }
        
            # 添加应用基本信息（如果存在）
            if app_basic_info:
                app_info.update(app_basic_info)
        
            # 将XML解析为JSON结构
            if xml_content:
                try:
                    app_info["elements"] = self._xml_to_json(xml_content)
                    # 分析页面布局，确定滚动方向
                    scroll_direction = self._analyze_scroll_direction(app_info["elements"])
                    app_info["recommended_scroll"] = scroll_direction
                
                    # 添加屏幕状态分析
                    screen_state = self._analyze_screen_state(app_info)
                    app_info.update(screen_state)
                except Exception as e:
                    print(f"解析XML失败: {e}")
                    # 添加错误信息但不中断流程
                    app_info["parse_error"] = str(e)
        
            # 保存JSON到文件
            json_path = os.path.join(data_dir, "app_info.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(app_info, f, ensure_ascii=False, indent=2)
        
            return xml_content, app_info
    
        except Exception as e:
            print(f"解析UI层次结构失败: {e}")
        
            # 添加额外恢复措施：截图和尝试使用device.dump()
            try:
                # 保存截图
                screenshot_path = os.path.join("data", "screen.png")
                self.device.screenshot(screenshot_path)
                print(f"已保存屏幕截图到 {screenshot_path}")
            
                # 尝试使用更简单的dump
                elements_info = self.device.dump()
            
                # 保存为JSON
                simple_json_path = os.path.join("data", "simple_elements.json")
                with open(simple_json_path, "w", encoding="utf-8") as f:
                    json.dump(elements_info, f, ensure_ascii=False, indent=2)
            
                # 构建一个简单的返回值
                simple_info = {
                    "screen_size": self.device_controller.get_screen_size(),
                    "simple_elements": elements_info
                }
            
                return None, simple_info
        
            except Exception as se:
                print(f"备份措施也失败: {se}")
                return None, {"error": str(e)}
    
    def _analyze_scroll_direction(self, elements):
        """分析页面布局，确定最可能的滚动方向
        
        Args:
            elements: 解析后的元素树
            
        Returns:
            推荐的滚动方向: "vertical", "horizontal", 或 "both"
        """
        # 默认为垂直滚动
        direction = "vertical"
        
        # 检查是否包含ScrollView或RecyclerView等常见可滚动容器
        if elements:
            scroll_classes = ["ScrollView", "RecyclerView", "ListView", "HorizontalScrollView", "ViewPager"]
            
            def find_scroll_view(node):
                if "class" in node:
                    node_class = node["class"]
                    for cls in scroll_classes:
                        if cls in node_class:
                            if "HorizontalScrollView" in node_class or "ViewPager" in node_class:
                                return "horizontal"
                            else:
                                return "vertical"
                
                # 递归搜索子节点
                if "children" in node:
                    for child in node["children"]:
                        result = find_scroll_view(child)
                        if result:
                            return result
                return None
            
            scroll_dir = find_scroll_view(elements)
            if scroll_dir:
                direction = scroll_dir
        
        return direction
    
    def extract_simplified_elements(self):
        """提取简化的元素信息，更适合AI理解
        
        Returns:
            简化的元素列表字典
        """
        try:
            # 使用uiautomator2的dump获取所有可见元素
            elements = self.device.dump()
            
            # 保存为JSON格式
            json_path = os.path.join("data", "simplified_elements.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(elements, f, ensure_ascii=False, indent=2)
            
            print(f"已导出简化元素信息到 {json_path}")
            return elements
        except Exception as e:
            print(f"提取简化元素失败: {e}")
            return []
    
    def _xml_to_json(self, xml_content):
        """将XML转换为JSON结构
        
        Args:
            xml_content: XML字符串
        """
        try:
            root = ET.fromstring(xml_content)
            return self._parse_node(root)
        except ET.ParseError as e:
            print(f"XML解析错误: {e}")
            # 尝试修复并重新解析
            fixed_xml = xml_content.replace("&", "&amp;")
            try:
                root = ET.fromstring(fixed_xml)
                return self._parse_node(root)
            except ET.ParseError:
                # 如果仍然失败，尝试使用u2的dump
                print("尝试使用简化的元素提取方法")
                return self.extract_simplified_elements()
    
    def _parse_node(self, node, parent_path=""):
        """递归解析XML节点
        
        Args:
            node: XML节点
            parent_path: 父节点路径
        """
        # 获取节点属性
        attrib = node.attrib if hasattr(node, 'attrib') else {}
        
        # 构建节点路径
        node_id = attrib.get("resource-id", "").split("/")[-1] if "resource-id" in attrib else ""
        node_text = attrib.get("text", "")
        node_class = attrib.get("class", "").split(".")[-1] if "class" in attrib else "node"
        
        if node_id:
            current_path = f"{parent_path}/{node_id}" if parent_path else node_id
        elif node_text:
            # 清理文本中的特殊字符
            clean_text = re.sub(r'[^\w]', '_', node_text)
            current_path = f"{parent_path}/{node_class}_{clean_text}" if parent_path else f"{node_class}_{clean_text}"
        else:
            current_path = f"{parent_path}/{node_class}" if parent_path else node_class
        
        # 构建节点信息
        node_info = {
            "class": attrib.get("class", ""),
            "resource-id": attrib.get("resource-id", ""),
            "text": attrib.get("text", ""),
            "content-desc": attrib.get("content-desc", ""),
            "clickable": attrib.get("clickable", "false") == "true",
            "bounds": self._parse_bounds(attrib.get("bounds", "")),
            "path": current_path,
            "children": []
        }
        
        # 处理子节点
        for child in node:
            try:
                child_info = self._parse_node(child, current_path)
                node_info["children"].append(child_info)
            except Exception as e:
                print(f"解析子节点失败: {e}")
        
        return node_info
    
    def _parse_bounds(self, bounds_str):
        """解析元素边界字符串为坐标
        
        Args:
            bounds_str: 格式如 "[0,0][1080,1920]"
        """
        try:
            match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                return {
                    "left": x1,
                    "top": y1,
                    "right": x2,
                    "bottom": y2,
                    "center_x": (x1 + x2) // 2,
                    "center_y": (y1 + y2) // 2
                }
        except Exception as e:
            print(f"解析边界失败: {bounds_str}, 错误: {e}")
        
        # 默认值
        return {
            "left": 0, "top": 0, "right": 0, "bottom": 0,
            "center_x": 0, "center_y": 0
        }
    
    def find_element_by_text(self, text, exact_match=True):
        """通过文本查找元素
        
        Args:
            text: 要查找的文本
            exact_match: 是否精确匹配
        """
        try:
            if exact_match:
                element = self.device(text=text)
            else:
                element = self.device(textContains=text)
            
            if element.exists:
                bounds = element.info['bounds']
                result = {
                    "text": element.info.get("text", ""),
                    "resource-id": element.info.get("resourceId", ""),
                    "class": element.info.get("className", ""),
                    "bounds": {
                        "left": bounds['left'],
                        "top": bounds['top'],
                        "right": bounds['right'],
                        "bottom": bounds['bottom'],
                        "center_x": (bounds['left'] + bounds['right']) // 2,
                        "center_y": (bounds['top'] + bounds['bottom']) // 2
                    },
                    "clickable": element.info.get("clickable", False)
                }
                print(f"找到文本元素: '{text}'")
                
                # 如果元素不可点击，尝试找到可点击的父元素
                if not result["clickable"]:
                    print(f"元素 '{text}' 不可点击，尝试查找可点击的父元素")
                    clickable_parent = self._find_clickable_parent(element)
                    if clickable_parent:
                        parent_bounds = clickable_parent.info['bounds']
                        parent_result = {
                            "text": clickable_parent.info.get("text", ""),
                            "resource-id": clickable_parent.info.get("resourceId", ""),
                            "class": clickable_parent.info.get("className", ""),
                            "bounds": {
                                "left": parent_bounds['left'],
                                "top": parent_bounds['top'],
                                "right": parent_bounds['right'],
                                "bottom": parent_bounds['bottom'],
                                "center_x": (parent_bounds['left'] + parent_bounds['right']) // 2,
                                "center_y": (parent_bounds['top'] + parent_bounds['bottom']) // 2
                            },
                            "clickable": True
                        }
                        print(f"找到可点击的父元素: {parent_result['class']}")
                        return parent_result
                
                return result
            print(f"未找到文本为 '{text}' 的元素")
            return None
        except Exception as e:
            print(f"查找文本元素时发生错误: {e}")
            return None
    
    def _find_clickable_parent(self, element):
        """查找元素的可点击父元素
        
        Args:
            element: uiautomator2的元素对象
            
        Returns:
            可点击的父元素对象或None
        """
        try:
            # 通过xpath轴查找父元素
            parent = element.parent()
            attempts = 0
            
            # 最多向上查找5层父级
            while parent and attempts < 5:
                if parent.info.get("clickable", False):
                    return parent
                
                parent = parent.parent()
                attempts += 1
            
            return None
        except Exception as e:
            print(f"查找可点击父元素时出错: {e}")
            return None
    
    def find_element_by_id(self, resource_id):
        """通过资源ID查找元素
        
        Args:
            resource_id: 资源ID
        """
        try:
            element = self.device(resourceId=resource_id)
            
            if element.exists:
                bounds = element.info['bounds']
                result = {
                    "text": element.info.get("text", ""),
                    "resource-id": element.info.get("resourceId", ""),
                    "class": element.info.get("className", ""),
                    "bounds": {
                        "left": bounds['left'],
                        "top": bounds['top'],
                        "right": bounds['right'],
                        "bottom": bounds['bottom'],
                        "center_x": (bounds['left'] + bounds['right']) // 2,
                        "center_y": (bounds['top'] + bounds['bottom']) // 2
                    },
                    "clickable": element.info.get("clickable", False)
                }
                print(f"找到ID元素: '{resource_id}'")
                
                # 如果元素不可点击，尝试找到可点击的父元素
                if not result["clickable"]:
                    print(f"元素 '{resource_id}' 不可点击，尝试查找可点击的父元素")
                    clickable_parent = self._find_clickable_parent(element)
                    if clickable_parent:
                        parent_bounds = clickable_parent.info['bounds']
                        parent_result = {
                            "text": clickable_parent.info.get("text", ""),
                            "resource-id": clickable_parent.info.get("resourceId", ""),
                            "class": clickable_parent.info.get("className", ""),
                            "bounds": {
                                "left": parent_bounds['left'],
                                "top": parent_bounds['top'],
                                "right": parent_bounds['right'],
                                "bottom": parent_bounds['bottom'],
                                "center_x": (parent_bounds['left'] + parent_bounds['right']) // 2,
                                "center_y": (parent_bounds['top'] + parent_bounds['bottom']) // 2
                            },
                            "clickable": True
                        }
                        print(f"找到可点击的父元素: {parent_result['class']}")
                        return parent_result
                
                return result
            print(f"未找到ID为 '{resource_id}' 的元素")
            return None
        except Exception as e:
            print(f"查找ID元素时发生错误: {e}")
            return None