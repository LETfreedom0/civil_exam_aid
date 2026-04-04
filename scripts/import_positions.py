import os
import requests
import openpyxl
import json
import sys
import os.path

# ================= 配置区域 =================
# Supabase 配置
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hubbzosfrhxnzwuiitcv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Fj0j0VPlvGuLLxhjcGMIWA_8KL4DAWV")
        
# 目标 Excel 文件 URL (如果为空，则只处理本地文件)
# 注意：如果是本地文件，请直接修改下方的 LOCAL_FILE_PATH，不要填在这里
EXCEL_URL = ""

# 本地文件路径 (支持绝对路径，请使用 r"" 防止转义错误)
LOCAL_FILE_PATH = r"C:\Users\Administrator\Downloads\浙江2026省考\甘肃省2026年度公务员招考职位表.xlsx"

# 筛选关键词
# 默认为 ["残疾", "残障"]。如果留空 []，则不过滤，导入所有数据。
FILTER_KEYWORDS = ["中华人民共和国残疾人证","肢体残疾四级","面向残疾人","肢体残疾","听力残疾","面向听力、肢体残疾3-4级持证残疾人"]

# 检查关键词的 Excel 列
CHECK_COLUMNS = ["其他条件", "备注", "职位简介", "职位描述", "其他要求", "其他报考条件","其他","招考对象","其它"]

# Excel 表头所在的行号（从 1 开始计数，例如第 4 行）
# 如果表头跨多行（如 4、5 行），这里填起始行（4），脚本会自动合并后续行
HEADER_ROW = 3
HEADER_HEIGHT = 2 # 表头占据的行数

# 数据开始的行号（从 1 开始计数，例如第 5 行）
DATA_START_ROW = 5

# Excel 列名到数据库字段的映射
COLUMN_MAPPING = {
    "exam_region": ["考区", "所属地区", "地区名称", "地区、部门"],
    "recruit_unit": ["招考单位", "单位名称", "招录单位", "招录机关", "上报单位", "部门名称","招录机关（单位)"],
    "unit_level": ["单位层级", "机构层级", "职位层级", "部门属性", "部门性质", "隶属关系"],
    "position_name": ["招考职位", "职位名称","拟任职务"],
    "position_code": ["职位代码", "职位编码", "代码"],
    "position_nature": ["职位性质", "职位工作性质及需要说明的其他事项"],
    "exam_subjects": ["笔试考试科目", "所属大类", "所属小类", "须注明的考试科目 申论类别", "专业科目", "公共科目类型", "科目类别", "笔试科目"],
    "quota": ["录用人数", "招录人数", "招录指标", "招考人数", "招考名额", "招录名额"],
    "candidate_identity": ["招录对象", "招考对象", "考录对象", "报考人员身份要求", "定向招录项目要求 服务基层项目人员", "优秀村(社区)干部", "驻村第一书记和工作队员", "少数民族", "2026届毕业生", "具有本科以上学历的安排工作的退役军士和义务兵", "民族"],
    "grassroots_exp": ["工作经历要求", "基层工作年限要求", "基层工作经历要求", "2年及以上基层工作经历要求", "基层工作经历最低年限", "基层工作经历时间", "经历要求"],
    "gender": ["性别", "性别要求"],
    "max_age": ["最高年龄要求", "年龄"],
    "education": ["学历学位", "学历", "最低学历要求", "学历要求"],
    "degree": ["学历学位", "学位", "学位要求"],
    "major": ["研究生专业名称及代码", "本科专业名称及代码", "大专专业名称及代码", "专科专业名称及代码", "专业要求", "专业", "职位资格条件和要求 专业"],
    "domicile": ["户籍要求", "户别要求", "户籍", "考录范围"],
    "certification": ["资格证书", "职业资格证书等要求"],
    "other_requirements": ["其他资格条件", "其他要求", "其他招录条件及说明", "其它条件", "其他报考条件", "其他", "备注（职位简介）", "备注", "其他条件", "其它"],
    "min_service_years": ["最低服务年限要求"],
    "exam_ratio": ["笔试最低开考比例", "笔试开考比例", "开考比例"],
    "physical_test_standards": ["体能测评", "体能测评项目和标准"],
    "medical_test_standards": ["心理素质测评", "体检标准"],
    "phone1": ["招考部门电话", "咨询电话1", "咨询电话", "考生咨询电话", "单位咨询电话"],
    "phone2": ["咨询电话2"],
    
    # 兼容原有字段映射
    "region_dept": ["招考部门", "地区部门", "用人部门", "部门代码", "内设机构"],
    "position_type": ["职位类型", "职位类别", "机构性质",],
    "rank_level": ["职级层次", "职位层级"],
    "political_status": ["政治面貌", "政治面貌要求"],
    "fresh_grad": ["是否限应届毕业生报考", "面向应届毕业生招考"],
    "fresh_grad_year": ["面向2026年应届毕业生招考"],
    "exam_type": ["笔试考试类型", "考试类别","使用试题"],
    "essay_subject": ["申论科目", "申论考试类型"],
    "police_subject": ["公安类专业科目"],
    "legal_knowledge": ["法律基础知识"],
    "physical_test": ["体能测评比例"],
    "is_set": ["专业能力测试是否测试", "是否组织专业能力测试"],
    "test_ratio": ["专业能力测试比例"],
    "interview_ratio": ["面试比例", "面试人数与计划录用人数的比例", "面试开考比例"],
    "inspection_ratio": ["考察比例"],
    "description": ["职位简介", "职位描述", "备注（职位简介）"],
}

# 默认值
DEFAULT_VALUES = {
    "year": 2026,
    "province_code": "620000"
}

# ===========================================

class _Cell:
    """
    简单的单元格对象，统一提供 .value 属性，兼容 openpyxl/xlrd 两种读取方式
    """
    def __init__(self, value):
        self.value = value

def read_xls_rows(file_path: str):
    """
    直接读取 .xls 文件为按工作表拆分的行列表
    返回: dict[sheet_name] = List[List[_Cell]]
    """
    try:
        import xlrd
        wb = xlrd.open_workbook(file_path)
        result = {}
        for sheet in wb.sheets():
            rows = []
            for r in range(sheet.nrows):
                values = []
                row = sheet.row(r)
                for c in row:
                    values.append(_Cell(c.value))
                rows.append(values)
            result[sheet.name] = rows
        return result
    except Exception as e:
        print(f"xlrd 读取 .xls 失败: {e}")
        return None

def convert_xls_to_xlsx(file_path: str) -> str | None:
    """
    将单个 .xls 文件转换为 .xlsx，返回转换后的新路径
    """
    try:
        import win32com.client as win32
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(file_path)
        new_path = file_path + "x"
        wb.SaveAs(new_path, FileFormat=51)
        wb.Close()
        excel.Quit()
        print(f"已转换为 .xlsx: {new_path}")
        return new_path
    except Exception as e:
        print(f"自动转换 .xls 失败: {e}")
        print("请使用 scripts/convert_xls_to_xlsx.py 先转换为 .xlsx 再重试。")
        return None

def load_config():
    """
    从 JSON 配置文件加载并覆盖脚本默认配置
    """
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), "import_positions.config.json")
        if not os.path.exists(cfg_path):
            return
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        global SUPABASE_URL, SUPABASE_KEY, EXCEL_URL, LOCAL_FILE_PATH
        global FILTER_KEYWORDS, CHECK_COLUMNS, HEADER_ROW, HEADER_HEIGHT, DATA_START_ROW
        global COLUMN_MAPPING, DEFAULT_VALUES
        if isinstance(cfg.get("SUPABASE_URL"), str):
            SUPABASE_URL = cfg["SUPABASE_URL"]
            os.environ["SUPABASE_URL"] = SUPABASE_URL
        if isinstance(cfg.get("SUPABASE_KEY"), str):
            SUPABASE_KEY = cfg["SUPABASE_KEY"]
            os.environ["SUPABASE_KEY"] = SUPABASE_KEY
        if isinstance(cfg.get("EXCEL_URL"), str):
            EXCEL_URL = cfg["EXCEL_URL"]
        if isinstance(cfg.get("LOCAL_FILE_PATH"), str):
            LOCAL_FILE_PATH = cfg["LOCAL_FILE_PATH"]
        if isinstance(cfg.get("FILTER_KEYWORDS"), list):
            FILTER_KEYWORDS = cfg["FILTER_KEYWORDS"]
        if isinstance(cfg.get("CHECK_COLUMNS"), list):
            CHECK_COLUMNS = cfg["CHECK_COLUMNS"]
        if isinstance(cfg.get("HEADER_ROW"), int):
            HEADER_ROW = cfg["HEADER_ROW"]
        if isinstance(cfg.get("HEADER_HEIGHT"), int):
            HEADER_HEIGHT = cfg["HEADER_HEIGHT"]
        if isinstance(cfg.get("DATA_START_ROW"), int):
            DATA_START_ROW = cfg["DATA_START_ROW"]
        if isinstance(cfg.get("COLUMN_MAPPING"), dict):
            COLUMN_MAPPING = cfg["COLUMN_MAPPING"]
        if isinstance(cfg.get("DEFAULT_VALUES"), dict):
            DEFAULT_VALUES = cfg["DEFAULT_VALUES"]
    except Exception as e:
        pass

load_config()

def download_excel(url, save_path):
    if not url:
        print("未提供 URL，跳过下载步骤。")
        return False
    
    print(f"开始从 {url} 下载文件...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"文件已保存至 {save_path}")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False

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
    print(f"正在读取 {file_path} ...")
    try:
        all_filtered_data = []
        if file_path.lower().endswith(".xls"):
            sheets_rows = read_xls_rows(file_path)
            if not sheets_rows:
                print("尝试自动转换为 .xlsx ...")
                new_path = convert_xls_to_xlsx(file_path)
                if not new_path or not os.path.exists(new_path):
                    print("无法读取或转换该 .xls 文件。")
                    return []
                file_path = new_path
                wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                sheetnames = wb.sheetnames
                get_rows = lambda name: list(wb[name].rows)
            else:
                sheetnames = list(sheets_rows.keys())
                get_rows = lambda name: sheets_rows[name]
        else:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheetnames = wb.sheetnames
            get_rows = lambda name: list(wb[name].rows)

        for sheet_name in sheetnames:
            print(f"正在处理工作表: {sheet_name}")
            rows = get_rows(sheet_name)
            if not rows:
                print(f"工作表 {sheet_name} 为空，跳过")
                continue

            # -----------------------------------------------------------
            # 动态查找表头行
            # 策略：检查前 20 行，看哪一行包含最多的 COLUMN_MAPPING 关键字
            # -----------------------------------------------------------
            best_header_row_idx = -1
            max_match_count = 0
            
            # 要检查的关键列名（用于识别表头）
            key_columns = ["招录单位", "职位名称", "专业", "学历", "人数", "指标", "代码", "备注", "单位名称"]
            
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
            
            if best_header_row_idx == -1 or max_match_count < 2:
                # 如果没找到明显的表头，尝试回退到默认 HEADER_ROW
                print(f"工作表 {sheet_name} 未自动检测到表头，尝试使用默认行 {HEADER_ROW}")
                current_header_row_start = HEADER_ROW - 1
            else:
                print(f"工作表 {sheet_name} 检测到表头在第 {best_header_row_idx + 1} 行 (匹配度: {max_match_count})")
                current_header_row_start = best_header_row_idx

            if current_header_row_start >= len(rows):
                 print(f"工作表 {sheet_name} 表头行超出范围，跳过")
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
                    # 收集该列所有行的非空值
                    col_values = []
                    for row_idx in range(len(raw_headers)):
                        if col_idx < len(raw_headers[row_idx]):
                            val = raw_headers[row_idx][col_idx]
                            if val is not None and str(val).strip():
                                # 去除换行符、全角空格、nbsp 并 strip
                                val_str = str(val).strip().replace('\n', '').replace('\u3000', '').replace('\xa0', '').replace(' ', '')
                                if val_str not in col_values: # 避免重复
                                    col_values.append(val_str)
                    
                    # 拼接成一个完整的表头名称，例如 "笔试 考试科目"
                    # 或者如果只有下一行有值，就取下一行
                    full_header_name = " ".join(col_values)
                    headers.append(full_header_name)
                    
            print(f"合并后的 Excel 表头: {headers}")
            
            # 调试：检查列名映射
            print("--- 调试：检查列名映射 ---")
            for db_field, possible_names in COLUMN_MAPPING.items():
                # 修改匹配逻辑：只要合并后的表头包含 possible_names 中的任意一个词，就算匹配
                # 或者精确匹配
                idx = -1
                for h_idx, header_val in enumerate(headers):
                    if not header_val: continue
                    for name in possible_names:
                        # 策略1: 精确匹配
                        if name == header_val:
                            idx = h_idx
                            break
                        # 策略2: 包含匹配 (如果表头是 "笔试 开考比例"，而我们找 "开考比例")
                        if name in header_val.split(): # 按空格分割后匹配单词，避免部分匹配错误
                            idx = h_idx
                            break
                    if idx != -1:
                        break
                
                if idx != -1:
                    print(f"[√] {db_field} -> 列索引 {idx} (表头: {headers[idx]})")
                else:
                    pass
                    # print(f"[×] {db_field} -> 未找到匹配列 (尝试: {possible_names})")
            print("---------------------------")
            
            # 确定要检查关键词的列索引
            check_col_indices = []
            for col_name in CHECK_COLUMNS:
                # 使用上面相同的匹配逻辑查找列索引
                idx = -1
                for h_idx, header_val in enumerate(headers):
                    if not header_val: continue
                    # 对于关键词列，允许模糊匹配
                    if col_name in header_val: 
                        idx = h_idx
                        break
                
                if idx != -1:
                    check_col_indices.append(idx)
            
            # 如果没找到指定列，检查所有文本列
            if not check_col_indices:
                print("警告: 未找到用于筛选关键词的列，将检查所有列。")
                check_col_indices = range(len(headers))

            # 遍历数据行 (从表头结束后的下一行开始)
            current_data_start_idx = current_header_row_start + HEADER_HEIGHT
            
            # 判断当前 sheet 是否为 "残疾人" 相关
            is_disabled_sheet = "残疾人" in sheet_name
            if is_disabled_sheet:
                print(f"检测到特殊 Sheet '{sheet_name}'，将无视关键词筛选，直接导入所有行。")

            for row in rows[current_data_start_idx:]:
                is_match = False
                
                # 如果是残疾人 Sheet，直接匹配
                if is_disabled_sheet:
                    is_match = True
                # 如果没有筛选关键词，默认匹配所有行
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
                
                if is_match:
                    db_item = {}
                    # 初始化所有字段为 None，确保 JSON 结构一致
                    for key in COLUMN_MAPPING.keys():
                        db_item[key] = None

                    # 映射字段
                    for db_field, possible_names in COLUMN_MAPPING.items():
                        if db_field == "major":
                            # 特殊处理 major 字段：合并多列（研究生/本科/大专）
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
                                        # 尝试添加前缀以区分不同学历层次的专业
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
                            # 常规处理：取第一个匹配的列
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
                    
                    # 特殊处理
                    if db_item.get("quota"):
                        try:
                            db_item["quota"] = int(float(db_item["quota"]))
                        except:
                            db_item["quota"] = 0
                    else:
                        db_item["quota"] = 0
                    
                    # # 默认值
                    # DEFAULT_VALUES = {
                    #     "year": DEFAULT_VALUES.year,
                    #     "province_code": DEFAULT_VALUES.province_code,
                    #     "max_age": 38,
                    #     "min_age": 18
                    # }
                    for k, v in DEFAULT_VALUES.items():
                        if db_item.get(k) is None:
                            db_item[k] = v
                    
                    all_filtered_data.append(db_item)
                
        print(f"筛选完成，共找到 {len(all_filtered_data)} 条符合条件的岗位。")
        if not all_filtered_data and rows:
             print("\n警告: 筛选结果为 0 条。可能是因为：")
             print("1. 筛选关键词过严（当前: {}）".format(FILTER_KEYWORDS))
             print("2. 筛选列未正确识别（尝试检查以下列: {}）".format(CHECK_COLUMNS))
             print("3. 表头解析错误 (请检查上方的 '合并后的 Excel 表头' 输出)")
             
             # 打印第一行数据示例，方便排查
             first_data_row_idx = current_data_start_idx
             if first_data_row_idx < len(rows):
                 print("\nExcel 第一行数据示例:")
                 print([cell.value for cell in rows[first_data_row_idx]])

        # 对数据进行去重（基于唯一键）
        if all_filtered_data:
            seen = set()
            unique_data = []
            for item in all_filtered_data:
                key = f"{item.get('position_name', '')}|{item.get('recruit_unit', '')}|{item.get('province_code', '')}|{item.get('year', '')}"
                if key not in seen:
                    seen.add(key)
                    unique_data.append(item)
            duplicates = len(all_filtered_data) - len(unique_data)
            if duplicates > 0:
                print(f"去重：发现 {duplicates} 条重复数据，已去除")
            all_filtered_data = unique_data
        
        if all_filtered_data:
            print("数据预览 (前1条):")
            print(json.dumps(all_filtered_data[0], ensure_ascii=False, indent=2))
        return all_filtered_data
        
    except Exception as e:
        print(f"处理 Excel 失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def upload_to_supabase(data):
    import time
    import hashlib
    
    # 生成执行ID用于追踪
    exec_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    print(f"\n========== 上传任务开始 (ID: {exec_id}) ==========")
    print(f"数据条数: {len(data) if data else 0}")
    
    if not data:
        print("没有数据需要上传。")
        return

    if "YOUR_SUPABASE_URL" in SUPABASE_URL:
        print("错误: 请先配置 SUPABASE_URL 和 SUPABASE_KEY。")
        print("数据预览 (前1条):")
        print(json.dumps(data[0], ensure_ascii=False, indent=2))
        return
    print("正在连接 Supabase (via REST API)...")
    try:
        # 构造 API URL
        api_url = f"{SUPABASE_URL}/rest/v1/positions"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        # 第一步：获取所有已存在的记录（使用组合唯一键）
        # 唯一键：position_name + recruit_unit + province_code + year
        print("正在检查已有数据...")
        existing_keys = set()
        offset = 0
        batch = 1000
        while True:
            query_url = f"{api_url}?select=position_name,recruit_unit,province_code,year&limit={batch}&offset={offset}"
            resp = requests.get(query_url, headers=headers)
            if resp.status_code >= 400:
                print(f"查询失败: {resp.text}")
                break
            rows = resp.json()
            if not rows:
                break
            for row in rows:
                pn = row.get("position_name") or ""
                ru = row.get("recruit_unit") or ""
                pv = row.get("province_code") or ""
                yr = str(row.get("year")) or ""
                if pn:  # 只有有职位名称的才加入
                    key = f"{pn}|{ru}|{pv}|{yr}"
                    existing_keys.add(key)
            offset += batch
            if len(rows) < batch:
                break
        
        print(f"数据库中已有 {len(existing_keys)} 条记录")
        
        # 第二步：分别处理每条数据
        total = len(data)
        inserted_count = 0
        updated_count = 0
        
        for i, item in enumerate(data):
            position_name = item.get("position_name") or ""
            recruit_unit = item.get("recruit_unit") or ""
            province_code = item.get("province_code") or ""
            year = str(item.get("year")) or ""
            unique_key = f"{position_name}|{recruit_unit}|{province_code}|{year}"
            
            if not position_name:
                # 没有职位名称，直接插入
                response = requests.post(api_url, headers=headers, json=[item])
                if response.status_code < 400:
                    inserted_count += 1
                else:
                    print(f"插入失败: {response.text}")
                continue
            
            if unique_key in existing_keys:
                # 已存在，执行更新（PATCH）
                # 使用多个条件匹配
                update_url = f"{api_url}?position_name=eq.{position_name}&recruit_unit=eq.{recruit_unit}&province_code=eq.{province_code}&year=eq.{year}"
                response = requests.patch(update_url, headers=headers, json=item)
                if response.status_code < 400:
                    updated_count += 1
                else:
                    print(f"更新失败 ({position_name}): {response.text}")
            else:
                # 不存在，执行插入
                response = requests.post(api_url, headers=headers, json=[item])
                if response.status_code < 400:
                    inserted_count += 1
                    existing_keys.add(unique_key)  # 添加到已存在集合
                else:
                    print(f"插入失败 ({position_name}): {response.text}")
            
            # 打印进度
            if (i + 1) % 50 == 0 or (i + 1) == total:
                print(f"进度: {i+1}/{total}")
            # 打印进度
            if (i + 1) % 50 == 0 or (i + 1) == total:
                print(f"进度: {i+1}/{total}")
        
        print(f"\n========== 上传任务结束 (ID: {exec_id}) ==========")
        print(f"共插入 {inserted_count} 条记录")
        
    except Exception as e:
        print(f"上传失败: {e}")
def main():
    # 支持通过命令行参数传入文件路径
    target_file_path = LOCAL_FILE_PATH
    if len(sys.argv) > 1:
        target_file_path = sys.argv[1]
        print(f"使用命令行参数指定的文件: {target_file_path}")
    elif EXCEL_URL:
        # 只有在未指定命令行参数且配置了 URL 时才下载
        download_excel(EXCEL_URL, LOCAL_FILE_PATH)
        target_file_path = LOCAL_FILE_PATH
    
    if os.path.exists(target_file_path):
        positions = process_excel(target_file_path)
        if positions:
            upload_to_supabase(positions)
    else:
        print(f"未找到文件 {target_file_path}")

if __name__ == "__main__":
    main()
