import os
import sys
import time
from src.utils.data_loader import DataLoader
from src.ui_automator.device_controller import DeviceController
from src.ui_automator.element_parser import ElementParser
from src.ui_automator.interaction_handler import InteractionHandler
from src.ai_interface.ai_client import AIClient
from src.test_runner.code_executor import CodeExecutor
from src.test_runner.result_validator import ResultValidator

# 设备ID
DEVICE_ID = "6hvok77taerg4hs4"

def print_separator():
    """打印分隔线"""
    print("\n" + "=" * 80 + "\n")

def run_test(test_case, data_loader, ai_client, code_executor, result_validator):
    """运行单个测试用例
    
    Args:
        test_case: 测试用例
        data_loader: 数据加载器
        ai_client: AI客户端
        code_executor: 代码执行器
        result_validator: 结果验证器
    """
    print(f"正在执行测试: {test_case['测试步骤']}")
    print(f"预期结果: {test_case['预期结果']}")
    print_separator()
    
    try:
        # 1. 获取当前UI状态
        print("正在获取初始UI状态...")
        xml_content, app_info = code_executor.element_parser.parse_ui_hierarchy()
        
        # 保存UI状态（只有在成功获取时才保存）
        if xml_content:
            data_loader.save_element_xml(xml_content)
        if app_info:
            data_loader.save_app_info(app_info)
        
        print("已获取当前UI状态")
        if not xml_content:
            print("警告: 未能获取XML内容，将使用默认或之前保存的内容")
            xml_content = data_loader.load_element_xml() or "<!-- XML内容获取失败 -->"
        
        if not app_info:
            print("警告: 未能获取应用信息，将使用默认或之前保存的信息")
            app_info = data_loader.load_app_info() or {"error": "应用信息获取失败"}
        
        print_separator()
        
        # 2. 获取动作计划
        print("正在分析UI并生成动作计划...")
        action_plan = ai_client.get_action_plan(test_case, xml_content, app_info)
        
        if not action_plan:
            print("获取动作计划失败，尝试使用简化信息重试...")
            # 简化信息重试
            simplified_info = {
                "test_step": test_case['测试步骤'],
                "expected_result": test_case['预期结果']
            }
            action_plan = ai_client.get_action_plan(test_case, "<!-- 简化XML -->", simplified_info)
            
            if not action_plan:
                print("获取动作计划失败")
                return "fail", "获取动作计划失败"
        
        print("动作计划:")
        print(action_plan)
        print_separator()
        
        # 3. 获取函数字典
        function_dict = code_executor.get_function_dictionary()
        
        # 4. 获取可执行代码
        print("正在生成可执行代码...")
        execution_code = ai_client.get_execution_code(action_plan, function_dict)
        
        if not execution_code:
            print("获取可执行代码失败")
            return "fail", "获取可执行代码失败"
        
        print("可执行代码:")
        print(execution_code)
        print_separator()
        
        # 5. 执行代码
        print("正在执行测试...")
        success, error_msg = code_executor.execute_code(execution_code)
        
        if not success:
            print(f"执行失败: {error_msg}")
            return "fail", f"执行失败: {error_msg}"
        
        print("执行完成")
        print_separator()
        
        # 6. 再次获取UI状态用于验证结果
        print("正在获取执行后的UI状态...")
        time.sleep(2)  # 给UI足够的时间响应
        post_xml_content, post_app_info = code_executor.element_parser.parse_ui_hierarchy()
        
        # 保存执行后的UI状态
        if post_xml_content:
            data_loader.save_element_xml(post_xml_content)
        if post_app_info:
            data_loader.save_app_info(post_app_info)
        
        print("已获取最新UI状态")
        print_separator()
        
        # 7. 验证测试结果
        print("正在验证测试结果...")
        result, reason = result_validator.validate_test_result(test_case, post_xml_content, post_app_info)
        
        print(f"测试结果: {result}")
        print(f"原因: {reason}")
        print_separator()
        
        return result, reason
    
    except Exception as e:
        import traceback
        error_msg = f"测试执行过程中发生异常: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return "fail", error_msg

def main():
    """主函数"""
    print("开始启动自动化测试系统...")
    
    try:
        # 确保数据目录存在
        os.makedirs("data", exist_ok=True)
        os.makedirs("config", exist_ok=True)
        
        # 初始化数据加载器
        data_loader = DataLoader()
        
        # 加载API配置
        api_config = data_loader.load_api_config()
        
        # 初始化设备控制器，使用指定的设备ID
        device_controller = DeviceController(device_id=DEVICE_ID)
        
        # 初始化元素解析器
        element_parser = ElementParser(device_controller)
        
        # 初始化交互处理器
        interaction_handler = InteractionHandler(device_controller, element_parser)
        
        # 初始化AI客户端
        ai_client = AIClient(api_config)
        
        # 初始化代码执行器
        code_executor = CodeExecutor(interaction_handler)
        
        # 初始化结果验证器
        result_validator = ResultValidator(ai_client, element_parser)
        
        # 加载测试用例
        test_cases = data_loader.load_test_cases()
        
        print(f"共加载 {len(test_cases)} 条测试用例")
        
        # 逐条执行测试用例
        for index, test_case in test_cases.iterrows():
            test_num = index + 1
            print(f"\n正在准备执行测试 {test_num}: {test_case['测试步骤']}")
            
            # 等待用户按回车继续
            input("按回车执行此测试用例...")
            
            result, reason = run_test(test_case, data_loader, ai_client, code_executor, result_validator)
            
            # 保存测试结果
            try:
                data_loader.save_test_result(test_num, result)
            except Exception as e:
                print(f"保存测试结果失败: {e}")
            
            print(f"测试 {test_num} 完成: {result}")
        
        print("\n所有测试用例执行完毕")
    
    except Exception as e:
        import traceback
        print(f"程序运行异常: {str(e)}")
        print(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())