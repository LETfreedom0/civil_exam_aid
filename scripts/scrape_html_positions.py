import requests
from bs4 import BeautifulSoup
import os
import json
# from supabase import create_client, Client # Avoid using supabase package due to dependency issues
try:
    from postgrest import SyncPostgrestClient as PostgrestClient
except ImportError:
    from postgrest import PostgrestClient

# ================= Configuration =================
# HTML Page URL to Scrape
HTML_URL = "https://www.shaanxi.gov.cn/xw/ztzl/zxzt/zkzl/2026/2026gwyfj/202601/t20260126_3607929.html"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hubbzosfrhxnzwuiitcv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Fj0j0VPlvGuLLxhjcGMIWA_8KL4DAWV")

# Default values
DEFAULT_YEAR = 2026
DEFAULT_PROVINCE_CODE = "650000" # Hainan

# Filter Keywords
FILTER_KEYWORDS = ["榆林市生源或户籍，肢体三级残疾或肢体四级残疾"]

# Column Mapping (HTML Header Name -> DB Column Name)
COL_MAP = {
    "招录机关名称": "recruit_unit",
    "部门名称": "region_dept", # 兼容部门名称
    "用人单位": "recruit_unit", # 兼容用人单位
    "单位层级": "unit_level",
    "机构性质": "position_nature",
    "职位名称": "position_name",
    "职位代码": "position_code", # 增加职位代码
    "职位描述": "description", # 兼容职位描述
    "职位简介": "description",
    "录用计划（人）": "quota", # 兼容录用计划
    "招考人数": "quota",
    "学历": "education",
    "学位": "degree",
    "专业": "major",
    "政治面貌": "political_status",
    "基层工作最低年限": "grassroots_exp",
    "基层工作经历最低年限": "grassroots_exp", # 兼容字段
    "是否仅限应届高校毕业生招考": "fresh_grad",
    "户籍限制情况": "domicile",
    "是否组织专业考试": "is_set", # 兼容字段
    "是否在面试阶段进行专业能力测试": "is_set",
    "是否进行体能测评": "physical_test",
    "性别": "gender",
    "开考比例": "exam_ratio",
    "最低服务年限": "min_service_years",
    "咨询电话1": "phone1",
    "咨询电话2": "phone2",
    "其他条件": "other_requirements", # 映射到其他条件
    "是否限于面向“服务基层项目”人员报考": "candidate_identity", # 映射到人员身份
    "备注": "other_requirements" # 映射到其他条件
    # "咨询电话3": Append to phone2
    # "是否为艰苦边远地区": Append to other_requirements
    # "是否警务技术职位": Append to other_requirements
    # "其他": Append to other_requirements
    # "备注": Append to other_requirements
}

# 可选别名映射（DB 字段 -> 多个表头别名）
ALIAS_MAP = {
    "recruit_unit": ["招录机关", "用人单位", "招录机关名称"],
    "region_dept": ["部门名称", "所在部门"],
    "unit_level": ["单位层级", "机构层级"],
    "position_nature": ["机构性质", "单位性质", "职位性质"],
    "position_name": ["职位名称", "岗位名称", "岗位"],
    "position_code": ["职位代码", "岗位代码", "职位编号", "岗位编号"],
    "description": ["职位简介", "职位描述", "岗位简介", "岗位描述"],
    "quota": ["录用计划（人）", "招考人数", "计划录用人数", "招聘人数"],
    "education": ["学历", "学历要求"],
    "degree": ["学位", "学位要求"],
    "major": ["专业", "专业要求"],
    "political_status": ["政治面貌"],
    "grassroots_exp": ["基层工作最低年限", "基层工作经历最低年限", "基层工作年限"],
    "fresh_grad": ["是否仅限应届高校毕业生招考", "是否限应届"],
    "domicile": ["户籍限制情况", "户籍要求"],
    "is_set": ["是否组织专业考试", "是否在面试阶段进行专业能力测试"],
    "physical_test": ["是否进行体能测评", "是否体能测评"],
    "gender": ["性别", "性别要求"],
    "exam_ratio": ["开考比例"],
    "min_service_years": ["最低服务年限"],
    "phone1": ["咨询电话1", "咨询电话"],
    "phone2": ["咨询电话2"],
    "candidate_identity": ["是否限于面向“服务基层项目”人员报考", "人员身份"],
    "other_requirements": ["其他条件", "备注", "其他"]
}

# ===============================================

def load_config():
    """
    从 JSON 配置文件加载并覆盖脚本默认配置
    """
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), "scrape_html_positions.config.json")
        if not os.path.exists(cfg_path):
            return
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        global HTML_URL, SUPABASE_URL, SUPABASE_KEY
        global DEFAULT_YEAR, DEFAULT_PROVINCE_CODE, FILTER_KEYWORDS, COL_MAP
        if isinstance(cfg.get("HTML_URL"), str):
            HTML_URL = cfg["HTML_URL"]
        if isinstance(cfg.get("SUPABASE_URL"), str):
            SUPABASE_URL = cfg["SUPABASE_URL"]
            os.environ["SUPABASE_URL"] = SUPABASE_URL
        if isinstance(cfg.get("SUPABASE_KEY"), str):
            SUPABASE_KEY = cfg["SUPABASE_KEY"]
            os.environ["SUPABASE_KEY"] = SUPABASE_KEY
        if isinstance(cfg.get("DEFAULT_YEAR"), int):
            DEFAULT_YEAR = cfg["DEFAULT_YEAR"]
        if isinstance(cfg.get("DEFAULT_PROVINCE_CODE"), str):
            DEFAULT_PROVINCE_CODE = cfg["DEFAULT_PROVINCE_CODE"]
        if isinstance(cfg.get("FILTER_KEYWORDS"), list):
            FILTER_KEYWORDS = cfg["FILTER_KEYWORDS"]
        if isinstance(cfg.get("COL_MAP"), dict):
            COL_MAP = cfg["COL_MAP"]
        if isinstance(cfg.get("ALIAS_MAP"), dict):
            # 允许在配置中覆盖别名映射
            global ALIAS_MAP
            ALIAS_MAP = cfg["ALIAS_MAP"]
    except Exception:
        pass

load_config()

def _normalize_text(s):
    """
    规范化表头/单元格文本：去除空白、统一大小写、移除常见标点
    """
    if not isinstance(s, str):
        return ""
    s = s.strip()
    # 中文标点与括号统一处理
    for ch in ["\u3000", "（", "）", "(", ")", "：", ":", "，", ","]:
        s = s.replace(ch, "")
    return s.lower()

def _build_runtime_mappings():
    """
    构建运行时映射：
    - exact_map：精确表头文本 -> DB 字段
    - regex_map：正则模式 -> DB 字段（当键以 're:' 开头时）
    - alias 展开：基于 ALIAS_MAP 将多个别名映射到同一 DB 字段
    """
    exact_map = {}
    regex_map = []
    # 先放入已有 COL_MAP 的直接映射
    for k, v in COL_MAP.items():
        if isinstance(k, str) and k.startswith("re:"):
            try:
                import re
                regex_map.append((re.compile(k[3:]), v))
            except Exception:
                continue
        else:
            exact_map[_normalize_text(k)] = v
    # 展开别名映射
    for db_col, aliases in ALIAS_MAP.items():
        for alias in aliases:
            if isinstance(alias, str) and alias.startswith("re:"):
                try:
                    import re
                    regex_map.append((re.compile(alias[3:]), db_col))
                except Exception:
                    continue
            else:
                exact_map[_normalize_text(alias)] = db_col
    return exact_map, regex_map

def _detect_header_row(rows, candidate_limit=80):
    """
    智能识别表头行：
    - 优先使用 <thead> 或包含 <th> 的行
    - 如果不存在，选择“与已知表头别名匹配数最多”的行
    """
    exact_map, regex_map = _build_runtime_mappings()
    # 1) 先找包含 th 的行
    for i, row in enumerate(rows[:candidate_limit]):
        ths = row.find_all('th')
        if ths:
            headers = [c.get_text(strip=True) for c in ths]
            if headers:
                return i, headers
    # 2) 统计匹配分数
    best_idx, best_headers, best_score = -1, [], 0
    for i, row in enumerate(rows[:candidate_limit]):
        cells = row.find_all(['th', 'td'])
        texts = [c.get_text(strip=True) for c in cells]
        score = 0
        for t in texts:
            nt = _normalize_text(t)
            if nt in exact_map:
                score += 2
            else:
                for pat, _db in regex_map:
                    try:
                        if pat.search(t):
                            score += 1
                            break
                    except Exception:
                        continue
        if score > best_score:
            best_idx, best_headers, best_score = i, texts, score
    # 3) 设置阈值避免误判（至少匹配到 3 个已知表头）
    if best_idx != -1 and best_score >= 6:
        return best_idx, best_headers
    return -1, []

def fetch_html(url):
    """
    抓取目标网页 HTML，带重试与流式读取
    """
    print(f"Fetching {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
# 增加重试机制和流式下载
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        response = session.get(url, headers=headers, stream=True, timeout=30)
        response.encoding = response.apparent_encoding
        
        # 强制读取全部内容，处理 IncompleteRead
        content = b""
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                content += chunk
                
        return content.decode(response.encoding, errors='replace')
    except Exception as e:
        print(f"Error fetching: {e}")
        return None

def parse_table(html):
    """
    解析 HTML 表格为岗位列表，依据 COL_MAP 映射字段并应用筛选
    """
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        print("No tables found.")
        return []
    
    table = tables[0]
    rows = table.find_all('tr')
    print(f"Total rows: {len(rows)}")
    # 更稳健的表头识别
    header_row_idx, headers = _detect_header_row(rows)
    if header_row_idx == -1:
        print("Could not find header row.")
        # 输出前若干行用于排查
        for i, row in enumerate(rows[:10]):
            cells = row.find_all(['th', 'td'])
            texts = [c.get_text(strip=True) for c in cells]
            print(f"Row {i}: {texts}")
        return []
    print(f"Header found at row {header_row_idx}: {headers}")
    
    data_list = []
    current_section = "" # For "exam_region" (e.g., 区直机关)
    
    # 构建运行时映射并对表头进行归一化
    exact_map, regex_map = _build_runtime_mappings()
    normalized_headers = [_normalize_text(h) for h in headers]
    db_header_map = []
    unmapped_headers = []
    for h, nh in zip(headers, normalized_headers):
        if nh in exact_map:
            db_header_map.append(exact_map[nh])
        else:
            mapped = None
            for pat, db_col in regex_map:
                try:
                    if pat.search(h):
                        mapped = db_col
                        break
                except Exception:
                    continue
            if mapped:
                db_header_map.append(mapped)
            else:
                db_header_map.append(None)
                unmapped_headers.append(h)
    if unmapped_headers:
        print(f"未识别的表头: {unmapped_headers}")
    
    # Iterate data rows
    for i in range(header_row_idx + 1, len(rows)):
        row = rows[i]
        cells = row.find_all(['th', 'td'])
        texts = [c.get_text(strip=True) for c in cells]
        
        # Skip empty rows
        if not texts or not any(texts):
            continue
            
        # Check for section header (usually 1 column spanning across)
        # Or if the row length is significantly shorter than headers
        # In the preview: Row 10: ['区直机关（17人）'] -> Length 1
        if len(texts) == 1:
            current_section = texts[0]
            # print(f"New Section: {current_section}")
            continue
            
        # Check for "条件" row (Row 9 in preview)
        if "条件" in texts and len(texts) < 5:
            continue
        # 跳过二级表头（如“专科/本科/研究生”等）
        subheader_tokens = {"专科", "本科", "研究生"}
        # 如果本行包含 th，或本行文本全部属于 subheader_tokens，则跳过
        is_th_row = bool(row.find_all('th'))
        if is_th_row or (texts and all(t in subheader_tokens for t in texts if t)):
            continue

        # Normal data row
        # Ensure it matches header length mostly
        # Sometimes merged cells make length vary, but usually `td` count matches if no colspan
        # We'll assume simple structure for now, or pad with empty strings
        
        if len(texts) < len(headers):
            # Try to handle simple colspan cases or just pad
            texts += [""] * (len(headers) - len(texts))
        
        item = {
            "exam_region": current_section,
            "year": DEFAULT_YEAR,
            "province_code": DEFAULT_PROVINCE_CODE,
            "other_requirements": ""
        }
        
        # Raw row text for filtering
        raw_row_text = "".join(texts)
        
        for h_idx, header in enumerate(headers):
            if h_idx >= len(texts): break
            val = texts[h_idx]
            
            # 使用 db_header_map 进行标准列映射（支持别名）
            db_col = db_header_map[h_idx] if h_idx < len(db_header_map) else None
            if db_col:
                # Special handling for quota (int)
                if db_col == "quota":
                    try:
                        item[db_col] = int(val)
                    except:
                        item[db_col] = 0
                # Special handling for other_requirements (append instead of overwrite)
                elif db_col == "other_requirements":
                    if val and val.strip():
                        if item[db_col]:
                            item[db_col] += f"; {val}"
                        else:
                            item[db_col] = val
                else:
                    item[db_col] = val
            
            # Map special columns to other_requirements
            elif header in ["是否为艰苦边远地区", "是否警务技术职位", "其他", "备注"]:
                if val and val not in ["否", "无", ""]:
                    prefix = f"{header}: " if header not in ["其他", "备注"] else ""
                    item["other_requirements"] += f"{prefix}{val}; "
            
            # Map phone3
            elif header == "咨询电话3" and val:
                 if "phone2" in item and item["phone2"]:
                     item["phone2"] += f", {val}"
                 else:
                     item["phone2"] = val

        # Filter check
        if FILTER_KEYWORDS:
            is_match = False
            for keyword in FILTER_KEYWORDS:
                if keyword in raw_row_text:
                    is_match = True
                    break
            
            if not is_match:
                continue

        data_list.append(item)
        
    print(f"Parsed {len(data_list)} positions.")
    return data_list

def upload_to_supabase(data):
    """
    通过 PostgREST 将岗位数据批量上传到 Supabase
    """
    if not data:
        return

    print("Connecting to Supabase (via Postgrest)...")
    try:
        # Construct PostgREST URL
        rest_url = f"{SUPABASE_URL}/rest/v1"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Initialize PostgrestClient
        # Note: PostgrestClient usage might vary slightly by version. 
        # Usually: client = PostgrestClient(base_url, headers=headers)
        # But some versions might need schema or other params.
        # Let's try standard init.
        client = PostgrestClient(rest_url, headers=headers)
        
        batch_size = 100
        total = len(data)
        
        for i in range(0, total, batch_size):
            batch = data[i : i + batch_size]
            print(f"Uploading {i+1} - {min(i+batch_size, total)}...")
            
            # Clean up data before insert (remove empty keys, etc)
            clean_batch = []
            for d in batch:
                d["other_requirements"] = d["other_requirements"].strip("; ")
                clean_batch.append(d)

            response = client.from_("positions").insert(clean_batch).execute()
            
        print("Upload complete!")
        
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    html = fetch_html(HTML_URL)
    if html:
        positions = parse_table(html)
        if positions:
            # Preview
            print("Preview first item:")
            print(json.dumps(positions[0], ensure_ascii=False, indent=2))
            
            upload_to_supabase(positions)
