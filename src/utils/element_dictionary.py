import xml.etree.ElementTree as ET
import json
import io

class ElementDictionary:
    def __init__(self):
        """初始化元素字典"""
        self.elements = {}
        self.app_info = {}
    
    def load_from_files(self, xml_path, app_info_path):
        """
        从XML和应用信息文件加载元素信息
        
        参数:
            xml_path: 元素XML文件路径
            app_info_path: 应用信息JSON文件路径
            
        返回:
            加载成功返回True，否则返回False
        """
        try:
            # 加载应用信息
            with open(app_info_path, 'r', encoding='utf-8') as f:
                self.app_info = json.load(f)
            
            # 读取XML文件并手动处理内容
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # 找到实际的XML开始位置
            if "<?xml" in xml_content:
                xml_start = xml_content.find("<?xml")
                xml_content = xml_content[xml_start:]
            
            # 使用ElementTree解析处理后的XML
            tree = ET.parse(io.StringIO(xml_content))
            root = tree.getroot()
            
            # 清空现有元素
            self.elements = {}
            
            # 解析元素信息
            self._parse_elements(root)
            
            return True
        except Exception as e:
            print(f"加载元素字典失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _parse_elements(self, node, parent_path=""):
        """递归解析XML元素树"""
        for i, child in enumerate(node):
            # 获取元素属性
            element_id = child.attrib.get('resource-id', '')
            text = child.attrib.get('text', '')
            content_desc = child.attrib.get('content-desc', '')
            class_name = child.attrib.get('class', '')
            bounds = child.attrib.get('bounds', '')
            
            # 生成友好的元素名称
            name = self._generate_element_name(element_id, text, content_desc, class_name)
            
            # 创建元素路径
            current_path = f"{parent_path}/{name}[{i}]" if parent_path else f"/{name}[{i}]"
            
            # 确定元素交互类型
            interactions = []
            if child.attrib.get('clickable') == 'true':
                interactions.append('点击')
            if child.attrib.get('long-clickable') == 'true':
                interactions.append('长按')
            if child.attrib.get('checkable') == 'true':
                interactions.append('勾选')
            if child.attrib.get('scrollable') == 'true':
                interactions.append('滚动')
            if child.attrib.get('editable') == 'true':
                interactions.append('编辑')
            
            # 解析元素边界
            if bounds:
                try:
                    # 通常格式为"[x1,y1][x2,y2]"
                    bounds = bounds.replace('][', ',').strip('[]').split(',')
                    bounds = [int(b) for b in bounds]
                    coords = {
                        'left': bounds[0],
                        'top': bounds[1],
                        'right': bounds[2],
                        'bottom': bounds[3],
                        'center_x': (bounds[0] + bounds[2]) // 2,
                        'center_y': (bounds[1] + bounds[3]) // 2
                    }
                except:
                    coords = {}
            else:
                coords = {}
            
            # 保存元素信息
            xpath = self._generate_xpath(child)
            self.elements[current_path] = {
                'name': name,
                'type': class_name,
                'text': text,
                'desc': content_desc,
                'resource_id': element_id,
                'possible_actions': interactions,
                'coords': coords,
                'xpath': xpath,
                'attribs': dict(child.attrib)
            }
            
            # 递归处理子元素
            self._parse_elements(child, current_path)
    
    def _generate_element_name(self, resource_id, text, desc, class_name):
        """生成友好的元素名称"""
        # 从资源ID提取名称
        if resource_id and '/' in resource_id:
            name = resource_id.split('/')[-1]
            return name
        
        # 如果有文本，使用文本
        if text:
            # 限制文本长度
            return text[:20].replace(' ', '_')
        
        # 如果有内容描述，使用内容描述
        if desc:
            return desc[:20].replace(' ', '_')
        
        # 如果都没有，使用类名
        if class_name:
            return class_name.split('.')[-1]
        
        # 如果还是没有，返回默认名称
        return "element"
    
    def _generate_xpath(self, element):
        """为元素生成XPath"""
        attribs = element.attrib
        class_name = attribs.get('class', '')
        
        # 基本XPath
        xpath = f"//{class_name}"
        
        # 添加资源ID条件
        if 'resource-id' in attribs and attribs['resource-id']:
            xpath += f"[@resource-id='{attribs['resource-id']}']"
        # 否则尝试添加文本条件
        elif 'text' in attribs and attribs['text']:
            xpath += f"[@text='{attribs['text']}']"
        # 否则尝试添加内容描述条件
        elif 'content-desc' in attribs and attribs['content-desc']:
            xpath += f"[@content-desc='{attribs['content-desc']}']"
        
        return xpath
    
    def get_element(self, identifier):
        """
        根据标识符获取元素信息
        
        参数:
            identifier: 元素标识符，可以是路径、名称、文本等
            
        返回:
            元素信息字典，未找到返回None
        """
        # 直接路径匹配
        if identifier in self.elements:
            return self.elements[identifier]
        
        # 尝试其他匹配方式
        for path, element in self.elements.items():
            # 匹配名称
            if element['name'] == identifier:
                return element
            
            # 匹配文本
            if element['text'] == identifier:
                return element
            
            # 匹配资源ID
            if element['resource_id'] == identifier or element['resource_id'].endswith(f"/{identifier}"):
                return element
        
        return None
    
    def get_all_elements(self):
        """获取所有元素信息，以便传递给AI"""
        return self.elements
    
    def get_app_info(self):
        """获取应用信息"""
        return self.app_info
    
    def get_element_summary(self):
        """返回元素摘要信息"""
        total = len(self.elements)
        interactive = sum(1 for e in self.elements.values() if e['possible_actions'])
        
        return {
            'total_elements': total,
            'interactive_elements': interactive,
            'non_interactive_elements': total - interactive,
            'app_package': self.app_info.get('current_app', {}).get('package', 'Unknown'),
            'app_activity': self.app_info.get('current_app', {}).get('activity', 'Unknown')
        }