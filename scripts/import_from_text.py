import os
import requests
import json
import sys

# ================= 配置区域 =================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hubbzosfrhxnzwuiitcv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Fj0j0VPlvGuLLxhjcGMIWA_8KL4DAWV")

# 固定值
YEAR = 2026
PROVINCE_CODE = "360000"  # 江西省
POSITION_ORIGIN = 0  # 省考

# 文本数据（直接粘贴在这里）
TEXT_DATA = """
会昌县残疾人联合会,赣州,县（市，区）直,01 综合管理岗,参照管理群团机关,一级科员,会昌县,A类（县乡综合管理）,1,全国,38周岁及以下（博士研究生43周岁以下）,不限,不限,不限,不限,本科及以上,不限,不限,专门职位（残疾人）,不限,从事综合管理、残疾人服务协调等工作，限持二代残疾人证（四级肢体/听力/视力残疾）报考,0797-5637175
德安县残疾人联合会,九江,县（市，区）直,01 综合管理岗,参照管理群团机关,一级科员,德安县,A类（县乡综合管理）,1,全国,38周岁及以下（博士研究生43周岁以下）,不限,不限,不限,不限,本科及以上,学士及以上学位,不限,专门职位（残疾人）,文学类,从事办公室业务等工作，限2026届普通高校毕业生报考,0792-4332035
赣州市残疾人联合会,赣州,市直,01 残疾人服务岗,参照管理人民团体和群众团体,一级科员,赣州市直,A类（省市综合管理）,1,全国,38周岁及以下,不限,不限,不限,不限,本科及以上,学士及以上学位,不限,专门职位（残疾人）,不限,从事残疾人康复、组织联络及权益保障相关工作，需持有二代残疾人证,0797-8992418
宜春市残疾人联合会,宜春,市直,01 综合服务岗,参照管理人民团体和群众团体,一级科员,宜春市直,A类（省市综合管理）,1,全国,38周岁及以下,不限,不限,不限,不限,本科及以上,学士及以上学位,不限,专门职位（残疾人）,公共管理类,从事残疾人服务、政策落实及综合协调工作，不设开考比例,0795-3199856
"""

# 字段映射：CSV列索引 -> 数据库字段
FIELD_MAPPING = {
    0: "recruit_unit",        # 单位
    1: "exam_region",         # 单位所属地区
    2: "unit_level",          # 单位层级
    3: "position_name",       # 职位
    4: "position_type",       # 单位所属系统
    5: "rank_level",          # 职级
    6: "city",                # 工作地点
    7: "exam_subjects",       # 考试类型
    8: "quota",               # 招录人数
    9: "domicile",            # 招生范围
    10: "max_age",            # 年龄要求
    11: "gender",             # 性别要求
    12: "candidate_identity", # 民族要求
    13: "political_status",   # 政治面貌要求
    14: "education",          # 学历类别要求
    15: "education",           # 学历要求
    16: "degree",             # 学位要求
    17: "grassroots_exp",     # 工作经历要求
    18: "fresh_grad",         # 专门职位
    19: "major",              # 所需专业
    20: "description",        # 职位简介
    21: "phone1",             # 联系方式
}

def parse_text_data(text):
    """解析文本数据"""
    positions = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 按逗号分割
        fields = line.split(',')
        
        if len(fields) < 10:
            print(f"跳过无效行: {line[:50]}...")
            continue
        
        item = {
            "year": YEAR,
            "province_code": PROVINCE_CODE,
            "position_origin": POSITION_ORIGIN,
        }
        
        # 映射字段
        for idx, db_field in FIELD_MAPPING.items():
            if idx < len(fields):
                value = fields[idx].strip()
                if value and value != "不限":
                    if db_field == "quota":
                        try:
                            item[db_field] = int(value)
                        except:
                            item[db_field] = 0
                    else:
                        item[db_field] = value
                elif db_field not in item:
                    item[db_field] = value
        
        positions.append(item)
    
    return positions

def upload_to_supabase(data):
    """上传到Supabase"""
    if not data:
        print("没有数据需要上传")
        return
    
    print(f"共解析出 {len(data)} 条职位数据")
    
    # 打印预览
    print("\n数据预览 (前2条):")
    for i, item in enumerate(data[:2]):
        print(f"\n--- 第{i+1}条 ---")
        print(f"职位: {item.get('position_name')}")
        print(f"单位: {item.get('recruit_unit')}")
        print(f"地区: {item.get('exam_region')}")
        print(f"招录人数: {item.get('quota')}")
    
    api_url = f"{SUPABASE_URL}/rest/v1/positions"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # 批量插入
    batch_size = 100
    total = len(data)
    inserted = 0
    
    for i in range(0, total, batch_size):
        batch = data[i:i+batch_size]
        print(f"\n正在插入第 {i+1} - {min(i+batch_size, total)} 条...")
        
        try:
            response = requests.post(api_url, headers=headers, json=batch)
            if response.status_code < 400:
                inserted += len(batch)
                print(f"成功插入 {len(batch)} 条")
            else:
                print(f"插入失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"插入异常: {e}")
    
    print(f"\n========== 完成 ==========")
    print(f"共插入 {inserted} 条记录")

def main():
    print("========== 文本数据导入 ==========")
    print(f"年份: {YEAR}")
    print(f"省份: {PROVINCE_CODE}")
    
    # 解析数据
    positions = parse_text_data(TEXT_DATA)
    
    if positions:
        # 确认导入
        print(f"\n解析完成，共 {len(positions)} 条数据")
        confirm = input("确认导入到数据库? (y/n): ")
        if confirm.lower() == 'y':
            upload_to_supabase(positions)
        else:
            print("已取消导入")
    else:
        print("未解析到有效数据")

if __name__ == "__main__":
    main()
