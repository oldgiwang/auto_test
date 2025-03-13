import os
import sys
import json
import time
import traceback

# 添加src目录到系统路径
sys.path.append(os.path.abspath("src"))

from src.ui_automator.device_controller import DeviceController
from src.ui_automator.element_parser import ElementParser
from src.ui_automator.interaction_handler import InteractionHandler
from src.ai_interface.ai_client import AIClient
from src.utils.data_loader import DataLoader

def main():
    """主程序入口"""
    print("=== 安卓UI自动化测试系统 (简化版) ===")
    
    # 步骤1: 初始化设备控制器并连接设备
    device_controller = DeviceController()
    if not device_controller.connect():
        print("连接设备失败，请检查设备连接")
        return
    print("设备连接成功")
    
    # 获取设备实例
    device = device_controller.get_device()
    
    # 步骤2: 初始化元素解析器
    element_parser = ElementParser(device)
    
    # 步骤3: 初始化AI客户端
    ai_client = AIClient("config/api_config.json")
    
    # 步骤4: 加载测试用例
    test_cases = DataLoader.load_test_cases("data/test_cases.xlsx")
    if not test_cases:
        print("加载测试用例失败，请检查测试用例文件")
        return
    print(f"成功加载 {len(test_cases)} 个测试用例")
    
    # 执行测试
    results = []
    for i, test_case in enumerate(test_cases):
        print(f"\n=== 测试步骤 {i+1}/{len(test_cases)}: {test_case['test_step']} ===")
        
        # 提示用户准备执行
        input(f"按回车键开始执行测试步骤 {i+1}...")
        
        # 步骤5: 提取当前UI元素和应用信息
        xml_path = "data/element.xml"
        app_info_path = "data/app_info.json"
        simplified_elements_path = "data/simplified_elements.json"

        print("正在分析当前界面...")
        if not element_parser.extract_elements(xml_path, app_info_path):
            print("提取UI元素失败")
            test_case["test_result"] = "fail"
            results.append(test_case)
            continue

        # 提取并简化元素信息
        print("正在生成简化元素结构...")
        simplified_elements = element_parser.extract_simplified_elements(xml_path, simplified_elements_path)
        print(f"提取了 {len(simplified_elements)} 个可交互元素")

        # 加载元素XML和应用信息
        xml_content = DataLoader.load_element_xml(xml_path)
        app_info = DataLoader.load_app_info(app_info_path)
        simplified_elements_json = json.dumps(simplified_elements, ensure_ascii=False, indent=2)

        if not xml_content or not app_info:
            print("加载UI元素数据失败")
            test_case["test_result"] = "fail"
            results.append(test_case)
            continue

        # 步骤6: 获取AI分析的高级动作
        print("正在分析测试步骤，提取高级动作...")
        actions = ai_client.analyze_test_step(
            test_step=test_case['test_step'],
            xml_content=xml_content,
            app_info=app_info,
            simplified_elements=simplified_elements_json
        )

        if not actions:
            print("未提取到有效动作")
            test_case["test_result"] = "fail"
            results.append(test_case)
            continue
    
        print(f"提取的高级动作: {json.dumps(actions, ensure_ascii=False, indent=2)}")

        # 步骤7: 生成具体操作脚本
        print("正在生成操作脚本...")
        operation_script = ai_client.generate_operation_script(
            actions=actions,
            xml_content=xml_content,
            app_info=app_info,
            simplified_elements=simplified_elements_json
        )

        if not operation_script:
            print("生成操作脚本失败")
            test_case["test_result"] = "fail"
            results.append(test_case)
            continue

        # 显示生成的代码
        print(f"\n生成的操作脚本:\n{'-'*50}\n{operation_script}\n{'-'*50}")
        
        # 步骤8: 执行操作脚本
        print("正在执行操作脚本...")
        try:
            # 创建交互处理器
            interaction_handler = InteractionHandler(device)
    
            # 修改这里: 把交互处理器提前添加到全局变量
            globals()['handler'] = interaction_handler
    
            # 创建本地变量空间
            local_vars = {
                "d": device,
                "handler": interaction_handler  # 确保这个变量被传入
            }
            
            # 在执行代码前，将 handler 添加到全局命名空间
            globals()["handler"] = interaction_handler

            # 执行代码
            exec(operation_script, globals(), local_vars)

            # 调用生成的函数
            result = False
            if "execute_test_step" in local_vars:
                result = local_vars["execute_test_step"](device)
            
            if not result:
                print("测试步骤执行失败")
                test_case["test_result"] = "fail"
                results.append(test_case)
                continue
            
            # 等待UI更新
            time.sleep(2)
            
            # 步骤9: 再次提取UI元素，用于验证结果
            print("正在分析执行结果...")
            if not element_parser.extract_elements(xml_path, app_info_path):
                print("提取UI元素失败，无法验证结果")
                test_case["test_result"] = "fail"
                results.append(test_case)
                continue
            
            # 重新加载元素信息
            xml_content = DataLoader.load_element_xml(xml_path)
            app_info = DataLoader.load_app_info(app_info_path)
            
            # 步骤10: 验证测试结果
            print("正在验证测试结果...")
            validation_result = ai_client.validate_test_result(
                test_step=test_case['test_step'],
                expected_result=test_case['expected_result'],
                xml_content=xml_content,
                app_info=app_info
            )
            
            # 更新测试结果
            test_case["test_result"] = "pass" if validation_result else "fail"
            print(f"测试结果: {'✅ 通过' if validation_result else '❌ 失败'}")
            
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