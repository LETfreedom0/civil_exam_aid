from openpyxl import Workbook

wb = Workbook()
ws = wb.active

# 表头
headers = ["部门名称", "职位名称", "职位简介", "其他条件", "招考人数", "学历", "专业"]
ws.append(headers)

# 数据
data = [
    ["税务局", "行政助理", "处理日常行政事务", "无", 1, "本科", "管理学"],
    ["残联", "专门岗位", "面向残疾人招录", "限残疾人报考，需持有残疾证", 2, "大专", "不限"],
    ["海关", "监管", "货物监管", "英语六级", 5, "硕士", "法学"]
]

for row in data:
    ws.append(row)

wb.save("scripts/positions.xlsx")
print("Created scripts/positions.xlsx using openpyxl")
