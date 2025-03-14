import sys
import traceback
import re

class CodeExecutor:
    def __init__(self, interaction_handler):
        """代码执行器，负责执行AI生成的代码
        
        Args:
            interaction_handler: 交互处理器实例
        """
        self.interaction_handler = interaction_handler
        self.device_controller = interaction_handler.device_controller
        self.element_parser = interaction_handler.element_parser
    
    def execute_code(self, code_string):
        """执行代码字符串
        
        Args:
            code_string: 要执行的代码字符串
        """
        # 清理代码字符串，移除Markdown格式的代码块标记
        cleaned_code = self._clean_code_block(code_string)
        
        # 创建局部变量字典，包含所有需要的引用
        local_vars = {
            "interaction_handler": self.interaction_handler,
            "device_controller": self.device_controller,
            "element_parser": self.element_parser
        }
        
        # 添加交互处理器的方法作为直接可调用函数
        for method_name in dir(self.interaction_handler):
            if not method_name.startswith("_"):  # 排除私有方法
                method = getattr(self.interaction_handler, method_name)
                if callable(method):
                    local_vars[method_name] = method
        
        # 添加设备控制器的方法
        for method_name in dir(self.device_controller):
            if not method_name.startswith("_"):  # 排除私有方法
                method = getattr(self.device_controller, method_name)
                if callable(method):
                    # 不覆盖已有方法
                    if method_name not in local_vars:
                        local_vars[method_name] = method
        
        try:
            # 打印代码
            print("\n=== 即将执行的代码 ===")
            print(cleaned_code)
            print("=====================\n")
            
            # 执行代码
            exec(cleaned_code, globals(), local_vars)
            return True, None
        except Exception as e:
            error_msg = f"代码执行错误: {str(e)}\n{traceback.format_exc()}"
            return False, error_msg
    
    def _clean_code_block(self, code_string):
        """清理代码字符串，移除Markdown格式的代码块标记
        
        Args:
            code_string: 包含可能的格式标记的代码字符串
            
        Returns:
            清理后的代码字符串
        """
        # 移除开始的```python或```等代码块标记
        code_string = re.sub(r'^```\w*\s*', '', code_string)
        
        # 移除结束的```代码块标记
        code_string = re.sub(r'```\s*$', '', code_string)
        
        return code_string
    
    def get_function_dictionary(self):
        """获取可用函数字典，用于AI生成代码
        
        Returns:
            包含函数名、参数和说明的字典
        """
        function_dict = {}
        
        # 添加交互处理器的方法
        for method_name in dir(self.interaction_handler):
            if not method_name.startswith("_"):  # 排除私有方法
                method = getattr(self.interaction_handler, method_name)
                if callable(method):
                    doc = method.__doc__ or ""
                    # 解析参数
                    params = []
                    for line in doc.split("\n"):
                        if "Args:" in line:
                            continue
                        param_match = line.strip().split(":")
                        if len(param_match) > 1:
                            param_name = param_match[0].strip()
                            params.append(param_name)
                    
                    function_dict[method_name] = {
                        "description": doc,
                        "parameters": params
                    }
        
        # 添加设备控制器的方法
        for method_name in dir(self.device_controller):
            if not method_name.startswith("_"):  # 排除私有方法
                method = getattr(self.device_controller, method_name)
                if callable(method):
                    # 不覆盖已有方法
                    if method_name not in function_dict:
                        doc = method.__doc__ or ""
                        # 解析参数
                        params = []
                        for line in doc.split("\n"):
                            if "Args:" in line:
                                continue
                            param_match = line.strip().split(":")
                            if len(param_match) > 1:
                                param_name = param_match[0].strip()
                                params.append(param_name)
                        
                        function_dict[method_name] = {
                            "description": doc,
                            "parameters": params
                        }
        
        return function_dict