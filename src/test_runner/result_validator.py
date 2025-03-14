class ResultValidator:
    def __init__(self, ai_client, element_parser):
        """结果验证器，验证测试结果是否符合预期
        
        Args:
            ai_client: AI客户端实例
            element_parser: 元素解析器实例
        """
        self.ai_client = ai_client
        self.element_parser = element_parser
    
    def validate_test_result(self, test_case, xml_content=None, app_info=None):
        """验证测试结果
        
        Args:
            test_case: 测试用例
            xml_content: XML元素内容（可选，如未提供会重新获取）
            app_info: 应用信息（可选，如未提供会重新获取）
        """
        # 如果未提供XML内容和应用信息，则重新获取
        if xml_content is None or app_info is None:
            print("未提供XML内容或应用信息，重新获取UI状态...")
            xml_content, app_info = self.element_parser.parse_ui_hierarchy()
        
        # 使用AI验证结果
        validation_result = self.ai_client.validate_test_result(test_case, xml_content, app_info)
        
        if validation_result:
            # 解析结果格式："结果: [pass/fail/uncertain]，原因: [简短说明]"
            parts = validation_result.split("，", 1)
            if len(parts) == 2:
                result_part = parts[0].strip()
                reason_part = parts[1].strip()
                
                result = result_part.split(":", 1)[1].strip().lower() if ":" in result_part else ""
                reason = reason_part.split(":", 1)[1].strip() if ":" in reason_part else ""
                
                # 标准化结果
                if result in ["pass", "通过"]:
                    return "pass", reason
                elif result in ["fail", "失败"]:
                    return "fail", reason
                else:
                    return "uncertain", reason
            
            # 如果无法按预期格式解析，尝试简单解析
            lower_result = validation_result.lower()
            if "pass" in lower_result:
                return "pass", validation_result
            elif "fail" in lower_result:
                return "fail", validation_result
            else:
                return "uncertain", validation_result
        
        return "uncertain", "无法解析AI验证结果"