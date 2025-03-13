import sys
import traceback
from typing import Dict, Any, Optional

class CodeExecutor:
    """执行AI生成的代码"""
    
    def __init__(self, device_controller):
        """
        初始化代码执行器
        
        参数:
            device_controller: 设备控制器实例，用于在代码执行环境中提供设备操作
        """
        self.device_controller = device_controller
    
    def execute_code(self, code: str) -> bool:
        """
        执行AI生成的代码
        
        参数:
            code: 要执行的Python代码
            
        返回:
            执行成功返回True，否则返回False
        """
        try:
            # 创建局部变量字典，包含设备控制器
            local_vars = {
                "d": self.device_controller.get_device(),
                "device": self.device_controller.get_device()
            }
            
            # 执行代码
            exec(code, globals(), local_vars)
            
            return True
        
        except Exception as e:
            print(f"执行代码时出错: {e}")
            traceback.print_exc()
            return False