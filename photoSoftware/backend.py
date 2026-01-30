#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端处理模块
处理联系人匹配、文件操作等功能
"""

import os
import re
import shutil
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class ContactMatcher:
    """联系人匹配处理类"""
    
    def __init__(self):
        self.matched_contacts = []
        self.unmatched_folders = []
        self.unmatched_contacts = []
    
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
    
    def parse_folder_name(self, folder_name: str) -> Tuple[str, str]:
        """
        解析文件夹名称，提取名称和单位
        
        Args:
            folder_name: 文件夹名称，格式为"名称 单位"
            
        Returns:
            (名称, 单位) 元组
        """
        # 尝试按空格分割
        parts = folder_name.strip().split()
        
        if len(parts) == 0:
            return ('', '')
        elif len(parts) == 1:
            return (parts[0], '')
        else:
            # 假设最后一个部分是单位，其余是名称
            name = ' '.join(parts[:-1])
            org = parts[-1]
            return (name, org)
    
    def is_subsequence_match(self, short_str: str, long_str: str) -> bool:
        """
        检查短字符串是否是长字符串的子序列（按顺序匹配）
        
        Args:
            short_str: 短字符串（联系人的单位，可能不完整或简写）
            long_str: 长字符串（文件夹的单位，完整）
            
        Returns:
            如果短字符串是长字符串的子序列，返回True
        """
        if not short_str or not long_str:
            return False
        
        # 转换为字符列表
        short_chars = list(short_str)
        long_chars = list(long_str)
        
        # 双指针法检查子序列
        short_idx = 0
        long_idx = 0
        
        while short_idx < len(short_chars) and long_idx < len(long_chars):
            if short_chars[short_idx] == long_chars[long_idx]:
                short_idx += 1
            long_idx += 1
        
        # 如果短字符串的所有字符都匹配了，说明是子序列
        return short_idx == len(short_chars)
    
    def match_contacts_to_folders(
        self, 
        contacts: List[Dict], 
        base_folder: str
    ) -> Dict[str, Dict]:
        """
        匹配联系人和文件夹
        
        Args:
            contacts: 联系人列表
            base_folder: 基础文件夹路径
            
        Returns:
            匹配结果字典，key为文件夹路径，value为联系人信息
        """
        matches = {}
        matched_contact_indices = set()  # 使用索引而不是名称，避免重名问题
        
        # 获取所有子文件夹
        base_path = Path(base_folder)
        if not base_path.exists():
            return matches
        
        folders = [f for f in base_path.iterdir() if f.is_dir() and f.name != 'photo']
        
        # 对文件夹排序：有单位的文件夹优先处理，避免无单位的文件夹抢占有单位的联系人
        def folder_sort_key(folder):
            _, folder_org = self.parse_folder_name(folder.name)
            # 有单位的排在前面（返回0），无单位的排在后面（返回1）
            return 0 if folder_org else 1
        
        folders = sorted(folders, key=folder_sort_key)
        
        # 匹配逻辑
        for folder in folders:
            folder_name, folder_org = self.parse_folder_name(folder.name)
            
            if not folder_name:
                continue
            
            # 查找所有名称匹配的联系人
            candidates = [
                (idx, c) for idx, c in enumerate(contacts)
                if c['name'].strip() == folder_name and idx not in matched_contact_indices
            ]
            
            if len(candidates) == 0:
                # 没有名称匹配的联系人，跳过
                continue
            elif len(candidates) == 1:
                # 只有一个名称匹配的联系人，直接匹配
                idx, contact = candidates[0]
                matches[str(folder)] = contact
                matched_contact_indices.add(idx)
                self.matched_contacts.append({
                    'folder': str(folder),
                    'contact': contact
                })
            else:
                # 有多个同名联系人
                best_match = None
                best_org_score = 0
                exact_match_found = False
                
                # 如果文件夹有单位信息，尝试匹配单位
                if folder_org:
                    for idx, contact in candidates:
                        contact_org = contact.get('org', '').strip()
                        
                        # 精确匹配（优先级最高）
                        if contact_org and contact_org == folder_org:
                            best_match = (idx, contact)
                            exact_match_found = True
                            break
                        
                        # 子序列匹配（联系人单位是文件夹单位的子序列）
                        if contact_org and self.is_subsequence_match(contact_org, folder_org):
                            # 记录最佳匹配（按长度，越长越精确）
                            score = len(contact_org)
                            if score > best_org_score:
                                best_org_score = score
                                best_match = (idx, contact)
                
                # 如果没有找到匹配（无单位或单位不匹配）
                if best_match is None:
                    # 优先选择无单位的联系人
                    no_org_candidates = [(idx, c) for idx, c in candidates if not c.get('org', '').strip()]
                    if no_org_candidates:
                        best_match = no_org_candidates[0]
                    else:
                        # 如果都有单位，使用第一个出现的联系人
                        best_match = candidates[0]
                
                # 添加匹配结果
                idx, contact = best_match
                matches[str(folder)] = contact
                matched_contact_indices.add(idx)
                self.matched_contacts.append({
                    'folder': str(folder),
                    'contact': contact
                })
        
        # 记录未匹配的文件夹
        for folder in folders:
            if str(folder) not in matches:
                self.unmatched_folders.append(str(folder))
        
        # 记录未匹配的联系人
        for idx, contact in enumerate(contacts):
            if idx not in matched_contact_indices:
                self.unmatched_contacts.append(contact)
        
        return matches
    
    def save_contact_info(self, output_folder: str, contact: Dict):
        """
        将联系人信息保存到输出文件夹
        
        Args:
            output_folder: 输出文件夹路径（联系人名称的文件夹）
            contact: 联系人信息
        """
        folder = Path(output_folder)
        folder.mkdir(parents=True, exist_ok=True)
        
        # 文件名为联系人名称.txt
        contact_name = contact['name']
        info_file = folder / f'{contact_name}.txt'
        
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"姓名：{contact['name']}\n")
            
            if contact.get('org'):
                f.write(f"单位：{contact['org']}\n")
            
            if contact.get('title'):
                f.write(f"职位：{contact['title']}\n")
            
            if contact.get('phones'):
                for i, phone in enumerate(contact['phones'], 1):
                    if len(contact['phones']) == 1:
                        f.write(f"电话：{phone}\n")
                    else:
                        f.write(f"电话{i}：{phone}\n")
            
            if contact.get('emails'):
                for i, email in enumerate(contact['emails'], 1):
                    if len(contact['emails']) == 1:
                        f.write(f"邮箱：{email}\n")
                    else:
                        f.write(f"邮箱{i}：{email}\n")
            
            if contact.get('addresses'):
                for i, addr in enumerate(contact['addresses'], 1):
                    if len(contact['addresses']) == 1:
                        f.write(f"地址：{addr}\n")
                    else:
                        f.write(f"地址{i}：{addr}\n")
            
            if contact.get('note'):
                f.write(f"备注：{contact['note']}\n")
    
    def copy_images_to_output(self, source_folder: str, output_folder: str):
        """
        将源文件夹中的图片复制到输出文件夹的photo子目录
        
        Args:
            source_folder: 源文件夹路径
            output_folder: 输出文件夹路径（联系人名称的文件夹）
        """
        source_path = Path(source_folder)
        photo_folder = Path(output_folder) / 'photo'
        
        # 支持的图片格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        
        # 查找源文件夹中的图片
        images = [
            f for f in source_path.iterdir() 
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        # 只有存在图片时才创建photo文件夹
        if images:
            photo_folder.mkdir(parents=True, exist_ok=True)
            
            # 复制图片，保持原始文件名
            for img in images:
                dest = photo_folder / img.name
                
                # 如果目标文件已存在，添加序号
                counter = 1
                while dest.exists():
                    name_part = img.stem
                    ext = img.suffix
                    new_name = f"{name_part}_{counter}{ext}"
                    dest = photo_folder / new_name
                    counter += 1
                
                shutil.copy2(img, dest)
    
    def process(
        self, 
        folder_path: str, 
        vcf_path: str,
        output_path: str
    ) -> Dict:
        """
        主处理函数
        
        Args:
            folder_path: 包含子文件夹的基础文件夹路径
            vcf_path: VCF联系人文件路径
            output_path: 输出目录路径
            
        Returns:
            处理结果字典
        """
        # 重置状态
        self.matched_contacts = []
        self.unmatched_folders = []
        self.unmatched_contacts = []
        
        # 解析VCF文件
        contacts = self.parse_vcf_file(vcf_path)
        
        # 匹配联系人和文件夹
        matches = self.match_contacts_to_folders(contacts, folder_path)
        
        # 创建输出目录
        output_base = Path(output_path)
        output_base.mkdir(parents=True, exist_ok=True)
        
        # 为每个匹配的联系人创建文件夹并保存信息
        for folder_path_str, contact in matches.items():
            # 使用源文件夹名称作为输出文件夹名称（避免同名联系人冲突）
            source_folder_name = Path(folder_path_str).name
            contact_output_folder = output_base / source_folder_name
            
            # 保存联系人信息
            self.save_contact_info(str(contact_output_folder), contact)
            
            # 复制图片到photo子目录
            self.copy_images_to_output(folder_path_str, str(contact_output_folder))
        
        # 返回结果
        return {
            'matched_count': len(self.matched_contacts),
            'matched_contacts': self.matched_contacts,
            'unmatched_folders': self.unmatched_folders,
            'unmatched_contacts': self.unmatched_contacts,
            'total_contacts': len(contacts),
            'total_folders': len([f for f in Path(folder_path).iterdir() if f.is_dir() and f.name != 'photo']),
            'output_path': str(output_base)
        }
