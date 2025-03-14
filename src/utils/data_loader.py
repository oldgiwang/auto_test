import os
import json
import pandas as pd
from xml.etree import ElementTree as ET

class DataLoader:
    def __init__(self, base_dir="."):
        """数据加载器，处理各种数据文件的加载和保存"""
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, "config")
        self.data_dir = os.path.join(base_dir, "data")
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所需目录存在"""
        for directory in [self.config_dir, self.data_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def load_api_config(self):
        """加载API配置文件"""
        config_path = os.path.join(self.config_dir, "api_config.json")
        if not os.path.exists(config_path):
            # 默认配置
            default_config = {
                "api_key": "sk-9f785583e19a4437ba617fbc600681f9",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
                "max_tokens": 4096,
                "temperature": 0.7
            }
            # 保存默认配置
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载API配置失败: {e}，使用默认配置")
            return {
                "api_key": "sk-9f785583e19a4437ba617fbc600681f9",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
                "max_tokens": 4096,
                "temperature": 0.7
            }
    
    def load_test_cases(self):
        """加载测试用例Excel文件"""
        test_cases_path = os.path.join(self.data_dir, "test_cases.xlsx")
        if not os.path.exists(test_cases_path):
            # 创建默认测试用例
            df = pd.DataFrame({
                "测试编号": [1, 2, 3, 4],
                "测试步骤": ["回到主界面", "打开设置", "打开wlan设置", "打开wlan开关"],
                "预期结果": ["系统成功返回主界面", "系统进入设置界面", "系统成功进入wlan设置", "wlan开关成功打开，可搜索到wifi"],
                "测试结果（pass/fail）": ["", "", "", ""]
            })
            df.to_excel(test_cases_path, index=False)
            return df
        
        try:
            return pd.read_excel(test_cases_path)
        except Exception as e:
            print(f"加载测试用例失败: {e}")
            # 创建空的DataFrame
            return pd.DataFrame(columns=["测试编号", "测试步骤", "预期结果", "测试结果（pass/fail）"])
    
    def load_element_xml(self):
        """加载元素XML文件"""
        xml_path = os.path.join(self.data_dir, "element.xml")
        if os.path.exists(xml_path):
            try:
                with open(xml_path, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试使用其他编码
                try:
                    with open(xml_path, "r", encoding="latin-1") as f:
                        return f.read()
                except Exception as e:
                    print(f"加载XML文件失败: {e}")
        return None
    
    def load_app_info(self):
        """加载应用信息JSON文件"""
        app_info_path = os.path.join(self.data_dir, "app_info.json")
        if os.path.exists(app_info_path):
            try:
                with open(app_info_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载应用信息失败: {e}")
        return {}
    
    def save_element_xml(self, xml_content):
        """保存元素XML内容到文件"""
        if xml_content is None:
            print("警告: XML内容为空，跳过保存")
            return
        
        xml_path = os.path.join(self.data_dir, "element.xml")
        try:
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_content)
            print(f"XML内容已保存到 {xml_path}")
        except Exception as e:
            print(f"保存XML内容失败: {e}")
    
    def save_app_info(self, app_info):
        """保存应用信息到JSON文件"""
        if not app_info:
            print("警告: 应用信息为空，跳过保存")
            return
        
        app_info_path = os.path.join(self.data_dir, "app_info.json")
        try:
            with open(app_info_path, "w", encoding="utf-8") as f:
                json.dump(app_info, f, ensure_ascii=False, indent=2)
            print(f"应用信息已保存到 {app_info_path}")
        except Exception as e:
            print(f"保存应用信息失败: {e}")
    
    def save_test_result(self, test_case_index, result):
        """保存测试结果到Excel文件"""
        test_cases_path = os.path.join(self.data_dir, "test_cases.xlsx")
        try:
            df = pd.read_excel(test_cases_path)
            if 0 <= test_case_index-1 < len(df):
                df.loc[test_case_index-1, "测试结果（pass/fail）"] = result
                df.to_excel(test_cases_path, index=False)
                print(f"测试结果已保存: 用例 {test_case_index} - {result}")
            else:
                print(f"警告: 测试用例索引 {test_case_index} 超出范围")
        except Exception as e:
            print(f"保存测试结果失败: {e}")