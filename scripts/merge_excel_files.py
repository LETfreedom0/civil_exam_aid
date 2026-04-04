import os
import openpyxl
from openpyxl.utils import get_column_letter

def merge_excel_files(source_dir, output_file):
    print(f"源目录: {source_dir}")
    print(f"输出文件: {output_file}")

    if not os.path.exists(source_dir):
        print("错误: 源目录不存在")
        return

    # 获取所有 .xlsx 文件
    xlsx_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.xlsx') and not f.startswith('~$')]
    
    if not xlsx_files:
        print("未找到 .xlsx 文件")
        return

    print(f"找到 {len(xlsx_files)} 个文件，准备合并...")

    # 创建新的工作簿
    merged_wb = openpyxl.Workbook()
    merged_ws = merged_wb.active
    merged_ws.title = "合并职位表"

    # 配置
    HEADER_ROW = 3    # 表头所在行
    DATA_START_ROW = 4 # 数据开始行
    
    header_written = False
    total_rows = 0

    for filename in xlsx_files:
        file_path = os.path.join(source_dir, filename)
        print(f"正在处理: {filename} ...")

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            ws = wb.active

            # 写入表头 (只写一次)
            if not header_written:
                header_values = []
                # 获取表头行数据
                for col in range(1, ws.max_column + 1):
                    cell_value = ws.cell(row=HEADER_ROW, column=col).value
                    # 清理换行符和多余空格
                    if isinstance(cell_value, str):
                        cell_value = cell_value.replace('\n', '').replace(' ', '')
                    header_values.append(cell_value)
                
                # 添加来源列
                header_values.append("来源文件")
                merged_ws.append(header_values)
                header_written = True

            # 写入数据行
            file_rows = 0
            for row in range(DATA_START_ROW, ws.max_row + 1):
                row_values = []
                has_data = False
                
                # 读取该行每一列的数据
                for col in range(1, ws.max_column + 1):
                    cell_value = ws.cell(row=row, column=col).value
                    row_values.append(cell_value)
                    if cell_value is not None:
                        has_data = True
                
                # 只有当该行有数据时才写入
                if has_data:
                    # 添加来源文件名（去除扩展名）
                    source_name = os.path.splitext(filename)[0]
                    row_values.append(source_name)
                    
                    merged_ws.append(row_values)
                    file_rows += 1
                    total_rows += 1
            
            print(f"  -> 已添加 {file_rows} 行数据")
            wb.close()

        except Exception as e:
            print(f"处理 {filename} 时出错: {e}")

    # 保存合并后的文件
    try:
        merged_wb.save(output_file)
        print("-" * 30)
        print(f"合并完成！总共合并了 {total_rows} 行数据。")
        print(f"文件已保存至: {output_file}")
    except Exception as e:
        print(f"保存文件失败: {e}")

if __name__ == "__main__":
    target_dir = r"C:\Users\Administrator\Downloads\浙江2026省考"
    output_path = os.path.join(target_dir, "浙江2026年度考试录用公务员各地职位表_合并版.xlsx")
    
    merge_excel_files(target_dir, output_path)
