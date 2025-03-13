from typing import Dict, Any, Optional

class ResultValidator:
    """验证测试结果是否符合预期"""
    
    def __init__(self, ai_client):
        """
        初始化结果验证器
        
        参数:
            ai_client: AI客户端实例，用于调用AI进行结果验证
        """
        self.ai_client = ai_client
    
    def validate_result(self, 
                       test_step: Dict[str, Any], 
                       expected_result: str,
                       element_xml: str,
                       app_info: Dict[str, Any],
                       prompt: str) -> bool:
        """
        验证测试结果是否符合预期
        
        参数:
            test_step: 测试步骤信息
            expected_result: 预期结果
            element_xml: 当前UI元素XML
            app_info: 当前应用信息
            prompt: 验证提示
            
        返回:
            验证成功返回True，否则返回False
        """
        return self.ai_client.validate_result(
            prompt=prompt, 
            test_step=test_step,
            expected_result=expected_result,
            element_xml=element_xml,
            app_info=app_info
        )