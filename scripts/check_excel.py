import openpyxl
import os
import re

FILE_PATH = r"C:\Users\Administrator\Downloads\四川2026省考\1.广安市2026年度市、县、乡公开考试录用公务员（参照管理工作人员）职位情况表.xlsx"
FILTER_KEYWORDS = ["残疾", "残障", "聋哑", "盲人"]
CHECK_COLUMNS = ["其他条件", "备注", "职位简介", "职位描述", "其他要求", "其他报考条件","其他","招考对象","其它"]
HEADER_ROW = 3
HEADER_HEIGHT = 1

def check_file():
    if not os.path.exists(FILE_PATH):
        print("文件不存在")
        return

    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    sheet = wb.active # 广安市 sheet
    rows = list(sheet.rows)
    print(f"Sheet: {sheet.title}")
    print(f"总行数: {len(rows)}")
    
    # 模拟表头查找
    best_header_row_idx = -1
    max_match_count = 0
    key_columns = ["招录单位", "职位名称", "专业", "学历", "人数", "指标", "代码", "备注", "单位名称", "职位编码"]
    
    for r_idx in range(min(20, len(rows))):
        row_values = [str(cell.value).strip() for cell in rows[r_idx] if cell.value]
        row_text = " ".join(row_values)
        match_count = 0
        for key in key_columns:
            if key in row_text:
                match_count += 1
        if match_count > max_match_count:
            max_match_count = match_count
            best_header_row_idx = r_idx
            
    print(f"表头行索引: {best_header_row_idx}")
    current_header_row_start = best_header_row_idx
    
    # 构建 headers
    raw_headers = []
    for i in range(HEADER_HEIGHT):
        current_row_idx = current_header_row_start + i
        if current_row_idx < len(rows):
            row_values = [cell.value for cell in rows[current_row_idx]]
            raw_headers.append(row_values)
            
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
            
    print(f"Headers: {headers}")
    
    # 确定检查列
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
        
        if not check_col_indices:
            print("未找到指定列，将检查所有列")
            check_col_indices = range(len(headers))
        else:
            print(f"检查列索引: {check_col_indices}")
            
    # 遍历数据
    current_data_start_idx = current_header_row_start + HEADER_HEIGHT
    match_rows = 0
    
    for r_idx, row in enumerate(rows[current_data_start_idx:]):
        real_idx = current_data_start_idx + r_idx
        if not any(cell.value for cell in row):
            continue
            
        is_match = False
        matched_kw = ""
        matched_val = ""
        
        for idx in check_col_indices:
            if idx < len(row):
                cell_value = str(row[idx].value) if row[idx].value is not None else ""
                for keyword in FILTER_KEYWORDS:
                    if keyword in cell_value:
                        is_match = True
                        matched_kw = keyword
                        matched_val = cell_value
                        break
            if is_match:
                break
                
        if is_match:
            match_rows += 1
            print(f"行 {real_idx+1} 匹配! 关键词: '{matched_kw}' in '{matched_val}'")
            
    print(f"总匹配行数: {match_rows}")

if __name__ == "__main__":
    check_file()
