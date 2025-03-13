import xml.etree.ElementTree as ET
import json
import io
import uuid

class ImprovedElementDictionary:
    """增强版元素字典，提供更好的元素索引和分类功能"""
    
    def __init__(self):
        """初始化元素字典"""
        self.elements = {}
        self.interactive_elements = {}  # 专门存储可交互的元素
        self.element_index = {}  # 元素索引：通过文本、资源ID等快速查找元素
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
            
            # 清空现有元素和索引
            self.elements = {}
            self.interactive_elements = {}
            self.element_index = {
                'by_text': {},
                'by_resource_id': {},
                'by_content_desc': {},
                'by_class': {}
            }
            
            # 解析元素信息
            self._parse_elements(root)
            print(f"加载了 {len(self.elements)} 个元素，其中 {len(self.interactive_elements)} 个可交互元素")
            
            return True
        except Exception as e:
            print(f"加载元素字典失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _parse_elements(self, node, parent_path="", depth=0):
        """递归解析XML元素树，生成元素字典和索引"""
        for i, child in enumerate(node):
            # 生成元素ID - 使用UUID确保唯一性
            element_id = f"element_{uuid.uuid4().hex[:8]}"
            
            # 获取元素属性
            resource_id = child.attrib.get('resource-id', '')
            text = child.attrib.get('text', '')
            content_desc = child.attrib.get('content-desc', '')
            class_name = child.attrib.get('class', '')
            bounds = child.attrib.get('bounds', '')
            package = child.attrib.get('package', '')
            
            # 判断元素是否可交互
            clickable = child.attrib.get('clickable') == 'true'
            long_clickable = child.attrib.get('long-clickable') == 'true'
            checkable = child.attrib.get('checkable') == 'true'
            scrollable = child.attrib.get('scrollable') == 'true'
            editable = child.attrib.get('editable') == 'true'
            
            # 确定元素是否可交互
            is_interactive = clickable or long_clickable or checkable or scrollable or editable
            
            # 生成友好的元素名称
            name = self._generate_element_name(resource_id, text, content_desc, class_name)
            
            # 创建元素路径 - 使用更友好的路径结构
            current_path = f"{parent_path}/{name}[{i}]" if parent_path else f"/{name}[{i}]"
            
            # 解析元素边界
            coords = {}
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
                        'center_y': (bounds[1] + bounds[3]) // 2,
                        'width': bounds[2] - bounds[0],
                        'height': bounds[3] - bounds[1]
                    }
                except:
                    coords = {}
            
            # 确定元素交互类型
            interactions = []
            if clickable:
                interactions.append('点击')
            if long_clickable:
                interactions.append('长按')
            if checkable:
                interactions.append('勾选')
            if scrollable:
                interactions.append('滚动')
            if editable:
                interactions.append('编辑')
                
            # 生成更专业的XPath
            xpath = self._generate_xpath(child)
            
            # 创建元素信息字典
            element_info = {
                'id': element_id,
                'name': name,
                'path': current_path,
                'type': class_name,
                'text': text,
                'desc': content_desc,
                'resource_id': resource_id,
                'package': package,
                'visible': child.attrib.get('visible-to-user') == 'true',
                'enabled': child.attrib.get('enabled') == 'true',
                'focused': child.attrib.get('focused') == 'true',
                'clickable': clickable,
                'long_clickable': long_clickable,
                'checkable': checkable,
                'checked': child.attrib.get('checked') == 'true',
                'scrollable': scrollable,
                'editable': editable,
                'possible_actions': interactions,
                'coords': coords,
                'xpath': xpath,
                'depth': depth,
                'is_interactive': is_interactive,
                'children_count': len(child)
            }
            
            # 保存元素信息
            self.elements[element_id] = element_info
            
            # 如果元素可交互，添加到交互式元素列表
            if is_interactive:
                self.interactive_elements[element_id] = element_info
            
            # 添加到索引
            if text:
                self.element_index['by_text'][text] = element_id
            if resource_id:
                self.element_index['by_resource_id'][resource_id] = element_id
                # 同时为短资源ID建立索引（去掉包名部分）
                if '/' in resource_id:
                    short_id = resource_id.split('/')[-1]
                    self.element_index['by_resource_id'][short_id] = element_id
            if content_desc:
                self.element_index['by_content_desc'][content_desc] = element_id
            if class_name:
                if class_name not in self.element_index['by_class']:
                    self.element_index['by_class'][class_name] = []
                self.element_index['by_class'][class_name].append(element_id)
            
            # 递归处理子元素
            self._parse_elements(child, current_path, depth + 1)
    
    def _generate_element_name(self, resource_id, text, desc, class_name):
        """生成友好的元素名称"""
        # 从资源ID提取名称
        if resource_id and '/' in resource_id:
            name = resource_id.split('/')[-1]
            return name
        
        # 如果有文本，使用文本
        if text:
            # 限制文本长度
            return text[:20].replace(' ', '_').replace('\n', '_')
        
        # 如果有内容描述，使用内容描述
        if desc:
            return desc[:20].replace(' ', '_').replace('\n', '_')
        
        # 如果都没有，使用类名
        if class_name:
            return class_name.split('.')[-1]
        
        # 如果还是没有，返回默认名称
        return "element"
    
    def _generate_xpath(self, element):
        """为元素生成更精确的XPath"""
        attribs = element.attrib
        class_name = attribs.get('class', '')
        
        # 基本XPath
        xpath = f"//{class_name}"
        
        # 添加多个条件使XPath更精确
        conditions = []
        
        # 添加资源ID条件
        if 'resource-id' in attribs and attribs['resource-id']:
            conditions.append(f"@resource-id='{attribs['resource-id']}'")
        
        # 添加文本条件
        if 'text' in attribs and attribs['text']:
            conditions.append(f"@text='{attribs['text']}'")
        
        # 添加内容描述条件
        if 'content-desc' in attribs and attribs['content-desc']:
            conditions.append(f"@content-desc='{attribs['content-desc']}'")
        
        # 添加位置条件
        if 'bounds' in attribs and attribs['bounds']:
            conditions.append(f"@bounds='{attribs['bounds']}'")
        
        # 组合条件
        if conditions:
            xpath += f"[{' and '.join(conditions)}]"
        
        return xpath
    
    def find_element(self, query, by='auto'):
        """
        智能查找元素
        
        参数:
            query: 查询字符串（文本、资源ID等）
            by: 查找方式，可以是'text', 'resource_id', 'content_desc', 'class', 'auto'
            
        返回:
            找到的元素信息，未找到返回None
        """
        element_id = None
        
        if by == 'auto':
            # 自动尝试各种方式查找
            for method in ['text', 'resource_id', 'content_desc']:
                element_id = self.find_element_id(query, method)
                if element_id:
                    break
                    
            # 如果还没找到，尝试模糊匹配
            if not element_id:
                element_id = self.find_element_id_fuzzy(query)
        else:
            # 使用指定方式查找
            element_id = self.find_element_id(query, by)
        
        # 返回找到的元素
        return self.elements.get(element_id) if element_id else None
    
    def find_element_id(self, query, by='text'):
        """根据不同方式查找元素ID"""
        if by == 'text':
            return self.element_index['by_text'].get(query)
        elif by == 'resource_id':
            return self.element_index['by_resource_id'].get(query)
        elif by == 'content_desc':
            return self.element_index['by_content_desc'].get(query)
        elif by == 'class':
            class_elements = self.element_index['by_class'].get(query, [])
            return class_elements[0] if class_elements else None
        return None
    
    def find_element_id_fuzzy(self, query):
        """使用模糊匹配查找元素ID"""
        # 搜索文本包含
        for text, element_id in self.element_index['by_text'].items():
            if query.lower() in text.lower():
                return element_id
        
        # 搜索资源ID包含
        for res_id, element_id in self.element_index['by_resource_id'].items():
            if query.lower() in res_id.lower():
                return element_id
                
        # 搜索内容描述包含
        for desc, element_id in self.element_index['by_content_desc'].items():
            if query.lower() in desc.lower():
                return element_id
                
        return None
    
    def find_all_interactive_elements(self):
        """获取所有可交互元素"""
        return self.interactive_elements
    
    def get_element_by_id(self, element_id):
        """通过ID获取元素"""
        return self.elements.get(element_id)
    
    def get_app_info(self):
        """获取应用信息"""
        return self.app_info
    
    def get_element_summary(self):
        """返回元素摘要信息"""
        # 计算可见的交互元素数量
        visible_interactive = sum(1 for e in self.interactive_elements.values() if e['visible'])
        
        return {
            'total_elements': len(self.elements),
            'interactive_elements': len(self.interactive_elements),
            'visible_interactive': visible_interactive,
            'app_package': self.app_info.get('current_app', {}).get('package', 'Unknown'),
            'app_activity': self.app_info.get('current_app', {}).get('activity', 'Unknown')
        }