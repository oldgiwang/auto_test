class PromptGenerator:
    """生成AI提示的工具类"""
    
    @staticmethod
    def generate_test_execution_prompt(test_step: str, test_step_number: int, total_steps: int) -> str:
        """
        生成执行测试的提示
        
        参数:
            test_step: 测试步骤描述
            test_step_number: 当前步骤编号
            total_steps: 总步骤数
            
        返回:
            生成的提示字符串
        """
        return f"""
        你是一个专业的安卓应用自动化测试AI。你需要生成Python代码来执行以下测试步骤：
        
        当前步骤 {test_step_number}/{total_steps}：{test_step}
        
        你的任务是生成可以使用uiautomator2库执行此步骤的Python代码。
        
        你的代码应该是完整的、可执行的，并且可以直接操作安卓设备。
        使用提供的UI元素树和应用信息来找到所需的元素，并使用适当的方法来执行操作。
        
        请生成具体、精确的代码。不要使用假设的元素ID或路径，只使用UI元素树中实际存在的元素。
        不要包含任何注释或解释，只提供可执行的代码。
        
        注意：代码会直接执行，不会被人工修改，所以请确保代码的正确性和鲁棒性。
        """
    
    @staticmethod
    def generate_result_validation_prompt(test_step: str, expected_result: str) -> str:
        """
        生成验证测试结果的提示
        
        参数:
            test_step: 测试步骤描述
            expected_result: 预期结果描述
            
        返回:
            生成的提示字符串
        """
        return f"""
        你是一个专业的安卓应用自动化测试验证AI。你需要验证以下测试步骤的结果是否符合预期：
        
        测试步骤：{test_step}
        预期结果：{expected_result}
        
        请仔细分析提供的UI元素树和应用信息，判断当前界面状态是否符合预期结果。
        只回答"通过"或"失败"，并给出简短的理由。
        
        如果当前状态符合预期结果，回答"通过"。
        如果当前状态不符合预期结果，回答"失败"。
        """