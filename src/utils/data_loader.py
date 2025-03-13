import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional

class DataLoader:
    """加载测试数据的工具类"""
    
    @staticmethod
    def load_test_cases(file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        从Excel文件加载测试用例
        
        参数:
            file_path: Excel文件路径
            
        返回:
            测试用例列表，每个测试用例是一个字典，包含测试编号、测试步骤、预期结果等信息
        """
        try:
            # 获取文件的绝对路径
            abs_path = os.path.abspath(file_path)
            
            # 读取Excel文件
            df = pd.read_excel(abs_path)
            
            # 将DataFrame转换为字典列表
            test_cases = []
            for _, row in df.iterrows():
                test_case = {
                    "test_id": str(row["测试编号"]),
                    "test_step": row["测试步骤"],
                    "expected_result": row["预期结果"],
                    "test_result": row["测试结果（pass/fail）"] if pd.notna(row["测试结果（pass/fail）"]) else ""
                }
                test_cases.append(test_case)
            
            return test_cases
        
        except Exception as e:
            print(f"加载测试用例时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def load_element_xml(file_path: str) -> Optional[str]:
        """
        加载元素XML文件
        
        参数:
            file_path: XML文件路径
            
        返回:
            XML字符串，失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            return xml_content
        except Exception as e:
            print(f"加载元素XML文件时出错: {e}")
            return None
    
    @staticmethod
    def load_app_info(file_path: str) -> Optional[Dict[str, Any]]:
        """
        加载应用信息JSON文件
        
        参数:
            file_path: JSON文件路径
            
        返回:
            应用信息字典，失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                app_info = json.load(f)
            return app_info
        except Exception as e:
            print(f"加载应用信息文件时出错: {e}")
            return None
    
    @staticmethod
    def save_test_results(file_path: str, test_cases: List[Dict[str, Any]]) -> bool:
        """
        保存测试结果到Excel文件
        
        参数:
            file_path: Excel文件路径
            test_cases: 测试用例列表，包含测试结果
            
        返回:
            保存成功返回True，否则返回False
        """
        try:
            # 创建DataFrame
            data = []
            for case in test_cases:
                data.append({
                    "测试编号": case["test_id"],
                    "测试步骤": case["test_step"],
                    "预期结果": case["expected_result"],
                    "测试结果（pass/fail）": case["test_result"]
                })
            
            df = pd.DataFrame(data)
            
            # 保存到Excel
            df.to_excel(file_path, index=False)
            
            return True
        
        except Exception as e:
            print(f"保存测试结果时出错: {e}")
            return False