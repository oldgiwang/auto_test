import os
import sys
import time
import json
import traceback
from pathlib import Path

# 添加src目录到系统路径
sys.path.append(os.path.abspath("src"))

from src.ui_automator.element_parser import ElementParser
from src.ui_automator.device_controller import DeviceController
from src.ui_automator.interaction_handler import InteractionHandler
from src.ai_interface.ai_client import AIClient
from src.ai_interface.improved_action_analyzer import ImprovedActionAnalyzer
from src.utils.data_loader import DataLoader
from src.utils.improved_element_dictionary import ImprovedElementDictionary

def main():
    """主程序入口"""
    print("=== 安卓UI自动化测试系统 (改进版) ===")
    
    # 初始化设备控制器
    device_controller = DeviceController()
    if not device_controller.connect():
        print("连接设备失败，请检查设备连接")
        return
    print("设备连接成功")
    
    # 获取设备实例
    device = device_controller.get_device()
    
    # 初始化元素解析器
    element_parser = ElementParser(device)
    
    # 初始化AI客户端
    ai_client = AIClient("config/api_config.json")
    
    # 初始化动作分析器
    action_analyzer = ImprovedActionAnalyzer(ai_client)
    
    # 加载测试用例
    test_cases = DataLoader.load_test_cases("data/test_cases.xlsx")
    if not test_cases:
        print("加载测试用例失败，请检查测试用例文件")
        return
    print(f"成功加载 {len(test_cases)} 个测试用例")
    
    # 初始化增强版元素字典
    element_dict = ImprovedElementDictionary()
    
    # 执行测试
    results = []
    for i, test_case in enumerate(test_cases):
        print(f"\n=== 测试步骤 {i+1}/{len(test_cases)}: {test_case['test_step']} ===")
        
        # 提示用户准备执行
        input(f"按回车键开始执行测试步骤 {i+1}...")
        
        # 提取当前UI元素和应用信息
        xml_path = "data/element.xml"
        app_info_path = "data/app_info.json"
        
        print("正在分析当前界面...")
        if not element_parser.extract_elements(xml_path, app_info_path):
            print("提取UI元素失败")
            test_case["test_result"] = "fail"
            results.append(test_case)
            continue
        
        # 加载元素XML和应用信息
        element_xml = DataLoader.load_element_xml(xml_path)
        app_info = DataLoader.load_app_info(app_info_path)
        
        # 加载增强版元素字典
        element_dict.load_from_files(xml_path, app_info_path)
        element_dict_data = element_dict.elements
        
        # 初始化交互处理器
        interaction_handler = InteractionHandler(device, element_dict)
        
        # 步骤1: 分析测试用例，获取高级动作
        print("正在分析测试步骤，提取高级动作...")
        action_result = action_analyzer.analyze_task(test_case['test_step'])
        actions = action_result.get('actions', [])
        
        if not actions:
            print("未提取到有效动作")
            test_case["test_result"] = "fail"
            results.append(test_case)
            continue
            
        print(f"提取的高级动作: {json.dumps(actions, ensure_ascii=False, indent=2)}")
        
        # 步骤2: 根据高级动作和元素字典生成具体操作脚本
        print("正在生成操作脚本...")
        operation_script = action_analyzer.generate_interaction_code(actions, element_dict_data, app_info)
        
        if not operation_script:
            print("生成操作脚本失败")
            test_case["test_result"] = "fail"
            results.append(test_case)
            continue
        
        # 显示生成的代码
        print(f"\n生成的操作脚本:\n{'-'*50}\n{operation_script}\n{'-'*50}")
        
        # 步骤3: 执行操作脚本
        print("正在执行操作脚本...")
        try:
            # 创建本地变量空间，包含设备对象和元素字典
            local_vars = {
                "d": device,
                "element_dict": element_dict_data
            }
            
            # 执行代码
            exec(operation_script, globals(), local_vars)
            
            # 调用生成的函数
            if "execute_test_step" in local_vars:
                result = local_vars["execute_test_step"](device)
                if not result:
                    print("测试步骤执行失败")
                    test_case["test_result"] = "fail"
                    results.append(test_case)
                    continue
            else:
                print("未找到execute_test_step函数")
                test_case["test_result"] = "fail"
                results.append(test_case)
                continue
            
            # 等待UI更新
            time.sleep(2)
            
            # 再次提取UI元素，用于验证结果
            print("正在分析执行结果...")
            if not element_parser.extract_elements(xml_path, app_info_path):
                print("提取UI元素失败，无法验证结果")
                test_case["test_result"] = "fail"
                results.append(test_case)
                continue
            
            # 重新加载元素信息
            element_xml = DataLoader.load_element_xml(xml_path)
            app_info = DataLoader.load_app_info(app_info_path)
            
            # 步骤4: 验证测试结果
            print("正在验证测试结果...")
            result_passed = ai_client.validate_test_result(
                test_case=test_case,
                element_xml=element_xml,
                app_info=app_info
            )
            
            # 更新测试结果
            test_case["test_result"] = "pass" if result_passed else "fail"
            print(f"测试结果: {'✅ 通过' if result_passed else '❌ 失败'}")
            
        except Exception as e:
            print(f"执行测试代码时出错: {e}")
            traceback.print_exc()
            test_case["test_result"] = "fail"
        
        # 添加结果
        results.append(test_case)
    
    # 保存测试结果
    result_file = "results/test_results.xlsx"
    os.makedirs(os.path.dirname(result_file), exist_ok=True)
    if DataLoader.save_test_results(result_file, results):
        print(f"\n测试结果已保存到 {os.path.abspath(result_file)}")
    
    # 显示测试总结
    passed = sum(1 for r in results if r["test_result"] == "pass")
    total = len(results)
    print(f"\n=== 测试完成: {passed}/{total} 通过 ===")

if __name__ == "__main__":
    main()