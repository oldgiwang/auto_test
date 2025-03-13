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

    def extract_elements(self, xml_output_path, app_info_output_path, screenshot_path=None):
        """
        提取UI元素信息和应用信息
    
        参数:
            xml_output_path: 输出元素XML的路径
            app_info_output_path: 输出应用信息JSON的路径
            screenshot_path: 可选的截图保存路径
    
        返回:
            成功提取元素和信息返回True，否则返回False
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(xml_output_path), exist_ok=True)
            os.makedirs(os.path.dirname(app_info_output_path), exist_ok=True)
        
            # 等待UI稳定
            time.sleep(1)
        
            # 收集系统上下文信息
            print("获取系统层级信息...")
            system_context = self._collect_system_context()
        
            # 保存系统上下文信息
            with open(app_info_output_path, "w", encoding="utf-8") as f:
                json.dump(system_context, f, ensure_ascii=False, indent=4)
        
            # 截取整个屏幕(如果需要)
            if screenshot_path:
                screen = self.device.screenshot(format='pillow')
                screen.save(screenshot_path)
        
            # 获取所有UI元素
            xml = self.device.dump_hierarchy()
        
            # 将XML保存到文件，确保XML声明在开头，没有前导空白
            with open(xml_output_path, "w", encoding="utf-8") as f:
                # 先写入XML声明
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            
                # 添加系统层级信息作为XML注释
                current_app = system_context.get('current_app', {})
                current_package = current_app.get('package', 'Unknown')
                current_activity = current_app.get('activity', 'Unknown')
                location_desc = self._analyze_system_location(system_context)
            
                f.write(f"<!-- 系统层级信息\n")
                f.write(f"包名 (Package): {current_package}\n")
                f.write(f"活动 (Activity): {current_activity}\n")
                f.write(f"系统位置: {location_desc}\n")
                f.write(f"界面特征: {', '.join(k for k, v in system_context.get('ui_features', {}).items() if v)}\n")
                f.write(f"-->\n\n")
            
                # 添加原始XML内容，但去掉原始XML中的XML声明，避免重复
                if "<?xml" in xml:
                    # 移除原始XML中的XML声明
                    xml_start = xml.find("?>") + 2
                    xml = xml[xml_start:].strip()
            
                f.write(xml)
        
            return True
        
        except Exception as e:
            print(f"提取元素时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

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