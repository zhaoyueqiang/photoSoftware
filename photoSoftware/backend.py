#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端处理模块
处理联系人匹配、照片标签读取、HTML相册生成等功能
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from PIL import Image


class ContactMatcher:
    """联系人匹配处理类"""
    
    def __init__(self):
        self.matched_contacts = []
        self.unmatched_photos = []
        self.unmatched_contacts = []
        self.photo_contact_map = {}  # 照片路径 -> 联系人信息
        self.photo_tags_info = {}  # 照片路径 -> 提取到的标签列表（用于调试）
    
    def parse_vcf_file(self, vcf_path: str) -> List[Dict]:
        """
        解析VCF文件，提取联系人信息
        
        Args:
            vcf_path: VCF文件路径
            
        Returns:
            联系人列表，每个联系人包含name、org、phones、addresses等字段
        """
        contacts = []
        
        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(vcf_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, FileNotFoundError):
                continue
        
        if content is None:
            raise ValueError(f"无法读取VCF文件: {vcf_path}")
        
        # 处理VCF的续行（以空格开头的行是上一行的继续）
        lines = []
        current_line = ''
        for line in content.split('\n'):
            if line.startswith(' ') or line.startswith('\t'):
                # 续行
                current_line += line[1:] if line.startswith(' ') else line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = line
        if current_line:
            lines.append(current_line)
        
        content = '\n'.join(lines)
        
        # 分割VCF条目
        vcard_blocks = re.split(r'BEGIN:VCARD', content, flags=re.IGNORECASE)
        
        for block in vcard_blocks:
            if not block.strip() or 'END:VCARD' not in block.upper():
                continue
            
            contact = {
                'name': '',
                'org': '',
                'phones': [],
                'emails': [],
                'addresses': [],
                'title': '',
                'note': ''
            }
            
            # 提取FN（Full Name）
            fn_patterns = [
                r'FN[;:]?(.*?)(?:\r?\n|$)',
                r'FN;.*?:(.*?)(?:\r?\n|$)',
            ]
            for pattern in fn_patterns:
                fn_match = re.search(pattern, block, re.IGNORECASE | re.MULTILINE)
                if fn_match:
                    name = fn_match.group(1).strip()
                    # 移除可能的编码标记
                    name = re.sub(r'^=\?.*?\?=.*?\?', '', name)
                    if name:
                        contact['name'] = name
                        break
            
            # 提取N（Name）
            if not contact['name']:
                n_patterns = [
                    r'N[;:]?(.*?)(?:\r?\n|$)',
                    r'N;.*?:(.*?)(?:\r?\n|$)',
                ]
                for pattern in n_patterns:
                    n_match = re.search(pattern, block, re.IGNORECASE | re.MULTILINE)
                    if n_match:
                        name_parts = n_match.group(1).strip().split(';')
                        # N格式通常是：Family;Given;Additional;Prefix;Suffix
                        name = ' '.join([p.strip() for p in name_parts[:2] if p.strip()])
                        if name:
                            contact['name'] = name
                            break
            
            # 提取ORG（Organization）
            org_patterns = [
                r'ORG[;:]?(.*?)(?:\r?\n|$)',
                r'ORG;.*?:(.*?)(?:\r?\n|$)',
            ]
            for pattern in org_patterns:
                org_match = re.search(pattern, block, re.IGNORECASE | re.MULTILINE)
                if org_match:
                    org = org_match.group(1).strip()
                    # 移除可能的编码标记
                    org = re.sub(r'^=\?.*?\?=.*?\?', '', org)
                    if org:
                        contact['org'] = org
                        break
            
            # 提取电话号码（TEL）
            tel_patterns = [
                r'TEL[;:][^:]*:(.*?)(?:\r?\n|$)',
                r'TEL:(.*?)(?:\r?\n|$)',
            ]
            for pattern in tel_patterns:
                tel_matches = re.findall(pattern, block, re.IGNORECASE | re.MULTILINE)
                for tel in tel_matches:
                    phone = tel.strip()
                    if phone and phone not in contact['phones']:
                        contact['phones'].append(phone)
            
            # 提取邮箱（EMAIL）- 逐行匹配避免跨行问题
            for line in block.split('\n'):
                line = line.strip()
                if line.upper().startswith('EMAIL'):
                    # 找到冒号后的内容
                    colon_pos = line.find(':')
                    if colon_pos != -1:
                        email_addr = line[colon_pos + 1:].strip()
                        if email_addr and email_addr not in contact['emails']:
                            contact['emails'].append(email_addr)
            
            # 提取地址（ADR）
            adr_patterns = [
                r'ADR[;:][^:]*:(.*?)(?:\r?\n|$)',
                r'ADR:(.*?)(?:\r?\n|$)',
            ]
            for pattern in adr_patterns:
                adr_matches = re.findall(pattern, block, re.IGNORECASE | re.MULTILINE)
                for adr in adr_matches:
                    # 地址格式：PO Box;Extended;Street;City;State;Postal;Country
                    parts = adr.strip().split(';')
                    # 过滤空值并组合地址
                    addr_parts = [p.strip() for p in parts if p.strip()]
                    if addr_parts:
                        address = ' '.join(addr_parts)
                        if address not in contact['addresses']:
                            contact['addresses'].append(address)
            
            # 提取职位（TITLE）
            title_match = re.search(r'TITLE[;:]?(.*?)(?:\r?\n|$)', block, re.IGNORECASE | re.MULTILINE)
            if title_match:
                contact['title'] = title_match.group(1).strip()
            
            # 提取备注（NOTE）
            note_match = re.search(r'NOTE[;:]?(.*?)(?:\r?\n|$)', block, re.IGNORECASE | re.MULTILINE)
            if note_match:
                contact['note'] = note_match.group(1).strip()
            
            # 只添加有名称的联系人
            if contact['name']:
                contacts.append(contact)
        
        return contacts
    
    def extract_photo_tags(self, photo_path: Path) -> List[str]:
        """
        从照片中提取人名标签（支持多个人名）
        从XMP元数据中提取人脸识别标记的人员信息
        
        Args:
            photo_path: 照片文件路径
            
        Returns:
            提取到的人名列表（可能包含多个人名）
        """
        tags = []
        
        try:
            with Image.open(photo_path) as img:
                # 从XMP XML中提取人名（包含人员标记信息）
                if hasattr(img, 'info') and 'xmp' in img.info:
                    xmp_bytes = img.info['xmp']
                    xmp_names = self._extract_names_from_xmp(xmp_bytes)
                    tags.extend(xmp_names)
                    
        except Exception as e:
            # 调试：记录错误但不中断
            pass
        
        # 去重并过滤空值
        tags = [t.strip() for t in tags if t.strip()]
        return list(set(tags))  # 去重
    
    def _extract_names_from_xmp(self, xmp_bytes: bytes) -> List[str]:
        """
        从XMP XML数据中提取人名
        
        Args:
            xmp_bytes: XMP数据的字节
            
        Returns:
            提取到的人名列表
        """
        names = []
        
        try:
            # 尝试多种编码解码XMP XML
            xmp_xml = None
            for encoding in ['utf-8', 'utf-16-le', 'utf-16-be', 'gbk', 'gb2312']:
                try:
                    decoded = xmp_bytes.decode(encoding, errors='ignore')
                    if decoded.strip() and ('<?xpacket' in decoded or '<x:xmpmeta' in decoded):
                        xmp_xml = decoded
                        # 移除BOM
                        if xmp_xml.startswith('\ufeff'):
                            xmp_xml = xmp_xml[1:]
                        break
                except Exception:
                    continue
            
            if not xmp_xml:
                return names
            
            # 解析XML
            try:
                # 移除xpacket包装，只保留xmpmeta部分
                xml_clean = xmp_xml
                if '<?xpacket' in xml_clean:
                    start = xml_clean.find('<x:xmpmeta')
                    end = xml_clean.rfind('</x:xmpmeta>')
                    if start != -1 and end != -1:
                        xml_clean = xml_clean[start:end+11]
                
                root = ET.fromstring(xml_clean)
                
                # 定义命名空间
                namespaces = {
                    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                    'dc': 'http://purl.org/dc/elements/1.1/',
                    'MPReg': 'http://ns.microsoft.com/photo/1.2/t/Region#',
                    'mwg-rs': 'http://www.metadataworkinggroup.com/schemas/regions/',
                }
                
                # 1. 从dc:subject提取（主题/标签，通常包含人名）
                for subject in root.findall('.//{http://purl.org/dc/elements/1.1/}subject/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li', namespaces):
                    if subject.text and subject.text.strip():
                        name = subject.text.strip()
                        # 过滤掉"People"等分类标签
                        if name and name != 'People' and '/' not in name and '|' not in name:
                            if name not in names:
                                names.append(name)
                
                # 2. 从MP:RegionInfo/MPReg:PersonDisplayName提取（Microsoft Photo人员显示名称）
                # PersonDisplayName是rdf:li元素的属性
                for rdf_li in root.findall('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li', namespaces):
                    person_name = rdf_li.get('{http://ns.microsoft.com/photo/1.2/t/Region#}PersonDisplayName')
                    if person_name and person_name.strip():
                        name = person_name.strip()
                        if name not in names:
                            names.append(name)
                
                # 3. 从mwg-rs:Regions/mwg-rs:Name提取（区域名称，通常是人名）
                # Name是Description元素的属性
                for desc in root.findall('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description', namespaces):
                    region_name = desc.get('{http://www.metadataworkinggroup.com/schemas/regions/}Name')
                    if region_name and region_name.strip():
                        name = region_name.strip()
                        if name not in names:
                            names.append(name)
                
                # 4. 从digiKam:TagsList提取（格式：People/人名）
                for tag_item in root.findall('.//{http://www.digikam.org/ns/1.0/}TagsList/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Seq/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li', namespaces):
                    if tag_item.text and tag_item.text.strip():
                        tag_text = tag_item.text.strip()
                        # 提取People/后面的人名
                        if tag_text.startswith('People/'):
                            name = tag_text[7:].strip()
                            if name and name not in names:
                                names.append(name)
                
                # 5. 从acdsee:categories属性提取（HTML编码的XML）
                for desc in root.findall('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description', namespaces):
                    categories_attr = desc.get('{http://ns.acdsee.com/iptc/1.0/}categories')
                    if categories_attr:
                        # 解码HTML实体
                        import html
                        categories_decoded = html.unescape(categories_attr)
                        # 提取Category标签中的人名
                        category_matches = re.findall(r'<Category[^>]*>([^<]+)</Category>', categories_decoded)
                        for match in category_matches:
                            name = match.strip()
                            # 过滤掉"People"分类
                            if name and name != 'People' and name not in names:
                                names.append(name)
                
            except ET.ParseError:
                # XML解析失败，尝试正则表达式提取
                # 从dc:subject中提取
                dc_subject_matches = re.findall(r'<dc:subject[^>]*>.*?<rdf:li>([^<]+)</rdf:li>', xmp_xml, re.DOTALL)
                for match in dc_subject_matches:
                    name = match.strip()
                    if name and name not in names:
                        names.append(name)
                
                # 从PersonDisplayName中提取
                person_matches = re.findall(r'MPReg:PersonDisplayName="([^"]+)"', xmp_xml)
                for match in person_matches:
                    name = match.strip()
                    if name and name not in names:
                        names.append(name)
                
                # 从mwg-rs:Name中提取
                name_matches = re.findall(r'mwg-rs:Name="([^"]+)"', xmp_xml)
                for match in name_matches:
                    name = match.strip()
                    if name and name not in names:
                        names.append(name)
                
            except Exception:
                pass
                
        except Exception:
            pass
        
        return names
    
    def is_name_match(self, photo_name: str, contact_name: str) -> bool:
        """
        检查照片标签中的人名是否与联系人姓名匹配
        
        Args:
            photo_name: 照片中提取的人名
            contact_name: 联系人姓名
            
        Returns:
            是否匹配
        """
        # 完全匹配
        if photo_name.strip() == contact_name.strip():
            return True
        
        # 部分匹配（照片标签包含联系人姓名，或联系人姓名包含照片标签）
        photo_clean = photo_name.strip()
        contact_clean = contact_name.strip()
        
        if photo_clean in contact_clean or contact_clean in photo_clean:
            return True
        
        return False
    
    def match_photos_to_contacts(
        self, 
        photos_folder: str, 
        contacts: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        匹配照片和联系人（一张照片可以匹配多个联系人）
        
        Args:
            photos_folder: 照片文件夹路径
            contacts: 联系人列表
            
        Returns:
            匹配结果字典，key为照片路径，value为匹配的联系人信息列表
        """
        matches = {}  # 改为存储列表，一张照片可以匹配多个联系人
        matched_contact_indices = set()  # 用于统计，但不限制一张照片匹配多个
        
        photos_path = Path(photos_folder)
        if not photos_path.exists():
            return matches
        
        # 支持的图片格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        
        # 获取所有照片（递归遍历所有子文件夹）
        photos = [f for f in photos_path.rglob('*') 
                  if f.is_file() and f.suffix.lower() in image_extensions]
        
        # 为每个照片提取标签并匹配
        for photo in photos:
            photo_tags = self.extract_photo_tags(photo)
            photo_path_str = str(photo)
            
            # 记录每张照片提取到的标签（用于调试）
            self.photo_tags_info[photo_path_str] = {
                'tags': photo_tags,
                'filename': photo.name,
                'exif_fields': {}  # 不再使用EXIF信息
            }
            
            if not photo_tags:
                self.unmatched_photos.append(photo_path_str)
                continue
            
            # 为这张照片匹配的所有联系人
            photo_matches: List[Dict] = []
            
            # 尝试匹配每个标签
            for tag in photo_tags:
                # 查找所有名称匹配的联系人（不限制已匹配）
                candidates = [
                    (idx, c) for idx, c in enumerate(contacts)
                        if self.is_name_match(tag, c['name'])
                ]
                
                if len(candidates) == 0:
                    continue
                elif len(candidates) == 1:
                        # 只有一个匹配，直接添加
                    idx, contact = candidates[0]
                    if contact not in photo_matches:  # 避免重复
                        photo_matches.append(contact)
                        matched_contact_indices.add(idx)
                        self.matched_contacts.append({
                            'photo': photo_path_str,
                            'contact': contact,
                            'tag': tag
                        })
                else:
                    # 多个同名联系人，优先选择有单位的
                    # 如果都有单位或都没有，选择第一个
                    best_contact = None
                    best_score = -1
                    
                    for idx, contact in candidates:
                        score = 0
                        if contact.get('org'):
                            score = 1
                        # 如果照片标签中包含单位信息，可以进一步匹配
                        # 这里简化处理
                        if score > best_score:
                            best_score = score
                            best_contact = contact
                    
                    if best_contact and best_contact not in photo_matches:
                        photo_matches.append(best_contact)
                        matched_contact_indices.add(candidates[0][0])  # 记录第一个匹配的索引
                    self.matched_contacts.append({
                            'photo': photo_path_str,
                            'contact': best_contact,
                            'tag': tag
                    })
        
            # 如果匹配到联系人，添加到结果中
            if photo_matches:
                matches[photo_path_str] = photo_matches
            else:
                self.unmatched_photos.append(photo_path_str)
        
        # 记录未匹配的联系人
        for idx, contact in enumerate(contacts):
            if idx not in matched_contact_indices:
                self.unmatched_contacts.append(contact)
        
        return matches
    
    def generate_html_album(
        self, 
        matches: Dict[str, List[Dict]],
        output_path: str,
        photos_folder: str
    ) -> str:
        """
        生成静态HTML相册（一张照片可以出现在多个联系人卡片中）
        
        Args:
            matches: 照片路径 -> 联系人信息列表的映射（一张照片可以匹配多个联系人）
            output_path: 输出HTML文件路径
            photos_folder: 照片文件夹路径（用于生成相对路径）
            
        Returns:
            HTML文件路径
        """
        photos_base = Path(photos_folder)
        output_file = Path(output_path)
        
        # 按联系人分组照片（一张照片可以出现在多个联系人卡片中）
        contact_photos = {}
        for photo_path, contacts in matches.items():
            # 计算相对路径，并转换为正斜杠（HTML需要）
            photo_rel_path = os.path.relpath(photo_path, output_file.parent)
            photo_rel_path = photo_rel_path.replace('\\', '/')  # Windows路径转正斜杠
            
            # 为每个匹配的联系人添加这张照片
            for contact in contacts:
                contact_key = f"{contact['name']}_{contact.get('org', '')}"
                if contact_key not in contact_photos:
                    contact_photos[contact_key] = {
                        'contact': contact,
                        'photos': []
                    }
                # 避免重复添加同一张照片到同一个联系人
                if photo_rel_path not in contact_photos[contact_key]['photos']:
                    contact_photos[contact_key]['photos'].append(photo_rel_path)
        
        # 生成HTML
        html_content = self._generate_html_content(contact_photos)
        
        # 保存HTML文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_file)
    
    def _generate_html_content(self, contact_photos: Dict) -> str:
        """生成HTML内容"""
        
        # 生成联系人数据（用于搜索）
        contacts_data = []
        for key, data in contact_photos.items():
            contact = data['contact']
            contacts_data.append({
                'name': contact['name'],
                'org': contact.get('org', ''),
                'title': contact.get('title', ''),
                'phones': contact.get('phones', []),
                'emails': contact.get('emails', []),
                'addresses': contact.get('addresses', []),
                'photos': data['photos']
            })
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>联系人照片相册</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e5e7eb;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #1f2937;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .search-box {{
            margin: 20px 30px;
            position: relative;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 15px 50px 15px 20px;
            font-size: 16px;
            background: #374151;
            color: #e5e7eb;
            border: 2px solid #4b5563;
            border-radius: 50px;
            outline: none;
            transition: all 0.3s;
        }}
        
        .search-box input::placeholder {{
            color: #9ca3af;
        }}
        
        .search-box input:focus {{
            border-color: #6366f1;
            background: #4b5563;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }}
        
        .search-box::after {{
            content: '🔍';
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 20px;
        }}
        
        .contacts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 30px;
            padding: 30px;
        }}
        
        .contact-card {{
            background: #2d3748;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            border: 1px solid #4a5568;
            transition: transform 0.3s, box-shadow 0.3s;
            cursor: pointer;
        }}
        
        .contact-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border-color: #6366f1;
        }}
        
        .contact-card.hidden {{
            display: none;
        }}
        
        .photo-gallery {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            padding: 15px;
            background: #1a202c;
        }}
        
        .photo-item {{
            position: relative;
            padding-top: 100%;
            overflow: hidden;
            border-radius: 8px;
            background: #2d3748;
        }}
        
        .photo-item.hidden {{
            display: none;
        }}
        
        .photo-item.expanded {{
            display: block;
        }}
        
        .show-more-btn {{
            grid-column: 1 / -1;
            padding: 12px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s;
            margin-top: 5px;
        }}
        
        .show-more-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(99, 102, 241, 0.5);
            background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        }}
        
        .show-more-btn:active {{
            transform: translateY(0);
        }}
        
        .photo-count-badge {{
            position: absolute;
            top: 5px;
            right: 5px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            z-index: 10;
        }}
        
        .photo-item img {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            cursor: pointer;
            transition: transform 0.3s;
        }}
        
        .photo-item img:hover {{
            transform: scale(1.1);
        }}
        
        .contact-info {{
            padding: 20px;
        }}
        
        .contact-name {{
            font-size: 1.5em;
            font-weight: bold;
            color: #f3f4f6;
            margin-bottom: 10px;
        }}
        
        .contact-org {{
            color: #818cf8;
            font-size: 1.1em;
            margin-bottom: 15px;
        }}
        
        .contact-details {{
            color: #d1d5db;
            font-size: 0.9em;
            line-height: 1.8;
        }}
        
        .contact-details p {{
            margin: 5px 0;
        }}
        
        .contact-details strong {{
            color: #e5e7eb;
        }}
        
        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: #9ca3af;
            font-size: 1.2em;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            cursor: pointer;
        }}
        
        .modal-content {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            max-width: 90%;
            max-height: 90%;
        }}
        
        .modal-content img {{
            width: 100%;
            height: auto;
            border-radius: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>联系人照片相册</h1>
            <p>共 {len(contact_photos)} 位联系人，{sum(len(d['photos']) for d in contact_photos.values())} 张照片</p>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="搜索联系人姓名、单位、电话...">
        </div>
        
        <div class="contacts-grid" id="contactsGrid">
"""
        
        # 生成联系人卡片
        for key, data in contact_photos.items():
            contact = data['contact']
            photos = data['photos']
            total_photos = len(photos)
            max_initial = 6  # 默认显示前6张
            
            # 生成照片HTML
            photos_html = ''
            for idx, photo in enumerate(photos):
                # 前6张正常显示，超过6张的添加hidden类
                hidden_class = ' hidden' if idx >= max_initial else ''
                photos_html += f'''
                <div class="photo-item{hidden_class}" data-photo-index="{idx}">
                    <img src="{photo}" alt="{contact['name']}" onclick="openModal('{photo}')">
                    {f'<div class="photo-count-badge">+{total_photos - max_initial}</div>' if idx == max_initial - 1 and total_photos > max_initial else ''}
                </div>
'''
            
            # 如果照片超过6张，添加"查看更多"按钮
            if total_photos > max_initial:
                photos_html += f'''
                <button class="show-more-btn" onclick="togglePhotos(this, {total_photos})">
                    <span class="show-more-text">查看更多 ({total_photos - max_initial} 张)</span>
                    <span class="show-less-text" style="display: none;">收起</span>
                </button>
'''
            
            # 生成联系人信息HTML
            info_html = f'''
            <div class="contact-name">{contact['name']}</div>
'''
            
            if contact.get('org'):
                info_html += f'<div class="contact-org">🏢 {contact["org"]}</div>'
            
            if contact.get('title'):
                info_html += f'<p><strong>职位：</strong>{contact["title"]}</p>'
            
            if contact.get('phones'):
                phones_str = '、'.join(contact['phones'])
                info_html += f'<p><strong>电话：</strong>{phones_str}</p>'
            
            if contact.get('emails'):
                emails_str = '、'.join(contact['emails'])
                info_html += f'<p><strong>邮箱：</strong>{emails_str}</p>'
            
            if contact.get('addresses'):
                addresses_str = '、'.join(contact['addresses'])
                info_html += f'<p><strong>地址：</strong>{addresses_str}</p>'
            
            if contact.get('note'):
                info_html += f'<p><strong>备注：</strong>{contact["note"]}</p>'
            
            html += f'''
            <div class="contact-card" data-name="{contact['name']}" data-org="{contact.get('org', '')}" data-phones="{' '.join(contact.get('phones', []))}" data-emails="{' '.join(contact.get('emails', []))}">
                <div class="photo-gallery">
{photos_html}
                </div>
                <div class="contact-info">
{info_html}
                </div>
            </div>
'''
        
        html += '''
        </div>
        
        <div class="no-results" id="noResults" style="display: none;">
            没有找到匹配的联系人
        </div>
    </div>
    
    <div class="modal" id="imageModal" onclick="closeModal()">
        <div class="modal-content">
            <img id="modalImage" src="" alt="">
        </div>
    </div>
    
    <script>
        const contactsData = ''' + json.dumps(contacts_data, ensure_ascii=False, indent=2) + ''';
        
        const searchInput = document.getElementById('searchInput');
        const contactsGrid = document.getElementById('contactsGrid');
        const noResults = document.getElementById('noResults');
        
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase().trim();
            const cards = document.querySelectorAll('.contact-card');
            let visibleCount = 0;
            
            cards.forEach(card => {
                const name = card.dataset.name.toLowerCase();
                const org = (card.dataset.org || '').toLowerCase();
                const phones = (card.dataset.phones || '').toLowerCase();
                const emails = (card.dataset.emails || '').toLowerCase();
                
                if (query === '' || 
                    name.includes(query) || 
                    org.includes(query) || 
                    phones.includes(query) || 
                    emails.includes(query)) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            });
            
            if (visibleCount === 0 && query !== '') {
                noResults.style.display = 'block';
            } else {
                noResults.style.display = 'none';
            }
        });
        
        function openModal(imageSrc) {
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            modalImg.src = imageSrc;
            modal.style.display = 'block';
        }
        
        function closeModal() {
            const modal = document.getElementById('imageModal');
            modal.style.display = 'none';
        }
        
        // 点击模态框外部关闭
        document.getElementById('imageModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
        
        // 切换显示更多照片
        function togglePhotos(button, totalPhotos) {{
            const gallery = button.closest('.photo-gallery');
            const hiddenPhotos = gallery.querySelectorAll('.photo-item.hidden');
            const showMoreText = button.querySelector('.show-more-text');
            const showLessText = button.querySelector('.show-less-text');
            
            if (hiddenPhotos.length > 0) {{
                // 展开：显示所有隐藏的照片
                hiddenPhotos.forEach(function(photo) {{
                    photo.classList.remove('hidden');
                    photo.classList.add('expanded');
                }});
                showMoreText.style.display = 'none';
                showLessText.style.display = 'inline';
                button.textContent = '收起';
            }} else {{
                // 收起：隐藏超过6张的照片
                const allPhotos = gallery.querySelectorAll('.photo-item');
                allPhotos.forEach(function(photo, index) {{
                    if (index >= 6) {{
                        photo.classList.add('hidden');
                        photo.classList.remove('expanded');
                    }}
                }});
                showMoreText.style.display = 'inline';
                showLessText.style.display = 'none';
                button.innerHTML = '<span class="show-more-text">查看更多 (' + (totalPhotos - 6) + ' 张)</span><span class="show-less-text" style="display: none;">收起</span>';
            }}
        }}
    </script>
</body>
</html>
'''
        
        return html
    
    def process(
        self, 
        photos_folder: str, 
        vcf_path: str,
        output_path: str
    ) -> Dict:
        """
        主处理函数
        
        Args:
            photos_folder: 包含照片的文件夹路径
            vcf_path: VCF联系人文件路径
            output_path: 输出HTML文件路径
            
        Returns:
            处理结果字典
        """
        # 重置状态
        self.matched_contacts = []
        self.unmatched_photos = []
        self.unmatched_contacts = []
        self.photo_contact_map = {}
        self.photo_tags_info = {}
        
        # 解析VCF文件
        contacts = self.parse_vcf_file(vcf_path)
        
        # 匹配照片和联系人
        matches = self.match_photos_to_contacts(photos_folder, contacts)
        
        # 生成HTML相册
        html_path = self.generate_html_album(matches, output_path, photos_folder)
        
        # 统计总照片数
        photos_path = Path(photos_folder)
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        total_photos = len([f for f in photos_path.rglob('*') 
                           if f.is_file() and f.suffix.lower() in image_extensions])
        
        # 统计匹配的照片数（一张照片匹配多个联系人只算一张）
        matched_photo_count = len(matches)
        # 统计匹配的联系人数（去重）
        matched_contact_count = len(set(
            contact['name'] for match_list in matches.values() 
            for contact in match_list
        ))
        
        # 返回结果
        return {
            'matched_count': matched_photo_count,  # 匹配的照片数
            'matched_contact_count': matched_contact_count,  # 匹配的联系人数
            'matched_contacts': self.matched_contacts,
            'unmatched_photos': self.unmatched_photos,
            'unmatched_contacts': self.unmatched_contacts,
            'total_contacts': len(contacts),
            'total_photos': total_photos,
            'html_path': html_path,
            'photo_tags_info': self.photo_tags_info  # 每张照片提取到的标签（用于调试）
        }
