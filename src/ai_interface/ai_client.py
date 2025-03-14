import json
import requests
import time
from typing import Dict, List, Any, Optional

class AIClient:
    def __init__(self, api_config):
        """AI客户端，负责与AI API交互
        
        Args:
            api_config: API配置信息
        """
        self.api_key = api_config.get("api_key")
        self.base_url = api_config.get("base_url")
        self.model = api_config.get("model")
        self.max_tokens = api_config.get("max_tokens", 4096)
        self.temperature = api_config.get("temperature", 0.7)
        self.max_retries = 3  # 最大重试次数
    
    def create_chat_completion(self, messages: List[Dict[str, str]], retry_count=0) -> Optional[str]:
        """调用AI API创建聊天完成
        
        Args:
            messages: 消息列表
            retry_count: 当前重试次数
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            print(f"发送API请求到 {self.base_url}...")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"API响应成功，获取到内容长度: {len(content)}")
                return content
            elif response.status_code == 429 and retry_count < self.max_retries:
                # 处理限流错误，等待后重试
                wait_time = min(2 ** retry_count, 8)  # 指数退避策略
                print(f"API请求限流，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                return self.create_chat_completion(messages, retry_count + 1)
            else:
                print(f"API请求失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                wait_time = min(2 ** retry_count, 8)
                print(f"API请求超时，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                return self.create_chat_completion(messages, retry_count + 1)
            else:
                print("API请求多次超时，放弃重试")
                return None
        except Exception as e:
            print(f"API请求异常: {e}")
            if retry_count < self.max_retries:
                wait_time = min(2 ** retry_count, 8)
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                return self.create_chat_completion(messages, retry_count + 1)
            return None
    
    def _identify_current_state(self, app_info):
        """根据应用信息识别当前界面状态
        
        Args:
            app_info: 应用信息字典
            
        Returns:
            识别出的界面状态描述
        """
        current_package = app_info.get('current_package', '')
        current_activity = app_info.get('current_activity', '')
        
        # 判断常见的界面
        if current_package == 'com.miui.home' and '.launcher.Launcher' in current_activity:
            return "主屏幕"
        elif current_package == 'com.android.settings':
            if current_activity.endswith('.Settings'):
                return "设置主界面"
            elif 'wifi' in current_activity.lower() or 'network' in current_activity.lower():
                return "WLAN设置界面"
            else:
                return "设置界面"
        
        # 返回一般性描述
        return f"{current_package} - {current_activity}"
            
    def get_action_plan(self, test_case: Dict[str, str], xml_content: str, app_info: Dict[str, Any]) -> str:
        """获取AI生成的动作计划
        
        Args:
            test_case: 测试用例
            xml_content: XML元素内容
            app_info: 应用信息
        """
        # 识别当前状态
        current_state = self._identify_current_state(app_info)
        test_step = test_case.get('测试步骤', '')
        expected_result = test_case.get('预期结果', '')
        
        # 特殊处理特定场景
        simple_plan = None
        
        # 情况1: 已经在主屏幕，测试要求是"回到主界面"
        if current_state == "主屏幕" and "回到主界面" in test_step:
            simple_plan = """# 已经在主界面，无需操作
print("当前已在主界面，符合要求")
# 为确保状态稳定，等待短暂时间
wait(1)"""
        
        # 情况2: 要求打开设置，当前已在设置界面
        elif "设置界面" in current_state and "打开设置" in test_step:
            simple_plan = """# 已经在设置界面，无需操作
print("当前已在设置界面，符合要求")
# 为确保状态稳定，等待短暂时间
wait(1)"""
            
        # 情况3: 需要打开设置，当前在主屏幕
        elif current_state == "主屏幕" and "打开设置" in test_step:
            simple_plan = """# 当前在主屏幕，需要打开设置
# 查找并点击设置图标
find_and_click_element(target_text="设置")
# 等待设置页面加载
wait(2)
# 验证是否进入设置界面
find_element_by_text("网络和互联网")"""
            
        # 情况4：需要打开WLAN设置，当前在设置界面
        elif "设置界面" in current_state and "打开wlan设置" in test_step:
            simple_plan = """# 当前在设置界面，需要打开WLAN设置
# 查找并点击网络和互联网或WLAN选项
if not find_and_click_element(target_text="网络和互联网"):
    find_and_click_element(target_text="WLAN")
# 等待WLAN设置页面加载
wait(2)
# 验证是否进入WLAN设置界面
find_element_by_text("WLAN") or find_element_by_text("Wi-Fi")"""
            
        # 情况5：需要打开WLAN开关，当前在WLAN设置界面
        elif "WLAN设置界面" in current_state and "打开wlan开关" in test_step:
            simple_plan = """# 当前在WLAN设置界面，需要打开WLAN开关
# 查找并点击WLAN开关
find_and_click_element(target_text="WLAN") or find_and_click_element(target_text="Wi-Fi")
# 等待WLAN扫描
wait(3)
# 验证是否有可用Wi-Fi列表
find_element_by_text("可用网络")"""
        
        # 如果有简单计划，直接返回
        if simple_plan:
            return simple_plan
            
        # 构建系统提示
        system_prompt = """
你是一个专业的移动应用UI自动化测试AI助手。你的任务是理解当前页面的状态信息和应用信息，并基于测试用例提供具体的UI交互动作步骤。

重要规则：
1. 只能使用UI交互操作，例如点击、滑动、输入文本等，模拟真实用户操作
2. 严禁使用后台操作或直接控制应用进程的方式
3. 必须通过UI元素分析和用户可见的交互方式完成测试
4. 优先使用系统级信息（如包名、活动名）来判断当前状态，避免不必要的元素查找
5. 生成最简洁有效的代码，避免冗余操作

你将收到以下信息：
1. 测试用例：包含测试步骤和预期结果
2. 当前页面状态：包含包名、活动名等系统信息
3. 当前页面XML：包含页面元素及其属性

对于元素交互，请注意：
1. 查找到的文本元素可能本身不可点击，需要找到其可点击的父容器
2. 分析页面布局确定滚动方向（垂直或水平）
3. 如果找不到元素，需要尝试滚动查找

请分析这些信息，并给出具体的交互动作指令。你的输出应该是清晰的Python风格伪代码，描述如何执行测试步骤。
        """
        
        # 限制XML内容长度，避免超出token限制
        max_xml_length = 4000
        truncated_xml = xml_content[:max_xml_length] if xml_content and len(xml_content) > max_xml_length else xml_content
        if truncated_xml and len(truncated_xml) < len(xml_content):
            truncated_xml += "\n<!-- XML内容已截断 -->"
        
        # 获取推荐滚动方向
        scroll_direction = app_info.get("recommended_scroll", "vertical")
        
        # 构建用户提示
        user_prompt = f"""
测试用例:
- 测试步骤: {test_step}
- 预期结果: {expected_result}

当前页面状态识别:
- 当前状态: {current_state}
- 包名: {app_info.get('current_package', '未知')}
- 活动名: {app_info.get('current_activity', '未知')}
- 屏幕尺寸: {app_info.get('screen_width', '?')}x{app_info.get('screen_height', '?')}
- 推荐滚动方向: {scroll_direction}

当前页面XML:
{truncated_xml if truncated_xml else '未获取到XML内容，请基于测试步骤和预期结果推断所需操作'}

请基于以上信息，特别是当前页面状态，提供最直接有效的操作步骤，避免冗余操作。请只输出Python风格的伪代码，不要包含任何解释或额外信息。
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.create_chat_completion(messages)
    
    def get_execution_code(self, action_plan: str, dictionary: Dict[str, Any]) -> str:
        """将动作计划转换为可执行代码
        
        Args:
            action_plan: 动作计划
            dictionary: 函数字典
        """
        # 构建系统提示
        system_prompt = """
你是一个专业的移动应用UI自动化测试AI助手。现在，你需要将高级动作计划转换为使用提供的函数字典的具体Python代码。

重要规则：
1. 只能使用UI交互操作，模拟真实用户操作
2. 严禁使用后台操作或直接控制应用进程的方式
3. 必须通过模拟用户点击、滑动等操作完成测试
4. 保持代码的简洁性，避免不必要的操作和验证

关于不可点击元素：
1. 当找到文本元素但它不可点击时，我们的函数会自动查找可点击的父容器
2. 点击操作应该针对UI元素的中心坐标

关于滚动操作：
1. 分析页面布局确定滚动方向（垂直或水平）
2. 如果需要水平滚动，使用scroll_horizontal函数
3. 对于列表和垂直内容，使用scroll_down和scroll_up

你将收到以下信息：
1. 动作计划：之前生成的Python风格伪代码
2. 函数字典：包含可用的函数及其参数

请将动作计划转换为可执行的Python代码，正确调用函数字典中的函数，并处理可能的异常情况。确保代码具有鲁棒性，每个操作后要给UI足够的响应时间。
        """
        
        # 构建用户提示
        user_prompt = f"""
动作计划:
{action_plan}

函数字典:
{json.dumps(dictionary, ensure_ascii=False, indent=2)}

请将动作计划转换为可执行的Python代码。代码应该调用字典中的函数，并处理可能的异常情况。请注意保持代码的简洁性，避免不必要的操作和重复验证。请只输出可执行的Python代码，不要包含任何解释或额外信息。
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.create_chat_completion(messages)
    
    def validate_test_result(self, test_case: Dict[str, str], xml_content: str = None, app_info: Dict[str, Any] = None) -> str:
        """验证测试结果
        
        Args:
            test_case: 测试用例
            xml_content: XML元素内容
            app_info: 应用信息
        """
        # 确保有xml_content和app_info
        if xml_content is None or app_info is None:
            # 该参数在旧版本接口中可能未提供，兼容处理
            from element_parser import ElementParser
            parser = ElementParser(None)
            xml_content, app_info = parser.parse_ui_hierarchy()
        
        # 识别当前状态
        current_state = self._identify_current_state(app_info)
        test_step = test_case.get('测试步骤', '')
        expected_result = test_case.get('预期结果', '')
            
        # 构建系统提示
        system_prompt = """
你是一个专业的移动应用UI自动化测试AI助手。你的任务是验证测试用例的执行结果是否符合预期。

验证策略:
1. 首先分析应用的系统级信息（包名、活动名）来判断当前状态
2. 然后检查UI元素是否符合预期结果的描述
3. 优先使用系统信息，避免过度依赖UI元素

你将收到以下信息：
1. 测试用例：包含测试步骤和预期结果
2. 当前页面状态：系统识别的状态描述
3. 当前页面XML：包含页面元素及其属性

请分析这些信息，判断测试是否通过。返回"pass"或"fail"，并简短说明原因。如果没有足够信息判断，请返回"uncertain"并说明原因。
        """
        
        # 限制XML内容长度
        max_xml_length = 4000
        truncated_xml = xml_content[:max_xml_length] if xml_content and len(xml_content) > max_xml_length else xml_content
        if truncated_xml and len(truncated_xml) < len(xml_content):
            truncated_xml += "\n<!-- XML内容已截断 -->"
        
        # 构建用户提示
        user_prompt = f"""
测试用例:
- 测试步骤: {test_step}
- 预期结果: {expected_result}

当前页面状态识别:
- 当前状态: {current_state}
- 包名: {app_info.get('current_package', '未知')}
- 活动名: {app_info.get('current_activity', '未知')}

当前页面XML:
{truncated_xml if truncated_xml else '未获取到XML内容'}

请验证测试结果是否符合预期。回复格式为："结果: [pass/fail/uncertain]，原因: [简短说明]"
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.create_chat_completion(messages)