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
        
    def analyze_test_step(self, test_step: str, xml_content: str, app_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分析测试步骤，提取高级动作
        
        参数:
            test_step: 测试步骤描述
            xml_content: 元素XML内容
            app_info: 应用信息
            
        返回:
            动作列表，每个动作是一个字典
        """
        try:
            # 构建提示
            prompt = f"""
            你是一个专注于UI操作分析的AI。请分析以下安卓测试步骤，并提取出要执行的高级动作。

            测试步骤: {test_step}

            当前应用信息:
            ```json
            {json.dumps(app_info, ensure_ascii=False, indent=2)}
            ```

            当前界面元素摘要:
            ```xml
            {xml_content[:2000] if len(xml_content) > 2000 else xml_content}
            ```

            请将动作分解为以下格式之一:
            1. 对于打开操作: {{"action": "OPEN", "target": "应用名称"}}
            2. 对于点击操作: {{"action": "CLICK", "target": "元素名称"}}
            3. 对于输入操作: {{"action": "INPUT", "target": "输入框名称", "text": "要输入的文本"}}
            4. 对于滑动操作: {{"action": "SWIPE", "direction": "方向(UP/DOWN/LEFT/RIGHT)"}}
            5. 对于检查操作: {{"action": "CHECK", "target": "元素名称"}}
            6. 对于等待操作: {{"action": "WAIT", "target": "元素名称", "timeout": 超时秒数}}
            7. 对于返回操作: {{"action": "BACK"}}
            8. 对于回主页操作: {{"action": "HOME"}}

            如果测试步骤涉及多个动作，请返回动作列表。
            只返回JSON格式的动作，不要有其他任何解释。
            """
            
            # 调用API获取分析结果
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "You are a helpful android UI automation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度使结果更确定
                max_tokens=self.config["max_tokens"],
                stream=False
            )
            
            # 提取分析结果
            result_text = response.choices[0].message.content
            
            # 解析JSON结果
            try:
                # 尝试直接解析
                actions = json.loads(result_text)
                
                # 确保返回格式一致 (列表)
                if isinstance(actions, dict):
                    if "actions" in actions:
                        actions = actions["actions"]
                    else:
                        actions = [actions]
                
                return actions
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                if "{" in result_text and "}" in result_text:
                    start = result_text.find("[") if "[" in result_text else result_text.find("{")
                    end = result_text.rfind("]") + 1 if "]" in result_text else result_text.rfind("}") + 1
                    json_part = result_text[start:end]
                    
                    try:
                        actions = json.loads(json_part)
                        # 确保返回格式一致 (列表)
                        if isinstance(actions, dict):
                            actions = [actions]
                        return actions
                    except:
                        pass
                        
                print(f"无法解析AI返回的JSON，返回原文本: {result_text}")
                return []
                
        except Exception as e:
            print(f"分析测试步骤时出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def generate_operation_script(self, actions: List[Dict[str, Any]], xml_content: str, app_info: Dict[str, Any]) -> str:
        """
        根据高级动作生成具体操作脚本
        """
        try:
            # 构建提示
            actions_json = json.dumps(actions, ensure_ascii=False, indent=2)
            prompt = f"""
            你是一个专业的安卓UI自动化测试专家。请根据以下信息生成Python代码:

            动作列表:
            ```json
            {actions_json}
            ```

            当前应用信息:
            ```json
            {json.dumps(app_info, ensure_ascii=False, indent=2)}
            ```

            当前界面元素:
            ```xml
            {xml_content[:5000] if len(xml_content) > 5000 else xml_content}
            ```

            请生成一个名为execute_test_step的函数，该函数:
            1. 接收一个参数d (uiautomator2设备对象)
            2. 在函数内部使用全局变量handler来执行操作
            3. 函数应该返回布尔值，表示操作是否成功

            重要约束:
            - 不要使用UI Automator框架的后台调度方法，而应该模拟真实的人工交互
            - 所有操作都必须通过handler调用，而不是直接使用d
            - 函数必须包含错误处理和备用方案，确保操作能够成功执行
            - 特别是对于"回到主界面"操作，不要只依赖Home键，也要考虑通过手势(如从屏幕底部向上滑动)来实现

            对于不同类型的动作，handler提供以下方法:
            - handler.click(text) - 通过文本点击元素
            - handler.click_by_xpath(xpath) - 通过XPath点击元素
            - handler.click_by_coords(x, y) - 通过坐标点击
            - handler.input_text(text, input_value) - 在输入框中输入文本
            - handler.swipe(direction) - 滑动屏幕 (direction 可以是 'up', 'down', 'left', 'right')
            - handler.back() - 按返回键
            - handler.home() - 按Home键
            - handler.wait_for_element(text, timeout) - 等待元素出现

            代码示例:
            ```python
            def execute_test_step(d):
                # 回到主界面
                if handler.home():
                    print("通过Home键回到主界面")
                else:
                    print("Home键方式失败，尝试手势方式")
                    # 尝试从底部向上滑动（模拟手势导航）
                    if handler.swipe('up'):
                        print("通过手势成功回到主界面")
                    else:
                        print("返回主界面失败")
                        return False
                    
                return True
            ```

            请确保生成的代码中所有操作都通过handler变量执行。不要直接使用d对象。
            只返回代码，不要有其他任何解释。不要使用```python和```标记。
            """
        
        # 调用API生成脚本...""
            
            # 调用API生成脚本
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
            
            # 清理代码（删除可能的代码标记）
            if "```python" in code and "```" in code:
                code = code.split("```python", 1)[1].split("```", 1)[0].strip()
            elif "```" in code and "```" in code.split("```", 1)[1]:
                code = code.split("```", 1)[1].split("```", 1)[0].strip()
                
            return code
            
        except Exception as e:
            print(f"生成操作脚本时出错: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def validate_test_result(self, test_step: str, expected_result: str, xml_content: str, app_info: Dict[str, Any]) -> bool:
        """
        验证测试结果
        
        参数:
            test_step: 测试步骤
            expected_result: 预期结果
            xml_content: 元素XML内容
            app_info: 应用信息
            
        返回:
            验证结果，通过返回True，否则返回False
        """
        try:
            # 构建提示
            prompt = f"""
            你是一个专业的安卓UI自动化测试验证AI。你需要验证以下测试步骤的结果是否符合预期：
            
            测试步骤：{test_step}
            预期结果：{expected_result}
            
            当前应用信息:
            ```json
            {json.dumps(app_info, ensure_ascii=False, indent=2)}
            ```
            
            当前界面元素:
            ```xml
            {xml_content[:5000] if len(xml_content) > 5000 else xml_content}
            ```
            
            请仔细分析当前界面状态，判断是否符合预期结果。
            只回答"通过"或"失败"，并给出简短的理由。
            """
            
            # 调用API验证结果
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "You are a helpful android UI testing validator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # 低温度使结果更确定
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