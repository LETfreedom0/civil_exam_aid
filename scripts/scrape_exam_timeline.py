import requests
from bs4 import BeautifulSoup
import re
import json
import datetime
import sys
import os
from urllib.parse import urlparse, parse_qs, unquote
from io import BytesIO

try:
    from docx import Document
except ImportError:
    print("请先安装 python-docx 库: pip install python-docx")
    sys.exit(1)

# ================= 配置区域 =================
# Supabase 配置
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hubbzosfrhxnzwuiitcv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Fj0j0VPlvGuLLxhjcGMIWA_8KL4DAWV")

# 默认年份 (如果无法自动识别)
DEFAULT_YEAR = 2026

# 省份映射
PROVINCE_MAP = {
  "北京": "110000", "天津": "120000", "河北": "130000", "山西": "140000", "内蒙古": "150000",
  "辽宁": "210000", "吉林": "220000", "黑龙江": "230000", "上海": "310000", "江苏": "320000",
  "浙江": "330000", "安徽": "340000", "福建": "350000", "江西": "360000", "山东": "370000",
  "河南": "410000", "湖北": "420000", "湖南": "430000", "广东": "440000", "广西": "450000",
  "海南": "460000", "重庆": "500000", "四川": "510000", "贵州": "520000", "云南": "530000",
  "西藏": "540000", "陕西": "610000", "甘肃": "620000", "青海": "630000", "宁夏": "640000",
  "新疆": "650000"
}

# 关键词映射 (关键词 -> 数据库字段)
# 注意：正则会匹配包含这些关键词的句子
KEYWORD_MAPPING = {
    "signup_start": ["报名时间", "报名起止", "提交报名申请", "提交报考申请", "报名日期", "注册报名"],
    "signup_end": ["报名截止", "报名结束", "交费时间", "缴费截止", "截止时间", "不再显示"], 
    "payment_end": ["缴费截止", "截止时间", "网上缴费"], # 去掉容易误判的"报名确认"
    "admit_card_start": ["准考证", "打印准考证", "下载打印", "打印笔试准考证"],
    "exam_date": ["笔试时间", "公共科目笔试", "行政职业能力测验", "申论", "专业科目笔试", "公共科目笔试时间", "笔试时间、地点"],
    "score_date": ["成绩查询", "查询成绩", "公布成绩", "成绩公布", "查询本人笔试成绩", "笔试成绩查询"],
    "interview_date_start": ["面试", "资格复审", "资格审查", "参加笔试确认"]
}

# ===========================================

def detect_context(text):
    """检测年份和省份"""
    year = DEFAULT_YEAR
    province_code = "460000" # 默认海南省   
    
    # 检测年份 (e.g., 2026年度)
    year_match = re.search(r"(\d{4})年度", text[:1000]) # 只看前1000字
    if year_match:
        year = int(year_match.group(1))
        print(f"自动检测到年份: {year}")
        
    # 检测省份
    for name, code in PROVINCE_MAP.items():
        if name in text[:500]: # 标题通常在前500字
            province_code = code
            print(f"自动检测到省份: {name} ({code})")
            break
            
    return year, province_code

def fetch_content(url):
    print(f"正在分析 URL: {url} ...")
    
    # 1. 处理 Office Online Viewer 链接
    parsed_url = urlparse(url)
    if "view.officeapps.live.com" in parsed_url.netloc or "officeapps.live.com" in parsed_url.netloc:
        query = parse_qs(parsed_url.query)
        if "src" in query:
            real_url = query["src"][0]
            print(f"检测到 Office 预览链接，提取真实文档地址: {real_url}")
            url = real_url
            
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        url_lower = url.lower()
        
        # 2. 处理 Word 文档 (.docx)
        if url_lower.endswith('.docx') or 'wordprocessingml.document' in content_type:
            print("正在下载并解析 Word 文档...")
            doc = Document(BytesIO(response.content))
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            # 也可以提取表格内容，视需求而定
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        full_text.append(cell.text)
            return "\n".join(full_text)
            
        # 3. 处理普通网页 (HTML)
        else:
            print("正在解析 HTML 网页...")
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            # 移除 script 和 style
            for script in soup(["script", "style"]):
                script.extract()
            
            # 策略优化：使用空格连接所有文本，然后合并空白字符，再按标点分句
            # 这样可以解决标签过多导致文本被打散的问题
            text = soup.get_text(separator=" ")
            
            # 合并多余空白
            text = re.sub(r'\s+', ' ', text)
            return text
            
    except Exception as e:
        print(f"获取内容失败: {e}")
        return None

def extract_dates(text, context_year=DEFAULT_YEAR):
    """
    从文本中提取日期。
    context_year: 上下文年份 (例如 "2026年度" -> 2026)
    策略：
    - 如果日期包含明确年份，使用该年份。
    - 如果只有月日：
      - 如果月份 >= 9，假设是上一年的 (context_year - 1)
      - 如果月份 < 9，假设是当年的 (context_year)
    """
    dates = []
    
    # 正则表达式匹配多种日期格式 (允许中间有空格)
    patterns = [
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        r"(\d{4})\s*\.\s*(\d{1,2})\s*\.\s*(\d{1,2})",
        r"(\d{4})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})",
        r"(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            groups = match.groups()
            try:
                if len(groups) == 3: # 有年份
                    y, m, d = int(groups[0]), int(groups[1]), int(groups[2])
                elif len(groups) == 2: # 无年份
                    m, d = int(groups[0]), int(groups[1])
                    # 智能判断年份
                    if m >= 9:
                        y = context_year - 1
                    else:
                        y = context_year
                
                # 简单验证日期有效性
                date_obj = datetime.date(y, m, d)
                dates.append(date_obj.isoformat())
            except ValueError:
                continue
                
    # 去重并排序
    return sorted(list(set(dates)))

def parse_announcement(text):
    # 1. 检测上下文
    context_year, province_code = detect_context(text)
    
    # 2. 分句 (按句号、分号、换行符等分割)
    # 使用正则分割，保留分割符以便调试（可选，这里直接丢弃）
    # 增加对 "一、" "（一）" "1." 等列表项的分割支持，或者简单点，只按标点
    # 注意：fetch_content 已经把 \n 变成了空格，所以这里不需要 split \n
    # 我们可以把 text 切割成较短的片段，或者按句子
    
    # 这里的正则：匹配 。 ； ！ ？ 以及可能的列表序号 (如 "1. " "（1）")
    # 为了避免把日期中的点号（2026.1.1）误判为句号，我们只匹配 "全角句号" 或 "分号"
    lines = re.split(r'[。；;！!？?]', text)
    
    # 过滤空行
    lines = [line.strip() for line in lines if line.strip()]
    
    result = {}
    
    # 遍历所有配置的字段
    for field, keywords in KEYWORD_MAPPING.items():
        field_dates = []
        
        # 在文本中查找包含关键词的行（或句子）
        for line in lines:
            # 简单的关键词匹配
            if any(kw in line for kw in keywords):
                # 特殊过滤：如果找缴费时间，但行里有"准考证"，跳过
                if field == "payment_end" and "准考证" in line:
                    continue
                
                # 特殊过滤：如果找笔试时间，但行里有"成绩"、"查询"，跳过 (避免匹配到成绩查询时间)
                # 优化：只过滤明确的成绩查询相关表述，避免误杀包含"查询准考证"或"查询地点"的行
                if field == "exam_date" and ("查询成绩" in line or "成绩查询" in line or "公布成绩" in line or "成绩公布" in line):
                    continue
                    
                # 提取该行中的日期
                extracted = extract_dates(line, context_year)
                if extracted:
                    field_dates.extend(extracted)
                    # Debug
                    print(f"[Debug] {field} 匹配行: {line.strip()[:30]}... -> 提取日期: {extracted}")
        
        if field_dates:
            field_dates.sort()
            # 策略调整：
            # end 类型取最后一个
            # exam_date, score_date 通常比较靠后，也取最后一个，避免取到公告发布日期
            if "end" in field or field in ["exam_date", "score_date"]:
                result[field] = field_dates[-1]
            else:
                # start 类型取第一个
                result[field] = field_dates[0]
                
    # 简单的逻辑校验
    # 1. 考试时间不应早于报名开始时间
    if "exam_date" in result and "signup_start" in result:
        if result["exam_date"] < result["signup_start"]:
            print(f"[Warn] 考试时间 {result['exam_date']} 早于报名时间，疑似提取错误，已移除")
            del result["exam_date"]
            
    # 2. 面试时间不应早于考试时间 (如果考试时间存在)
    if "interview_date_start" in result:
        ref_date = result.get("exam_date") or result.get("signup_end")
        if ref_date and result["interview_date_start"] < ref_date:
             print(f"[Warn] 面试时间 {result['interview_date_start']} 早于 {ref_date}，疑似提取错误，已移除")
             del result["interview_date_start"]
             
    return result, province_code, context_year

def generate_sql(data, province_code, year):
    if not data:
        return "-- 未提取到任何时间信息"
        
    # 补充必要字段
    data["province_code"] = province_code
    data["year"] = year
    data["category"] = "公务员"
    
    columns = ", ".join(data.keys())
    values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in data.values()])
    
    sql = f"INSERT INTO public.exam_timelines ({columns}) VALUES ({values});"
    return sql

def upload_to_supabase(data, province_code, year):
    if not data:
        print("没有数据需要上传。")
        return

    print("正在连接 Supabase (via REST API)...")
    try:
        # 补充必要字段
        payload = data.copy()
        payload["province_code"] = province_code
        payload["year"] = year
        payload["category"] = "公务员"

        # 构造 API URL
        api_url = f"{SUPABASE_URL}/rest/v1/exam_timelines"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        # 先检查是否已存在相同省份年份的数据，如果存在则更新，否则插入
        # 这里为了简单，直接尝试插入，如果你的表设置了唯一约束可能会报错
        # 或者我们可以先查询一下
        
        print(f"正在上传数据: {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code >= 400:
            print(f"上传失败 (HTTP {response.status_code}): {response.text}")
        else:
            print("上传成功！")
            
    except Exception as e:
        print(f"上传过程中发生错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # 交互式输入模式，方便用户粘贴包含特殊字符（如 &）的 URL
        print("请输入公告 URL (按 Enter 确认):")
        try:
            url = input().strip()
        except KeyboardInterrupt:
            sys.exit(0)
            
        if not url:
            print("未提供 URL，退出。")
            sys.exit(1)

    # 简单清洗 URL (去除两端引号，以防用户在 PowerShell 中传递了带引号的字符串)
    url = url.strip("'\"")

    text_content = fetch_content(url)
    if text_content:
        # Debug: 打印前 500 个字符看看抓取到了什么
        print(f"--- 抓取内容预览 (前2000字符) ---\n{text_content[:2000]}\n-------------------------------")
        
        timeline_data, province_code, year = parse_announcement(text_content)
        print("\n=== 提取结果 ===")
        print(json.dumps(timeline_data, indent=2, ensure_ascii=False))
        
        # print("\n=== SQL 语句 ===")
        # print(generate_sql(timeline_data, province_code, year))
        
        if timeline_data:
            upload_to_supabase(timeline_data, province_code, year)
        else:
            print("未提取到有效的时间线数据，跳过上传。")
