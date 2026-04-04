import os
import requests
import json

# Supabase 配置
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hubbzosfrhxnzwuiitcv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Fj0j0VPlvGuLLxhjcGMIWA_8KL4DAWV")

def check_data():
    print("正在连接 Supabase...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "count=exact"
    }
    
    # 1. 查询总数据量
    url = f"{SUPABASE_URL}/rest/v1/positions?select=count"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content_range = resp.headers.get("Content-Range")
            total = content_range.split('/')[-1] if content_range else "Unknown"
            print(f"总数据量: {total}")
        else:
            print(f"查询总数失败: {resp.text}")
    except Exception as e:
        print(f"错误: {e}")

    # 2. 查询 exam_region 包含 '四川' 的数据量
    url = f"{SUPABASE_URL}/rest/v1/positions?exam_region=ilike.*四川*&select=count"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content_range = resp.headers.get("Content-Range")
            total = content_range.split('/')[-1] if content_range else "Unknown"
            print(f"exam_region 包含 '四川' 的数据量: {total}")
        else:
            print(f"查询四川失败: {resp.text}")
    except Exception as e:
        print(f"错误: {e}")

    # 3. 查询 province_code 为 510000 的数据量
    url = f"{SUPABASE_URL}/rest/v1/positions?province_code=eq.510000&select=count"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            content_range = resp.headers.get("Content-Range")
            total = content_range.split('/')[-1] if content_range else "Unknown"
            print(f"province_code=510000 的数据量: {total}")
        else:
            print(f"查询 510000 失败: {resp.text}")
    except Exception as e:
        print(f"错误: {e}")

    # 4. 获取几条数据样本看看
    url = f"{SUPABASE_URL}/rest/v1/positions?exam_region=ilike.*四川*&limit=5&select=*"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n数据样本 ({len(data)} 条):")
            for item in data:
                print(f"ID: {item.get('id')}, Province: {item.get('province_code')}, Year: {item.get('year')}, Name: {item.get('position_name')}, Unit: {item.get('recruit_unit')}")
        else:
            print(f"查询样本失败: {resp.text}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_data()
