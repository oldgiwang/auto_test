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
from src.ai_interface.ai_client import AIClient
from src.utils.data_loader import DataLoader
from src.utils.element_dictionary import ElementDictionary

def main():
    """主程序入口"""
    print("=== 安卓UI自动化测试系统 ===")
    
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
    
    # 加载测试用例
    test_cases = DataLoader.load_test_cases("data/test_cases.xlsx")
    if not test_cases:
        print("加载测试用例失败，请检查测试用例文件")
        return
    print(f"成功加载 {len(test_cases)} 个测试用例")
    
    # 初始化元素字典
    element_dict = ElementDictionary()
    
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
        
        # 加载元素字典
        element_dict.load_from_files(xml_path, app_info_path)
        element_dict_data = element_dict.get_all_elements()
        
        # 生成测试代码
        print("正在生成测试代码...")
        code = ai_client.generate_test_code(
            test_cases=test_cases,
            element_xml=element_xml,
            app_info=app_info,
            element_dict=element_dict_data,
            test_index=i
        )
        
        if not code:
            print("生成测试代码失败")
            test_case["test_result"] = "fail"
            results.append(test_case)
            continue
        
        # 显示生成的代码
        print(f"\n生成的测试代码:\n{'-'*50}\n{code}\n{'-'*50}")
        
        # 执行测试代码
        print("正在执行测试代码...")
        try:
            # 创建本地变量空间，包含设备对象
            local_vars = {"d": device}
            
            # 执行代码
            exec(code, globals(), local_vars)
            
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
            
            # 验证测试结果
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