import os
import requests
import openpyxl
import json
import re
import time

# ================= 配置区域 =================
# Supabase 配置
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hubbzosfrhxnzwuiitcv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Fj0j0VPlvGuLLxhjcGMIWA_8KL4DAWV")

# 目标文件夹路径
TARGET_DIR = r"C:\Users\Administrator\Downloads\浙江2026省考\浙江2026年度考试录用公务员各地职位表_合并版.xlsx"  

# 筛选关键词 - 四川省考导入全部数据，不进行筛选
FILTER_KEYWORDS = ["残疾人"]

# 检查关键词的 Excel 列
CHECK_COLUMNS = ["其他条件", "备注", "职位简介", "职位描述", "其他要求", "其他报考条件","其他","招考对象","其它"]

# Excel 表头所在的行号（从 1 开始计数，例如第 4 行）
HEADER_ROW = 3
HEADER_HEIGHT = 1 # 表头占据的行数

# Excel 列名到数据库字段的映射
COLUMN_MAPPING = {
    "exam_region": ["考区", "所属地区", "地区名称", "招录机关所在市（州）"],
    "recruit_unit": ["招考单位", "单位名称", "招录单位", "招录机关", "上报单位", "部门名称","招录机关（单位)"],
    "unit_level": ["单位层级", "机构层级", "职位层级", "部门属性", "部门性质", "隶属关系"],
    "position_name": ["招考职位", "职位名称"],
    "position_code": ["职位代码", "职位编码", "代码"],
    "position_nature": ["职位性质", "职位工作性质及需要说明的其他事项"],
    "exam_subjects": ["笔试考试科目", "所属大类", "所属小类", "须注明的考试科目 申论类别", "专业科目", "公共科目类型", "科目类别", "笔试科目"],
    "quota": ["录用人数", "招录人数", "招录指标", "招考人数", "招考名额", "录用名额"],
    "candidate_identity": ["招录对象", "招考对象", "报考人员身份要求", "定向招录项目要求 服务基层项目人员", "优秀村(社区)干部", "驻村第一书记和工作队员", "少数民族", "2026届毕业生", "具有本科以上学历的安排工作的退役军士和义务兵", "民族", "招收对象"],
    "grassroots_exp": ["工作经历要求", "基层工作年限要求", "基层工作经历要求", "2年及以上基层工作经历要求", "基层工作经历最低年限", "基层工作经历时间", "经历要求"],
    "gender": ["性别", "性别要求"],
    "max_age": ["最高年龄要求", "年龄", "年龄要求"],
    "education": ["学历学位", "学历", "最低学历要求", "学历要求"],
    "degree": ["学历学位", "学位", "学位要求"],
    "major": ["研究生专业名称及代码", "本科专业名称及代码", "大专专业名称及代码", "专科专业名称及代码", "专业要求", "专业", "职位资格条件和要求 专业"],
    "domicile": ["户籍要求", "户别要求", "户籍"],
    "certification": ["资格证书", "职业资格证书等要求"],
    "other_requirements": ["其他资格条件", "其他要求", "其他招录条件及说明", "其它条件", "其他报考条件", "其他", "备注（职位简介）", "备注", "其他条件", "其它"],
    "min_service_years": ["最低服务年限要求"],
    "exam_ratio": ["笔试最低开考比例", "笔试开考比例", "开考比例"],
    "physical_test_standards": ["体能测评", "体能测评项目和标准"],
    "medical_test_standards": ["心理素质测评", "体检标准"],
    "phone1": ["招考部门电话", "咨询电话1", "咨询电话", "考生咨询电话", "单位咨询电话", "联系方式"],
    "phone2": ["咨询电话2"],
    
    # 兼容原有字段映射
    "region_dept": ["招考部门", "地区部门", "用人部门", "部门代码"],
    "position_type": ["职位类型", "职位类别", "机构性质"],
    "rank_level": ["职级层次", "职位层级"],
    "political_status": ["政治面貌", "政治面貌要求"],
    "fresh_grad": ["是否限应届毕业生报考", "面向应届毕业生招考"],
    "fresh_grad_year": ["面向2026年应届毕业生招考"],
    "exam_type": ["笔试考试类型", "考试类别"],
    "essay_subject": ["申论科目", "申论考试类型"],
    "police_subject": ["公安类专业科目"],
    "legal_knowledge": ["法律基础知识"],
    "physical_test": ["体能测评比例"],
    "is_set": ["专业能力测试是否测试", "是否组织专业能力测试"],
    "test_ratio": ["专业能力测试比例"],
    "interview_ratio": ["面试比例", "面试人数与计划录用人数的比例"],
    "inspection_ratio": ["考察比例"],
    "description": ["职位简介", "职位描述", "备注（职位简介）"],
}

# 默认值
DEFAULT_VALUES = {
    "year": 2026,
    "province_code": "330000" # 四川省代码
}

# ===========================================

def extract_region_from_filename(filename):
    """从文件名中提取地区名称"""
    # 匹配 "广安市", "凉山州", "四川省" 等
    match = re.search(r'([\u4e00-\u9fa5]{2,})(市|州|省)', filename)
    if match:
        return match.group(1) + match.group(2)
    
    # 特殊处理 "省级机关"
    if "省级机关" in filename:
        return "四川省直"
        
    return "四川省"

def get_column_index(headers, possible_names):
    """在表头中查找匹配的列索引"""
    for idx, header in enumerate(headers):
        if header and str(header).strip() in possible_names:
            return idx
    return -1

def process_excel(file_path):
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return []

    filename = os.path.basename(file_path)
    default_region = extract_region_from_filename(filename)
    print(f"正在读取 {filename} (默认地区: {default_region})...")
    print(f"当前筛选关键词: {FILTER_KEYWORDS}")
    
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        all_filtered_data = []

        # 遍历所有工作表
        for sheet_name in wb.sheetnames:
            print(f"  正在处理工作表: {sheet_name}")
            sheet = wb[sheet_name]
            
            rows = list(sheet.rows)
            if not rows:
                print(f"  工作表 {sheet_name} 为空，跳过")
                continue

            # -----------------------------------------------------------
            # 动态查找表头行
            # -----------------------------------------------------------
            best_header_row_idx = -1
            max_match_count = 0
            
            # 要检查的关键列名（用于识别表头）
            key_columns = ["招录单位", "职位名称", "专业", "学历", "人数", "指标", "代码", "备注", "单位名称", "职位编码"]
            
            scan_limit = min(20, len(rows))
            for r_idx in range(scan_limit):
                row_values = [str(cell.value).strip() for cell in rows[r_idx] if cell.value]
                row_text = " ".join(row_values)
                
                match_count = 0
                for key in key_columns:
                    if key in row_text:
                        match_count += 1
                
                if match_count > max_match_count:
                    max_match_count = match_count
                    best_header_row_idx = r_idx
            
            current_header_row_start = HEADER_ROW - 1
            if best_header_row_idx != -1 and max_match_count >= 2:
                print(f"  工作表 {sheet_name} 检测到表头在第 {best_header_row_idx + 1} 行 (匹配度: {max_match_count})")
                current_header_row_start = best_header_row_idx
            else:
                print(f"  工作表 {sheet_name} 未自动检测到表头，尝试使用默认行 {HEADER_ROW}")

            if current_header_row_start >= len(rows):
                 print(f"  工作表 {sheet_name} 表头行超出范围，跳过")
                 continue

            # 读取多行表头并合并
            raw_headers = []
            for i in range(HEADER_HEIGHT):
                current_row_idx = current_header_row_start + i
                if current_row_idx < len(rows):
                    row_values = [cell.value for cell in rows[current_row_idx]]
                    raw_headers.append(row_values)
            
            # 合并表头逻辑
            headers = []
            if raw_headers:
                col_count = len(raw_headers[0])
                for col_idx in range(col_count):
                    col_values = []
                    for row_idx in range(len(raw_headers)):
                        if col_idx < len(raw_headers[row_idx]):
                            val = raw_headers[row_idx][col_idx]
                            if val is not None and str(val).strip():
                                val_str = str(val).strip().replace('\n', '').replace('\u3000', '').replace('\xa0', '').replace(' ', '')
                                if val_str not in col_values:
                                    col_values.append(val_str)
                    full_header_name = " ".join(col_values)
                    headers.append(full_header_name)
            
            # 确定要检查关键词的列索引
            check_col_indices = []
            if FILTER_KEYWORDS:
                for col_name in CHECK_COLUMNS:
                    idx = -1
                    for h_idx, header_val in enumerate(headers):
                        if not header_val: continue
                        if col_name in header_val: 
                            idx = h_idx
                            break
                    if idx != -1:
                        check_col_indices.append(idx)
                
                # 如果没找到指定列，但有筛选关键词，则检查所有列
                if not check_col_indices:
                    check_col_indices = range(len(headers))

            # 判断当前 sheet 是否为 "残疾人" 相关
            is_disabled_sheet = "残疾" in sheet_name
            if is_disabled_sheet:
                print(f"  检测到特殊 Sheet '{sheet_name}'，将导入所有行。")

            # 遍历数据行 (从表头结束后的下一行开始)
            current_data_start_idx = current_header_row_start + HEADER_HEIGHT
            
            for row in rows[current_data_start_idx:]:
                # 跳过空行（假设主要列都为空就是空行）
                if not any(cell.value for cell in row):
                    continue
                    
                # 简单验证：如果该行看起来像备注或者页脚，跳过
                first_cell_val = str(row[0].value).strip() if row and row[0].value else ""
                if "注：" in first_cell_val or "说明：" in first_cell_val:
                    continue

                # 筛选逻辑
                is_match = False
                if is_disabled_sheet:
                    is_match = True
                elif not FILTER_KEYWORDS:
                    is_match = True
                else:
                    for idx in check_col_indices:
                        if idx < len(row):
                            cell_value = str(row[idx].value) if row[idx].value is not None else ""
                            for keyword in FILTER_KEYWORDS:
                                if keyword in cell_value:
                                    is_match = True
                                    break
                        if is_match:
                            break
                
                if not is_match:
                    continue

                db_item = {}
                for key in COLUMN_MAPPING.keys():
                    db_item[key] = None

                # 映射字段
                for db_field, possible_names in COLUMN_MAPPING.items():
                    if db_field == "major":
                        major_vals = []
                        for h_idx, header_val in enumerate(headers):
                            if not header_val: continue
                            is_match = False
                            for name in possible_names:
                                if name == header_val or name in header_val.split():
                                    is_match = True
                                    break
                            if is_match and h_idx < len(row):
                                val = row[h_idx].value
                                if val is not None and str(val).strip():
                                    val_str = str(val).strip()
                                    prefix = ""
                                    if "研究生" in header_val: prefix = "研究生:"
                                    elif "本科" in header_val: prefix = "本科:"
                                    elif "大专" in header_val: prefix = "大专:"
                                    
                                    if prefix:
                                        major_vals.append(f"{prefix}{val_str}")
                                    else:
                                        major_vals.append(val_str)
                        
                        if major_vals:
                            db_item[db_field] = "; ".join(major_vals)
                    else:
                        col_idx = -1
                        for h_idx, header_val in enumerate(headers):
                            if not header_val: continue
                            for name in possible_names:
                                if name == header_val or name in header_val.split():
                                    col_idx = h_idx
                                    break
                            if col_idx != -1: break
                        
                        if col_idx != -1 and col_idx < len(row):
                            val = row[col_idx].value
                            if val is not None:
                                db_item[db_field] = str(val).strip()
                
                # 数据清洗和默认值
                if db_item.get("quota"):
                    try:
                        # 处理可能出现的 "1名" 这种格式
                        quota_str = str(db_item["quota"]).replace("名", "").replace("人", "")
                        db_item["quota"] = int(float(quota_str))
                    except:
                        db_item["quota"] = 0
                else:
                    db_item["quota"] = 0

                # 如果没有提取到地区，使用文件名中的默认地区
                if not db_item.get("exam_region"):
                    db_item["exam_region"] = default_region

                for k, v in DEFAULT_VALUES.items():
                    if db_item.get(k) is None:
                        db_item[k] = v
                
                # 只有当职位名称和招录单位都有值时才认为是有效行
                if db_item.get("position_name") and db_item.get("recruit_unit"):
                    all_filtered_data.append(db_item)
                
        print(f"  解析完成，共提取 {len(all_filtered_data)} 条职位信息。")
        return all_filtered_data
        
    except Exception as e:
        print(f"  处理 Excel 失败: {e}")
        # import traceback
        # traceback.print_exc()
        return []

def upload_to_supabase(data):
    if not data:
        return

    print("正在连接 Supabase (via REST API)...")
    try:
        api_url = f"{SUPABASE_URL}/rest/v1/positions"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        batch_size = 100
        total = len(data)
        success_count = 0
        
        for i in range(0, total, batch_size):
            batch = data[i : i + batch_size]
            # print(f"正在上传第 {i+1} - {min(i+batch_size, total)} 条...")
            
            try:
                response = requests.post(api_url, headers=headers, json=batch)
                
                if response.status_code >= 400:
                    print(f"上传失败 (HTTP {response.status_code}): {response.text}")
                else:
                    success_count += len(batch)
            except Exception as e:
                print(f"网络错误: {e}")
                
        print(f"  上传完成！成功: {success_count}/{total}")
        
    except Exception as e:
        print(f"上传流程异常: {e}")

def main():
    if not os.path.exists(TARGET_DIR):
        print(f"目标目录不存在: {TARGET_DIR}")
        return

    files = [f for f in os.listdir(TARGET_DIR) if f.endswith('.xlsx') and not f.startswith('~$')]
    print(f"在 {TARGET_DIR} 目录下找到 {len(files)} 个 Excel 文件。")
    
    total_processed = 0
    
    for idx, filename in enumerate(files):
        file_path = os.path.join(TARGET_DIR, filename)
        print(f"\n[{idx+1}/{len(files)}] 处理文件: {filename}")
        
        positions = process_excel(file_path)
        if positions:
            upload_to_supabase(positions)
            total_processed += len(positions)
        
        # 稍微暂停一下，避免请求过于频繁
        # time.sleep(0.5)

    print(f"\n========================================")
    print(f"所有任务完成！共处理 {len(files)} 个文件，累计提取 {total_processed} 条职位数据。")
    print(f"========================================")

if __name__ == "__main__":
    main()
