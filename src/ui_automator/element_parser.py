import uiautomator2 as u2
import time
import json
import os
from PIL import Image
import cv2
import numpy as np

class ElementParser:
    def __init__(self, device=None):
        """初始化元素解析器"""
        self.device = device or u2.connect()  # 如果没有提供设备，自动连接
    
    # 修改 src/ui_automator/element_parser.py 中的 extract_elements 方法

    def extract_simplified_elements(self, xml_path, json_output_path=None):
        """
        提取简化的元素信息，更适合AI理解
    
        参数:
            xml_path: XML文件路径
            json_output_path: 可选的JSON输出路径
        
        返回:
            简化的元素列表，也可选择写入JSON文件
        """
        # 先提取完整元素
        self.extract_elements(xml_path, "data/app_info.json")
    
        # 读取XML
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # 解析XML
            import xml.etree.ElementTree as ET
            import io
        
            # 找到实际的XML开始位置
            if "<?xml" in xml_content:
                xml_start = xml_content.find("<?xml")
                xml_content = xml_content[xml_start:]
        
            tree = ET.parse(io.StringIO(xml_content))
            root = tree.getroot()
        
            # 简化元素列表
            simplified_elements = []
        
            # 递归收集所有可交互元素
            def collect_interactive_elements(node, path=""):
                # 获取元素属性
                attrs = node.attrib
            
                # 判断元素是否可交互
                is_clickable = attrs.get('clickable') == 'true'
                is_editable = attrs.get('editable') == 'true'
                is_checkable = attrs.get('checkable') == 'true'
                is_scrollable = attrs.get('scrollable') == 'true'
            
                if is_clickable or is_editable or is_checkable or is_scrollable:
                    # 获取元素文本、描述等
                    text = attrs.get('text', '')
                    resource_id = attrs.get('resource-id', '')
                    content_desc = attrs.get('content-desc', '')
                    class_name = attrs.get('class', '')
                    bounds_str = attrs.get('bounds', '')
                
                    # 解析bounds
                    bounds = []
                    if bounds_str:
                        try:
                            # 通常格式为"[x1,y1][x2,y2]"
                            bounds_str = bounds_str.replace('][', ',').strip('[]').split(',')
                            bounds = [int(b) for b in bounds_str]
                            center_x = (bounds[0] + bounds[2]) // 2
                            center_y = (bounds[1] + bounds[3]) // 2
                        except:
                            bounds = []
                
                    # 创建简化元素
                    element = {
                        "id": resource_id,
                        "text": text,
                        "desc": content_desc,
                        "class": class_name,
                        "path": path + "/" + (text or content_desc or resource_id or class_name),
                        "clickable": is_clickable,
                        "editable": is_editable,
                        "checkable": is_checkable,
                        "scrollable": is_scrollable
                    }
                
                    # 添加坐标（如果有）
                    if bounds:
                        element["coords"] = {
                            "center_x": center_x,
                            "center_y": center_y,
                            "left": bounds[0],
                            "top": bounds[1],
                            "right": bounds[2],
                            "bottom": bounds[3]
                        }
                
                    simplified_elements.append(element)
            
                # 递归处理子元素
                for i, child in enumerate(node):
                    new_path = path + "/" + (text or content_desc or resource_id or class_name)
                    collect_interactive_elements(child, new_path)
        
            # 开始收集
            collect_interactive_elements(root)
        
            # 输出JSON（如果需要）
            if json_output_path:
                import json
                with open(json_output_path, 'w', encoding='utf-8') as f:
                    json.dump(simplified_elements, f, ensure_ascii=False, indent=2)
            
            return simplified_elements
            
        except Exception as e:
            print(f"提取简化元素时出错: {e}")
            import traceback
            traceback.print_exc()
            return []    

    def _collect_system_context(self):
        """收集当前系统上下文信息，包括应用信息、窗口状态和UI特征"""
        context_info = {}
        
        # 获取当前应用信息
        try:
            context_info['current_app'] = self.device.app_current()
        except Exception as e:
            context_info['current_app_error'] = str(e)
        
        # 获取当前窗口信息
        try:
            context_info['window_info'] = self.device.window_info()
        except Exception as e:
            context_info['window_info_error'] = str(e)
        
        # 分析常见界面特征
        common_features = {
            "主屏幕": self.device.xpath('//android.widget.TextView[@text="主屏幕" or @text="Home"]').exists or 
                    self.device.xpath('//*[@resource-id="com.android.launcher3:id/workspace"]').exists,
                    
            "设置页": self.device.xpath('//android.widget.TextView[@text="设置" or @text="Settings"]').exists or 
                    self.device.xpath('//*[@resource-id="com.android.settings:id/settings_homepage_container"]').exists,
                    
            "WLAN设置": self.device.xpath('//android.widget.TextView[@text="WLAN" or @text="Wi-Fi"]').exists or 
                       self.device.xpath('//*[@resource-id="com.android.settings:id/wifi_settings"]').exists,
                       
            "蓝牙设置": self.device.xpath('//android.widget.TextView[@text="蓝牙" or @text="Bluetooth"]').exists or 
                       self.device.xpath('//*[@resource-id="com.android.settings:id/bluetooth_settings"]').exists,
                       
            "应用列表": self.device.xpath('//android.widget.TextView[@text="应用程序" or @text="Apps"]').exists or 
                       self.device.xpath('//*[@resource-id="com.android.settings:id/apps_list"]').exists,
                       
            "通知中心": self.device.xpath('//android.widget.TextView[@text="通知" or @text="Notifications"]').exists or 
                       self.device.xpath('//*[@resource-id="com.android.systemui:id/notification_panel"]').exists,
                       
            "控制中心": self.device.xpath('//android.widget.TextView[@text="控制中心" or @text="Control Center"]').exists or 
                       self.device.xpath('//*[@resource-id="com.android.systemui:id/quick_settings_panel"]').exists,
        }
        context_info['ui_features'] = {k: v for k, v in common_features.items() if v}
        
        # 获取可检测键盘状态
        context_info['keyboard_visible'] = self.device.xpath('//*[@resource-id="com.android.inputmethod.latin:id/keyboard_view"]').exists
        
        return context_info
    
    def _analyze_system_location(self, system_context):
        """分析当前系统位置并返回描述"""
        current_app = system_context.get('current_app', {})
        package = current_app.get('package', '')
        activity = current_app.get('activity', '')
        ui_features = system_context.get('ui_features', {})
        
        # 常见应用包名映射
        app_names = {
            'com.android.settings': '设置',
            'com.android.launcher3': '主屏幕/桌面',
            'com.android.systemui': '系统UI',
            'com.google.android.apps.messaging': '信息',
            'com.android.contacts': '联系人',
            'com.android.dialer': '电话',
            'com.android.camera': '相机',
            'com.android.gallery3d': '图库',
            'com.android.browser': '浏览器',
            'com.android.email': '邮件',
            'com.google.android.gm': 'Gmail',
            'com.google.android.apps.photos': '照片',
            'com.google.android.youtube': 'YouTube',
        }
        
        # 判断当前应用
        current_app_name = app_names.get(package, package)
        
        # 尝试根据活动名和界面特征确定更具体的位置
        location = f"当前应用: {current_app_name}"
        
        # 添加更具体的位置信息
        if package == 'com.android.settings':
            if "WLAN设置" in ui_features:
                location += " > WLAN/Wi-Fi设置"
            elif "蓝牙设置" in ui_features:
                location += " > 蓝牙设置"
            elif "应用列表" in ui_features:
                location += " > 应用列表"
            else:
                location += " > 设置主页"
        elif package == 'com.android.launcher3' or 'launcher' in package:
            if "控制中心" in ui_features:
                location += " > 控制中心"
            elif "通知中心" in ui_features:
                location += " > 通知中心"
            else:
                location += " > 主屏幕"
        
        # 添加键盘状态
        if system_context.get('keyboard_visible', False):
            location += " (键盘已显示)"
        
        return location