import os
import subprocess
import sys
import streamlit as st
import importlib
import json
import requests

timeline = importlib.import_module("scrape_exam_timeline")
positions = importlib.import_module("import_positions")
htmlpos = importlib.import_module("scrape_html_positions")


def list_scripts(base_dir: str) -> list[str]:
    """
    列出可运行的脚本文件（排除当前 app.py）
    :param base_dir: 搜索脚本的目录路径
    :return: 脚本文件名列表
    """
    scripts = []
    for name in os.listdir(base_dir):
        if name.endswith(".py") and name != "app.py":
            scripts.append(name)
    return sorted(scripts)


def run_script(script_path: str) -> tuple[int, str, str]:
    """
    在独立进程中运行指定的 Python 脚本
    :param script_path: 脚本的绝对路径
    :return: (退出码, 标准输出, 标准错误)
    """
    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=os.path.dirname(script_path),
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return 1, "", f"执行异常: {e}"


def scripts_page(base_dir: str) -> None:
    """
    脚本管理页面：列出脚本、选择并运行，显示运行结果
    """
    st.title("Civil Exam Aid · 脚本管理")
    st.caption("在左侧选择脚本并执行，便于快速调试与管理")
    scripts = list_scripts(base_dir)
    with st.sidebar:
        st.header("脚本选择")
        selected = st.selectbox("选择一个脚本运行", options=scripts)
        st.write(f"工作目录：{base_dir}")
        if st.button("运行所选脚本"):
            if selected:
                code, out, err = run_script(os.path.join(base_dir, selected))
                st.session_state["last_run"] = {
                    "script": selected,
                    "code": code,
                    "out": out,
                    "err": err,
                }
            else:
                st.warning("请先选择脚本")
    st.subheader("脚本列表")
    if scripts:
        st.dataframe({"脚本文件": scripts})
    else:
        st.info("当前目录未找到可运行脚本")
    st.subheader("最近一次运行结果")
    last = st.session_state.get("last_run")
    if last:
        st.write(f"脚本：{last['script']} | 退出码：{last['code']}")
        if last["out"]:
            st.success("标准输出：")
            st.code(last["out"], language="bash")
        if last["err"]:
            st.error("标准错误：")
            st.code(last["err"], language="bash")
    else:
        st.caption("暂无运行记录")


def db_admin_page(base_dir: str) -> None:
    """
    数据库管理页面：通过 Supabase REST 对数据进行增删改查
    - 支持表选择：positions / exam_timelines
    - 查询：支持按省份代码与年份过滤并展示数据
    - 更新：在查询结果中编辑以更新所有字段，按唯一键/组合键或 id 提交
    - 删除：按唯一键/组合键或 id 删除
    依赖环境变量 SUPABASE_URL、SUPABASE_KEY（可在其他配置页保存注入）
    """
    st.title("数据库 CRUD 管理")
    base_url = os.environ.get("SUPABASE_URL", "")
    api_key = os.environ.get("SUPABASE_KEY", "")
    with st.expander("Supabase 设置", expanded=not (base_url and api_key)):
        base_url = st.text_input("SUPABASE_URL", value=base_url)
        api_key = st.text_input("SUPABASE_KEY", value=api_key, type="password")
        if st.button("更新至会话环境"):
            os.environ["SUPABASE_URL"] = base_url
            os.environ["SUPABASE_KEY"] = api_key
            st.success("已更新环境变量")
    if not base_url or not api_key:
        st.warning("请先设置 SUPABASE_URL 与 SUPABASE_KEY")
        return

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    table = st.sidebar.selectbox("选择数据表", options=["positions", "exam_timelines"])
    st.caption(f"当前操作表：{table}")
    rest_url = f"{base_url}/rest/v1/{table}"

    # 查询区域
    st.subheader("查询")
    q = st.text_input("关键词")
    provinces = [
        ("北京市", "110000"), ("天津市", "120000"), ("河北省", "130000"), ("山西省", "140000"), ("内蒙古自治区", "150000"),
        ("辽宁省", "210000"), ("吉林省", "220000"), ("黑龙江省", "230000"), ("上海市", "310000"), ("江苏省", "320000"),
        ("浙江省", "330000"), ("安徽省", "340000"), ("福建省", "350000"), ("江西省", "360000"), ("山东省", "370000"),
        ("河南省", "410000"), ("湖北省", "420000"), ("湖南省", "430000"), ("广东省", "440000"), ("广西壮族自治区", "450000"),
        ("海南省", "460000"), ("重庆市", "500000"), ("四川省", "510000"), ("贵州省", "520000"), ("云南省", "530000"),
        ("西藏自治区", "540000"), ("陕西省", "610000"), ("甘肃省", "620000"), ("青海省", "630000"), ("宁夏回族自治区", "640000"),
        ("新疆维吾尔自治区", "650000"),
    ]
    prov_names = [p[0] for p in provinces]
    prov_codes = {p[0]: p[1] for p in provinces}
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        selected_prov = st.selectbox("省份代码过滤", options=["不限"] + prov_names, index=0)
    with col_b:
        year_filter = st.number_input("年份过滤", min_value=0, max_value=2100, value=0, help="0 表示不限")
    with col_c:
        limit = st.number_input("返回条数限制", min_value=1, max_value=1000, value=100)
    
    # 查询按钮
    if 'db_query_key' not in st.session_state:
        st.session_state.db_query_key = 0
    
    query_clicked = st.button("查询数据", key="query_btn")
    
    # 初始化数据
    if 'db_original_rows' not in st.session_state:
        st.session_state.db_original_rows = []
    if 'db_edited_rows' not in st.session_state:
        st.session_state.db_edited_rows = []
    
    # 查询或页面加载时获取数据
    if query_clicked or (not st.session_state.db_original_rows and st.session_state.get('db_current_table') == table):
        params = {"select": "*", "limit": limit}
        if q:
            params["description" if table == "positions" else "category"] = f"ilike.*{q}*"
        if selected_prov != "不限":
            params["province_code"] = f"eq.{prov_codes.get(selected_prov, '')}"
        if year_filter and table in ("positions", "exam_timelines"):
            params["year"] = f"eq.{int(year_filter)}"
        
        resp = requests.get(rest_url, headers=headers, params=params)
        data = resp.json() if resp.status_code < 400 else []
        rows = data if isinstance(data, list) else [data]
        
        # 保存原始数据（深拷贝）
        import copy
        st.session_state.db_original_rows = copy.deepcopy(rows)
        st.session_state.db_edited_rows = copy.deepcopy(rows)
        st.session_state.db_current_table = table
    
    # 显示编辑表格
    if st.session_state.db_edited_rows:
        st.caption(f"共 {len(st.session_state.db_edited_rows)} 条数据，请编辑后点击'保存修改'")
        
        # 使用 session_state 存储编辑后的数据
        edited_result = st.data_editor(
            st.session_state.db_edited_rows, 
            width="stretch", 
            key=f"data_editor_{table}"
        )
        
        # 检查数据是否有变化
        import copy
        st.session_state.db_edited_rows = copy.deepcopy(edited_result)
    else:
        st.info("点击'查询数据'按钮获取数据")
    
    # 保存修改按钮
    st.subheader("保存修改")
    if st.button("保存修改", key="save_btn"):
        if not st.session_state.db_original_rows or not st.session_state.db_edited_rows:
            st.warning("没有数据可保存")
        else:
            changed = 0
            if table == "positions":
                # 使用 position_name + recruit_unit + province_code + year 作为唯一键
                for i, (orig, edited) in enumerate(zip(st.session_state.db_original_rows, st.session_state.db_edited_rows)):
                    # 构建唯一键
                    pn = orig.get("position_name") or ""
                    ru = orig.get("recruit_unit") or ""
                    pv = orig.get("province_code") or ""
                    yr = str(orig.get("year")) or ""
                    
                    if not pn:
                        continue
                    
                    # 检查是否有变化
                    payload = {k: v for k, v in edited.items() if orig.get(k) != v}
                    if payload:
                        update_url = f"{rest_url}?position_name=eq.{pn}&recruit_unit=eq.{ru}&province_code=eq.{pv}&year=eq.{yr}"
                        res = requests.patch(update_url, headers=headers, json=payload)
                        if res.status_code < 300:
                            changed += 1
            else:
                for i, (orig, edited) in enumerate(zip(st.session_state.db_original_rows, st.session_state.db_edited_rows)):
                    params_upd = None
                    if orig.get("id") is not None:
                        params_upd = {"id": f"eq.{orig.get('id')}"}
                    else:
                        comp = f"{orig.get('year')}|{orig.get('province_code')}|{orig.get('category')}"
                        if comp:
                            params_upd = {
                                "year": f"eq.{orig.get('year')}",
                                "province_code": f"eq.{orig.get('province_code')}",
                                "category": f"eq.{orig.get('category')}",
                            }
                    
                    if not params_upd:
                        continue
                    
                    payload = {k: v for k, v in edited.items() if orig.get(k) != v}
                    if payload:
                        res = requests.patch(rest_url, headers=headers, json=payload, params=params_upd)
                        if res.status_code < 300:
                            changed += 1
            
            if changed > 0:
                st.success(f"已更新 {changed} 条记录")
                # 刷新数据
                st.session_state.db_original_rows = copy.deepcopy(st.session_state.db_edited_rows)
            else:
                st.info("没有检测到需要更新的改动")


    # 删除
    st.subheader("删除记录")
    del_id = st.text_input("按 id 删除（优先）")
    if st.button(f"按 id 删除 {table}"):
        if del_id:
            r = requests.delete(rest_url, headers=headers, params={"id": f"eq.{del_id}"})
            if r.status_code < 300:
                st.success("删除成功")
            else:
                st.error(f"删除失败: {r.status_code} {r.text}")
        else:
            st.warning("请填写 id 后再删除")
    del_prov = st.text_input("按省份代码删除（将删除该省份的所有记录）")
    if st.button(f"按省份代码删除 {table}"):
        if del_prov:
            r = requests.delete(rest_url, headers=headers, params={"province_code": f"eq.{del_prov}"})
            if r.status_code < 300:
                st.success("删除成功")
            else:
                st.error(f"删除失败: {r.status_code} {r.text}")
        else:
            st.warning("请填写省份代码后再删除")


def positions_config_page(base_dir: str) -> None:
    """
    职位导入配置页面：编辑并保存 import_positions.py 的配置项
    """
    st.title("职位导入配置")
    cfg_path = os.path.join(base_dir, "import_positions.config.json")
    default_cfg = {
        "SUPABASE_URL": os.environ.get("SUPABASE_URL", getattr(positions, "SUPABASE_URL", "")),
        "SUPABASE_KEY": os.environ.get("SUPABASE_KEY", getattr(positions, "SUPABASE_KEY", "")),
        "EXCEL_URL": getattr(positions, "EXCEL_URL", ""),
        "LOCAL_FILE_PATH": getattr(positions, "LOCAL_FILE_PATH", ""),
        "FILTER_KEYWORDS": getattr(positions, "FILTER_KEYWORDS", []),
        "CHECK_COLUMNS": getattr(positions, "CHECK_COLUMNS", []),
        "HEADER_ROW": getattr(positions, "HEADER_ROW", 3),
        "HEADER_HEIGHT": getattr(positions, "HEADER_HEIGHT", 2),
        "DATA_START_ROW": getattr(positions, "DATA_START_ROW", 5),
        "COLUMN_MAPPING": getattr(positions, "COLUMN_MAPPING", {}),
        "DEFAULT_VALUES": getattr(positions, "DEFAULT_VALUES", {"year": 2026, "province_code": ""}),
    }
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
                default_cfg.update(file_cfg)
        except Exception:
            pass
    with st.form("positions_config_form"):
        st.subheader("Supabase")
        supabase_url = st.text_input("SUPABASE_URL", value=default_cfg.get("SUPABASE_URL", ""))
        supabase_key = st.text_input("SUPABASE_KEY", value=default_cfg.get("SUPABASE_KEY", ""), type="password")
        st.subheader("Excel来源")
        excel_url = st.text_input("EXCEL_URL（留空仅处理本地文件）", value=default_cfg.get("EXCEL_URL", ""))
        local_file = st.text_input("LOCAL_FILE_PATH", value=default_cfg.get("LOCAL_FILE_PATH", ""))
        st.caption("建议填写绝对路径；也可在“保存并运行”时通过命令行参数传入该路径")
        st.subheader("筛选关键词与检查列")
        keywords_text = st.text_area("FILTER_KEYWORDS（逗号或换行分隔）", value="\n".join(default_cfg.get("FILTER_KEYWORDS", [])))
        checkcols_text = st.text_area("CHECK_COLUMNS（逗号或换行分隔）", value="\n".join(default_cfg.get("CHECK_COLUMNS", [])))
        st.subheader("表头与数据行")
        header_row = st.number_input("HEADER_ROW（表头起始行）", min_value=1, value=int(default_cfg.get("HEADER_ROW", 3)))
        header_height = st.number_input("HEADER_HEIGHT（表头行数）", min_value=1, value=int(default_cfg.get("HEADER_HEIGHT", 2)))
        data_start_row = st.number_input("DATA_START_ROW（数据起始行）", min_value=1, value=int(default_cfg.get("DATA_START_ROW", 5)))
        st.subheader("列名映射（每行逗号分隔多个匹配名）")
        mapping_rows = [{"字段": k, "匹配列名": ", ".join(v)} for k, v in default_cfg.get("COLUMN_MAPPING", {}).items()]
        edited_rows = st.data_editor(mapping_rows, num_rows="dynamic", key="mapping_editor")
        st.subheader("默认值")
        year = st.number_input("DEFAULT_VALUES.year", min_value=1900, max_value=2100, value=int(default_cfg.get("DEFAULT_VALUES", {}).get("year", 2026)))
        provinces = [
            ("北京市", "110000"),
            ("天津市", "120000"),
            ("河北省", "130000"),
            ("山西省", "140000"),
            ("内蒙古自治区", "150000"),
            ("辽宁省", "210000"),
            ("吉林省", "220000"),
            ("黑龙江省", "230000"),
            ("上海市", "310000"),
            ("江苏省", "320000"),
            ("浙江省", "330000"),
            ("安徽省", "340000"),
            ("福建省", "350000"),
            ("江西省", "360000"),
            ("山东省", "370000"),
            ("河南省", "410000"),
            ("湖北省", "420000"),
            ("湖南省", "430000"),
            ("广东省", "440000"),
            ("广西壮族自治区", "450000"),
            ("海南省", "460000"),
            ("重庆市", "500000"),
            ("四川省", "510000"),
            ("贵州省", "520000"),
            ("云南省", "530000"),
            ("西藏自治区", "540000"),
            ("陕西省", "610000"),
            ("甘肃省", "620000"),
            ("青海省", "630000"),
            ("宁夏回族自治区", "640000"),
            ("新疆维吾尔自治区", "650000"),
        ]
        prov_names = [p[0] for p in provinces]
        prov_codes = {p[0]: p[1] for p in provinces}
        current_code = default_cfg.get("DEFAULT_VALUES", {}).get("province_code", "")
        current_index = 0
        if current_code:
            for i, (_, code) in enumerate(provinces):
                if code == current_code:
                    current_index = i
                    break
        selected_prov = st.selectbox("DEFAULT_VALUES.province_code", options=prov_names, index=current_index)
        col1, col2 = st.columns(2)
        with col1:
            save_btn = st.form_submit_button("保存配置")
        with col2:
            run_btn = st.form_submit_button("保存并运行")
    if save_btn or run_btn:
        new_mapping = {}
        for row in edited_rows:
            key = str(row.get("字段", "")).strip()
            vals = []
            raw = str(row.get("匹配列名", "") or "")
            for part in raw.replace("\n", ",").split(","):
                s = part.strip()
                if s:
                    vals.append(s)
            if key:
                new_mapping[key] = vals
        cfg = {
            "SUPABASE_URL": supabase_url.strip(),
            "SUPABASE_KEY": supabase_key.strip(),
            "EXCEL_URL": excel_url.strip(),
            "LOCAL_FILE_PATH": local_file.strip(),
            "FILTER_KEYWORDS": [s.strip() for s in keywords_text.replace("\r", "").replace("，", ",").splitlines() if s.strip()] if "\n" in keywords_text else [s.strip() for s in keywords_text.replace("，", ",").split(",") if s.strip()],
            "CHECK_COLUMNS": [s.strip() for s in checkcols_text.replace("\r", "").replace("，", ",").splitlines() if s.strip()] if "\n" in checkcols_text else [s.strip() for s in checkcols_text.replace("，", ",").split(",") if s.strip()],
            "HEADER_ROW": int(header_row),
            "HEADER_HEIGHT": int(header_height),
            "DATA_START_ROW": int(data_start_row),
            "COLUMN_MAPPING": new_mapping,
            "DEFAULT_VALUES": {"year": int(year), "province_code": prov_codes.get(selected_prov, "")},
        }
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            os.environ["SUPABASE_URL"] = cfg["SUPABASE_URL"]
            os.environ["SUPABASE_KEY"] = cfg["SUPABASE_KEY"]
            st.success("配置已保存")
        except Exception as e:
            st.error(f"保存失败：{e}")
        if run_btn:
            st.subheader("运行结果")
            code = run_import_positions_streaming(os.path.join(base_dir, "import_positions.py"), cfg.get("LOCAL_FILE_PATH"))
            st.write(f"退出码：{code}")

def run_import_positions(script_path: str, file_path: str | None) -> tuple[int, str, str]:
    """
    运行职位导入脚本，可选传入本地 Excel 文件路径
    """
    try:
        args = [sys.executable, script_path]
        if file_path:
            args.append(file_path)
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=os.path.dirname(script_path),
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return 1, "", f"执行异常: {e}"

def run_import_positions_streaming(script_path: str, file_path: str | None) -> int:
    """
    以流式方式运行职位导入脚本，将日志实时输出到页面
    修复：完整显示多sheet导入的所有日志
    """
    import subprocess as sp
    import threading
    import queue
    import os
    try:
        args = [sys.executable, script_path]
        if file_path:
            args.append(file_path)
        
        # 创建队列用于线程间通信
        log_queue = queue.Queue()
        
        # 启动子进程
        proc = sp.Popen(
            args,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            cwd=os.path.dirname(script_path),
        )
        
        # 使用文本模式包装，处理多种编码
        import io
        import codecs
        
        # 设置子进程环境变量确保输出 UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # 重新启动子进程
        proc = sp.Popen(
            args,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            cwd=os.path.dirname(script_path),
            env=env,
        )
        
        # 使用 UTF-8 包装
        proc.stdout = io.TextIOWrapper(proc.stdout, encoding='utf-8', errors='replace')
        proc.stderr = io.TextIOWrapper(proc.stderr, encoding='utf-8', errors='replace')
        
        # 创建日志容器
        log_area = st.empty()
        all_logs = []
        
        # 后台线程读取输出
        def read_output(pipe, queue_obj, is_error=False):
            try:
                for line in pipe:
                    clean_line = line.strip()
                    if clean_line:
                        queue_obj.put((is_error, clean_line))
                queue_obj.put((is_error, None))  # 结束标记
            except Exception as e:
                queue_obj.put((is_error, f"Read error: {str(e)}"))
        
        # 启动读取线程
        out_thread = threading.Thread(target=read_output, args=(proc.stdout, log_queue, False))
        err_thread = threading.Thread(target=read_output, args=(proc.stderr, log_queue, True))
        out_thread.daemon = True
        err_thread.daemon = True
        out_thread.start()
        err_thread.start()
        
        # 主循环：收集日志并显示
        finished_count = 0
        while finished_count < 2:
            try:
                is_error, content = log_queue.get(timeout=0.1)
                if content is None:  # 结束标记
                    finished_count += 1
                    continue
                
                # 添加到日志列表
                prefix = "[ERROR]" if is_error else "[INFO]"
                all_logs.append(f"{prefix} {content}")
                
                # 显示所有日志（保留完整历史）
                log_area.code("\n".join(all_logs), language="bash")
                
            except queue.Empty:
                # 检查进程是否结束
                if proc.poll() is not None:
                    break
        
        # 等待线程结束
        out_thread.join(timeout=1)
        err_thread.join(timeout=1)
        
        return proc.returncode
        
    except Exception as e:
        st.error(f"执行异常: {e}")
        return 1


def html_positions_config_page(base_dir: str) -> None:
    """
    Web position scraping config page: edit and save scrape_html_positions.py parameters
    """
    st.title("网页职位抓取配置")
    cfg_path = os.path.join(base_dir, "scrape_html_positions.config.json")
    default_cfg = {
        "HTML_URL": getattr(htmlpos, "HTML_URL", ""),
        "SUPABASE_URL": os.environ.get("SUPABASE_URL", getattr(htmlpos, "SUPABASE_URL", "")),
        "SUPABASE_KEY": os.environ.get("SUPABASE_KEY", getattr(htmlpos, "SUPABASE_KEY", "")),
        "DEFAULT_YEAR": getattr(htmlpos, "DEFAULT_YEAR", 2026),
        "DEFAULT_PROVINCE_CODE": getattr(htmlpos, "DEFAULT_PROVINCE_CODE", ""),
        "FILTER_KEYWORDS": getattr(htmlpos, "FILTER_KEYWORDS", []),
        "COL_MAP": getattr(htmlpos, "COL_MAP", {}),
    }
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
                default_cfg.update(file_cfg)
                # 特殊处理：如果 COL_MAP 为空，尝试回退到脚本默认值
                if not default_cfg.get("COL_MAP") and getattr(htmlpos, "COL_MAP", {}):
                    default_cfg["COL_MAP"] = getattr(htmlpos, "COL_MAP", {})
        except Exception:
            pass
    with st.form("html_positions_config_form"):
        st.subheader("来源与目标")
        html_url = st.text_input("HTML_URL", value=default_cfg.get("HTML_URL", ""))
        supabase_url = st.text_input("SUPABASE_URL", value=default_cfg.get("SUPABASE_URL", ""))
        supabase_key = st.text_input("SUPABASE_KEY", value=default_cfg.get("SUPABASE_KEY", ""), type="password")
        st.subheader("默认值")
        year = st.number_input("DEFAULT_YEAR", min_value=1900, max_value=2100, value=int(default_cfg.get("DEFAULT_YEAR", 2026)))
        provinces = [
            ("北京市", "110000"), ("天津市", "120000"), ("河北省", "130000"), ("山西省", "140000"), ("内蒙古自治区", "150000"),
            ("辽宁省", "210000"), ("吉林省", "220000"), ("黑龙江省", "230000"), ("上海市", "310000"), ("江苏省", "320000"),
            ("浙江省", "330000"), ("安徽省", "340000"), ("福建省", "350000"), ("江西省", "360000"), ("山东省", "370000"),
            ("河南省", "410000"), ("湖北省", "420000"), ("湖南省", "430000"), ("广东省", "440000"), ("广西壮族自治区", "450000"),
            ("海南省", "460000"), ("重庆市", "500000"), ("四川省", "510000"), ("贵州省", "520000"), ("云南省", "530000"),
            ("西藏自治区", "540000"), ("陕西省", "610000"), ("甘肃省", "620000"), ("青海省", "630000"), ("宁夏回族自治区", "640000"),
            ("新疆维吾尔自治区", "650000"),
        ]
        prov_names = [p[0] for p in provinces]
        prov_codes = {p[0]: p[1] for p in provinces}
        current_code = default_cfg.get("DEFAULT_PROVINCE_CODE", "")
        current_index = 0
        if current_code:
            for i, (_, code) in enumerate(provinces):
                if code == current_code:
                    current_index = i
                    break
        selected_prov = st.selectbox("DEFAULT_PROVINCE_CODE", options=prov_names, index=current_index)
        st.subheader("筛选关键词")
        keywords_text = st.text_area("FILTER_KEYWORDS（逗号或换行分隔）", value="\n".join(default_cfg.get("FILTER_KEYWORDS", [])))
        st.subheader("列名映射（HTML表头 → 数据库字段）")
        mapping_rows = [{"HTML表头": k, "数据库字段": v} for k, v in default_cfg.get("COL_MAP", {}).items()]
        edited_rows = st.data_editor(mapping_rows, num_rows="dynamic", key="html_mapping_editor")
        col1, col2 = st.columns(2)
        with col1:
            save_btn = st.form_submit_button("保存配置")
        with col2:
            run_btn = st.form_submit_button("保存并运行")
    if save_btn or run_btn:
        new_map = {}
        for row in edited_rows:
            hk = str(row.get("HTML表头", "")).strip()
            db = str(row.get("数据库字段", "")).strip()
            if hk and db:
                new_map[hk] = db
        cfg = {
            "HTML_URL": html_url.strip(),
            "SUPABASE_URL": supabase_url.strip(),
            "SUPABASE_KEY": supabase_key.strip(),
            "DEFAULT_YEAR": int(year),
            "DEFAULT_PROVINCE_CODE": prov_codes.get(selected_prov, ""),
            "FILTER_KEYWORDS": [s.strip() for s in keywords_text.replace("\r", "").replace("，", ",").splitlines() if s.strip()] if "\n" in keywords_text else [s.strip() for s in keywords_text.replace("，", ",").split(",") if s.strip()],
            "COL_MAP": new_map,
        }
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            os.environ["SUPABASE_URL"] = cfg["SUPABASE_URL"]
            os.environ["SUPABASE_KEY"] = cfg["SUPABASE_KEY"]
            st.success("配置已保存")
        except Exception as e:
            st.error(f"保存失败：{e}")
        if run_btn:
            st.subheader("运行结果")
            code = run_import_positions_streaming(os.path.join(base_dir, "scrape_html_positions.py"), None)
            st.write(f"退出码：{code}")

def timeline_page() -> None:
    """
    时间线导入页面：输入公告 URL，提取时间点并上传至 Supabase
    """
    st.title("考试时间线导入")
    st.caption("支持解析网页与 .docx 公告，自动识别报名、考试等关键时间")
    url = st.text_input("公告 URL", placeholder="粘贴含报名/考试时间的公告链接")
    col1, col2 = st.columns(2)
    with col1:
        do_upload = st.checkbox("解析后上传到 Supabase", value=True)
    with col2:
        st.write("")
    supabase_url = st.text_input("Supabase URL", value=os.environ.get("SUPABASE_URL", ""), help="留空使用脚本默认值")
    supabase_key = st.text_input("Supabase API Key", value=os.environ.get("SUPABASE_KEY", ""), type="password", help="留空使用脚本默认值")
    if st.button("开始解析"):
        if not url:
            st.warning("请先填写公告 URL")
            return
        with st.spinner("正在抓取并解析内容..."):
            text = timeline.fetch_content(url)
        if not text:
            st.error("抓取失败，请确认链接可访问")
            return
        st.success("抓取成功，内容预览：")
        st.code(text[:2000])
        data, province_code, year = timeline.parse_announcement(text)
        if not data:
            st.warning("未提取到有效的时间线数据")
            return
        st.subheader("提取结果")
        st.json({"year": year, "province_code": province_code, **data})
        if do_upload:
            if supabase_url:
                os.environ["SUPABASE_URL"] = supabase_url
            if supabase_key:
                os.environ["SUPABASE_KEY"] = supabase_key
            with st.spinner("正在上传到 Supabase..."):
                timeline.upload_to_supabase(data, province_code, year)
            st.success("上传完成")
        else:
            st.info("已解析但未上传，可调整 Supabase 配置后再次上传")


def main() -> None:
    """
    应用入口：提供页面切换（脚本管理 / 时间线导入）
    """
    st.set_page_config(page_title="Civil Exam Aid 管理", layout="wide")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    page = st.sidebar.radio("选择页面", options=["脚本管理", "职位导入配置", "网页职位抓取配置", "时间线导入", "数据库管理"])
    if page == "脚本管理":
        scripts_page(base_dir)
    elif page == "职位导入配置":
        positions_config_page(base_dir)
    elif page == "网页职位抓取配置":
        html_positions_config_page(base_dir)
    elif page == "时间线导入":
        timeline_page()
    else:
        db_admin_page(base_dir)


if __name__ == "__main__":
    main()
