from typing import List, Dict, Any, Optional
import json

class ImprovedActionAnalyzer:
    """分析测试任务并生成高级操作动作，适配新的交互处理框架"""
    
    def __init__(self, ai_client):
        """
        初始化动作分析器
        
        参数:
            ai_client: AI客户端实例，用于调用AI服务
        """
        self.ai_client = ai_client
    
    def analyze_task(self, test_step: str) -> Dict[str, Any]:
        """
        分析测试步骤，提取高级动作
        
        参数:
            test_step: 测试步骤描述
            
        返回:
            包含动作类型和参数的字典，或动作列表
        """
        # 构建提示
        prompt = f"""
        你是一个专注于UI操作分析的AI。请分析以下安卓测试步骤，并提取出要执行的高级动作。

        测试步骤: {test_step}

        请将动作分解为以下格式之一:
        1. 对于打开操作: {{"action": "OPEN", "target": "应用名称"}}
        2. 对于点击操作: {{"action": "CLICK", "target": "元素名称", "description": "点击描述"}}
        3. 对于输入操作: {{"action": "INPUT", "target": "输入框名称", "text": "要输入的文本"}}
        4. 对于滑动操作: {{"action": "SWIPE", "direction": "方向(UP/DOWN/LEFT/RIGHT)"}}
        5. 对于检查操作: {{"action": "CHECK", "target": "元素名称", "condition": "条件描述"}}
        6. 对于等待操作: {{"action": "WAIT", "target": "元素名称", "timeout": 超时秒数}}
        7. 对于返回操作: {{"action": "BACK"}}
        8. 对于回主页操作: {{"action": "HOME"}}

        如果测试步骤涉及多个动作，请返回动作列表:
        [
            {{"action": "CLICK", "target": "设置"}},
            {{"action": "CLICK", "target": "WLAN"}}
        ]

        只返回JSON格式的动作，不要有其他任何解释。
        """
        
        # 调用AI获取动作分析
        action_json = self.ai_client.get_action_analysis(prompt)
        
        # 规范化结果
        if isinstance(action_json, list):
            # 如果是动作列表，返回原样
            return {"actions": action_json}
        elif isinstance(action_json, dict) and "action" in action_json:
            # 如果是单个动作，包装为列表
            return {"actions": [action_json]}
        else:
            # 其他情况，尝试处理或返回默认值
            print("动作分析结果格式不符合预期")
            return {"actions": [{"action": "UNKNOWN", "target": "UNKNOWN"}]}
    
    def generate_interaction_code(self, actions: List[Dict[str, Any]], element_dict: Dict[str, Any], app_info: Dict[str, Any]) -> str:
        """
        根据高级动作和元素字典生成交互代码
        
        参数:
            actions: 高级动作列表
            element_dict: 元素字典
            app_info: 应用信息
            
        返回:
            可执行的Python脚本
        """
        # 为交互处理器创建函数模板
        code_template = """
def execute_test_step(d):
    from src.ui_automator.interaction_handler import InteractionHandler
    from src.utils.improved_element_dictionary import ImprovedElementDictionary
    
    # 初始化交互处理器
    element_dict = ImprovedElementDictionary()
    element_dict_data = element_dict
    handler = InteractionHandler(d, element_dict_data)
    
    # 执行操作序列
{operations}
    
    return True  # 如果所有操作都成功执行
"""
        
        # 生成操作代码
        operations = []
        for i, action in enumerate(actions):
            action_type = action.get('action', 'UNKNOWN').upper()
            target = action.get('target', '')
            
            # 根据不同动作类型生成代码
            if action_type == 'OPEN':
                operations.append(f'    # 打开"{target}"\n    success = handler.find_and_perform_action("OPEN", "{target}")')
            
            elif action_type == 'CLICK':
                operations.append(f'    # 点击"{target}"\n    success = handler.find_and_perform_action("CLICK", "{target}")')
            
            elif action_type == 'INPUT':
                text = action.get('text', '')
                operations.append(f'    # 在"{target}"中输入"{text}"\n    success = handler.find_and_perform_action("INPUT", "{target}", text="{text}")')
            
            elif action_type == 'SWIPE':
                direction = action.get('direction', 'UP')
                operations.append(f'    # {direction}方向滑动\n    success = handler.find_and_perform_action("SWIPE", "", direction="{direction}")')
            
            elif action_type == 'CHECK':
                condition = action.get('condition', '')
                operations.append(f'    # 检查"{target}"{f" ({condition})" if condition else ""}\n    success = handler.find_and_perform_action("CHECK", "{target}")')
            
            elif action_type == 'WAIT':
                timeout = action.get('timeout', 10)
                operations.append(f'    # 等待"{target}"出现\n    success = handler.find_and_perform_action("WAIT", "{target}", timeout={timeout})')
            
            elif action_type == 'BACK':
                operations.append(f'    # 按返回键\n    success = handler.find_and_perform_action("BACK", "")')
            
            elif action_type == 'HOME':
                operations.append(f'    # 按Home键\n    success = handler.find_and_perform_action("HOME", "")')
            
            else:
                operations.append(f'    # 未知操作: {action}\n    print("未支持的操作类型: {action_type}")\n    success = False')
            
            # 添加检查
            operations.append(f'    if not success:\n        print("步骤 {i+1} 失败: {action_type} {target}")\n        return False\n')
        
        # 如果没有操作，添加默认操作
        if not operations:
            operations.append('    print("没有操作需要执行")\n')
        
        # 拼接操作代码
        operations_code = '\n'.join(operations)
        
        # 填充模板
        code = code_template.format(operations=operations_code)
        return code