import json
import os
from openai import OpenAI
from typing import Dict, Any, List, Optional

class AIClient:
    """与AI API交互的客户端"""
    
    def __init__(self, config_path: str = "config/api_config.json"):
        """初始化AI客户端"""
        # 加载API配置
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"加载API配置失败: {e}")
            # 设置默认配置
            self.config = {
                "api_key": "sk-9f785583e19a4437ba617fbc600681f9",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
                "max_tokens": 4096,
                "temperature": 0.7
            }
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"]
        )
    
    def get_action_analysis(self, prompt: str) -> Dict[str, Any]:
        """
        分析测试步骤并返回高级动作
        
        参数:
            prompt: 提示文本
            
        返回:
            动作字典
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "You are a helpful android UI automation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 较低的温度使结果更确定
                max_tokens=1024,
                stream=False
            )
            
            action_text = response.choices[0].message.content
            try:
                # 尝试解析JSON
                action_dict = json.loads(action_text)
                return action_dict
            except json.JSONDecodeError:
                # 如果解析失败，尝试提取JSON部分
                if "{" in action_text and "}" in action_text:
                    json_part = action_text[action_text.find("{"):action_text.rfind("}")+1]
                    try:
                        action_dict = json.loads(json_part)
                        return action_dict
                    except:
                        pass
                
                print("无法解析AI返回的动作JSON，使用默认动作")
                return {"action": "UNKNOWN", "target": "UNKNOWN"}
                
        except Exception as e:
            print(f"获取动作分析时出错: {e}")
            import traceback
            traceback.print_exc()
            return {"action": "ERROR", "target": str(e)}
    
    def generate_operation_script(self, prompt: str) -> str:
        """
        生成具体操作脚本
        
        参数:
            prompt: 提示文本
            
        返回:
            Python脚本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "You are a helpful android UI automation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                stream=False
            )
            
            # 提取生成的代码
            code = response.choices[0].message.content
            code = self._extract_code_from_response(code)
            return code
            
        except Exception as e:
            print(f"生成操作脚本时出错: {e}")
            import traceback
            traceback.print_exc()
            return "def execute_test_step(d):\n    print('生成脚本出错')\n    return False"
    
    def generate_test_code(self, 
                          test_cases: List[Dict[str, Any]], 
                          element_xml: str, 
                          app_info: Dict[str, Any],
                          element_dict: Dict[str, Any],
                          test_index: int = 0) -> Optional[str]:
        """
        根据测试用例和元素信息生成测试代码
        
        参数:
            test_cases: 测试用例列表
            element_xml: 元素XML字符串
            app_info: 应用信息
            element_dict: 元素字典
            test_index: 要执行的测试用例索引
            
        返回:
            生成的测试代码
        """
        try:
            # 确保test_index在有效范围内
            if test_index < 0 or test_index >= len(test_cases):
                print(f"测试索引 {test_index} 超出范围")
                return None
            
            current_test = test_cases[test_index]
            
            # 构建提示
            prompt = f"""
            你是一个专业的安卓UI自动化测试专家。请根据以下信息生成Python代码:
            
            测试用例: {current_test['test_step']}
            预期结果: {current_test['expected_result']}
            
            当前应用信息:
            ```json
            {json.dumps(app_info, ensure_ascii=False, indent=2)}
            ```
            
            元素字典包含以下UI元素:
            ```json
            {json.dumps(element_dict, ensure_ascii=False, indent=2)}
            ```
            
            请基于uiautomator2库生成一个完整的Python函数，实现上述测试用例的测试步骤。
            函数应该执行"{current_test['test_step']}"这个操作，比如点击相应的按钮、输入文本等。
            代码应该模拟人类操作:
            1. 找到目标元素在屏幕上的位置
            2. 执行相应的交互动作
            
            你的代码必须：
            1. 使用上面的元素字典中的信息来找到正确的UI元素
            2. 执行必要的操作（点击、输入等）
            3. 只包含必要的代码，不要包含任何注释、说明或无关代码
            4. 函数名应该为"execute_test_step"，参数为"d"（uiautomator2设备对象）
            
            示例格式:
            ```python
            def execute_test_step(d):
                # 查找WLAN元素
                element = None
                for path, elem_info in element_dict.items():
                    if elem_info['text'] == 'WLAN':
                        element = elem_info
                        break
                
                if element:
                    # 获取元素中心坐标
                    x, y = element['coords']['center_x'], element['coords']['center_y']
                    # 点击元素
                    d.click(x, y)
                    return True
                return False
            ```
            
            只返回代码，不要有其他任何解释。
            """
            
            # 调用DeepSeek API
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "You are a helpful android UI automation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                stream=False
            )
            
            # 提取生成的代码
            code = response.choices[0].message.content
            code = self._extract_code_from_response(code)
            return code
            
        except Exception as e:
            print(f"生成代码时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def validate_test_result(self, 
                           test_case: Dict[str, Any], 
                           element_xml: str, 
                           app_info: Dict[str, Any]) -> bool:
        """
        验证测试结果
        
        参数:
            test_case: 测试用例
            element_xml: 元素XML
            app_info: 应用信息
            
        返回:
            验证结果，通过返回True，否则返回False
        """
        try:
            # 构建提示
            prompt = f"""
            你是一个专业的安卓UI自动化测试专家。请验证测试结果:
            
            测试步骤: {test_case['test_step']}
            预期结果: {test_case['expected_result']}
            
            当前应用信息:
            ```json
            {json.dumps(app_info, ensure_ascii=False, indent=2)}
            ```
            
            XML元素树摘要:
            ```
            {element_xml[:2000] if len(element_xml) > 2000 else element_xml}
            ```
            
            请分析上述信息，判断测试结果是否符合预期。
            只回答"通过"或"失败"，然后在新行提供简要理由。
            """
            
            # 调用DeepSeek API
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "You are a helpful android UI testing validator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # 较低的温度使结果更确定
                max_tokens=1024,
                stream=False
            )
            
            # 提取验证结果
            validation_result = response.choices[0].message.content
            
            # 判断结果
            is_passed = "通过" in validation_result.split("\n")[0].lower()
            print(f"验证结果: {validation_result}")
            
            return is_passed
            
        except Exception as e:
            print(f"验证结果时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """从响应文本中提取代码块"""
        if "```python" in response_text and "```" in response_text.split("```python", 1)[1]:
            code_block = response_text.split("```python", 1)[1].split("```", 1)[0]
            return code_block.strip()
        elif "```" in response_text and "```" in response_text.split("```", 1)[1]:
            code_block = response_text.split("```", 1)[1].split("```", 1)[0]
            return code_block.strip()
        else:
            # 如果没有代码块标记，返回整个响应
            return response_text.strip()