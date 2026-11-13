-- =============================================================================
-- 助残公考 · 数据结构 v2
-- 迁移 2/3：索引、行级安全、权限收紧
--
-- 重点解决两个现网问题：
--   1. 列表「拉全量再前端过滤」——加 trigram 索引，让关键词搜索走数据库
--   2. anon key 能往 positions 里随便写——撤销匿名写权限
-- =============================================================================

create extension if not exists pg_trgm;

-- -----------------------------------------------------------------------------
-- 1. 索引
-- -----------------------------------------------------------------------------

-- 列表主查询：省份 + 年份 + 考试类别
create index if not exists idx_positions_province_year
  on public.positions (province_code, year, position_origin);

create index if not exists idx_positions_cycle
  on public.positions (cycle_id);

create index if not exists idx_positions_active
  on public.positions (id) where is_active;

create index if not exists idx_positions_disability_only
  on public.positions (province_code, year) where is_disability_only;

-- 关键词搜索：替代前端 includes，支持「职位/单位/专业」三路 ILIKE
create index if not exists idx_positions_name_trgm
  on public.positions using gin (position_name gin_trgm_ops);
create index if not exists idx_positions_unit_trgm
  on public.positions using gin (recruit_unit gin_trgm_ops);
create index if not exists idx_positions_major_trgm
  on public.positions using gin (major gin_trgm_ops);

-- 「我是听力残疾，能报哪些岗」——数组包含查询
create index if not exists idx_position_disability_types
  on public.position_disability using gin (disability_types);

create index if not exists idx_position_disability_exclusive
  on public.position_disability (position_id) where is_exclusive;

create index if not exists idx_exam_cycles_lookup
  on public.exam_cycles (province_code, year, category);

create index if not exists idx_majors_parent
  on public.majors (parent_id);

create index if not exists idx_majors_name_trgm
  on public.majors using gin (name gin_trgm_ops);

create index if not exists idx_position_majors_major
  on public.position_majors (major_id);

create index if not exists idx_report_feedback_status
  on public.report_feedback (status, created_at desc);

create index if not exists idx_favorites_openid
  on public.favorites (user_openid, created_at desc);

create index if not exists idx_update_logs_created
  on public.update_logs (created_at desc);

-- -----------------------------------------------------------------------------
-- 2. 行级安全
-- -----------------------------------------------------------------------------

alter table public.exam_cycles          enable row level security;
alter table public.position_disability  enable row level security;
alter table public.majors               enable row level security;
alter table public.position_majors      enable row level security;
alter table public.education_levels     enable row level security;
alter table public.data_sources         enable row level security;
alter table public.update_logs          enable row level security;
alter table public.report_feedback      enable row level security;
alter table public.favorites            enable row level security;

-- 公开读：职位、批次、适配、专业字典 —— 小程序端只读
drop policy if exists "Public read exam_cycles" on public.exam_cycles;
create policy "Public read exam_cycles" on public.exam_cycles
  for select using (true);

drop policy if exists "Public read position_disability" on public.position_disability;
create policy "Public read position_disability" on public.position_disability
  for select using (true);

drop policy if exists "Public read majors" on public.majors;
create policy "Public read majors" on public.majors
  for select using (true);

drop policy if exists "Public read position_majors" on public.position_majors;
create policy "Public read position_majors" on public.position_majors
  for select using (true);

drop policy if exists "Public read education_levels" on public.education_levels;
create policy "Public read education_levels" on public.education_levels
  for select using (true);

drop policy if exists "Public read update_logs" on public.update_logs;
create policy "Public read update_logs" on public.update_logs
  for select using (true);

-- 报错反馈：任何人可提交，不允许删改（处理走 service_role）
drop policy if exists "Anyone can submit report" on public.report_feedback;
create policy "Anyone can submit report" on public.report_feedback
  for insert with check (true);

-- 收藏：当前先允许读写；接入 openid 鉴权后应改为
--   using (user_openid = current_setting('request.jwt.claims', true)::json->>'sub')
drop policy if exists "Read favorites" on public.favorites;
create policy "Read favorites" on public.favorites
  for select using (true);

drop policy if exists "Write favorites" on public.favorites;
create policy "Write favorites" on public.favorites
  for insert with check (true);

drop policy if exists "Delete favorites" on public.favorites;
create policy "Delete favorites" on public.favorites
  for delete using (true);

-- -----------------------------------------------------------------------------
-- 3. 权限收紧（现网隐患：anon key 可以往 positions 写数据）
-- -----------------------------------------------------------------------------
drop policy if exists "Enable insert access for all users" on public.positions;
drop policy if exists "Enable read access for all users"   on public.positions;
drop policy if exists "Public read positions"              on public.positions;

create policy "Public read positions" on public.positions
  for select using (true);

revoke insert, update, delete, truncate on public.positions from anon, authenticated;
revoke insert, update, delete on public.exam_cycles         from anon, authenticated;
revoke insert, update, delete on public.position_disability from anon, authenticated;
revoke insert, update, delete on public.majors              from anon, authenticated;
revoke insert, update, delete on public.position_majors     from anon, authenticated;
revoke insert, update, delete on public.education_levels    from anon, authenticated;
revoke insert, update, delete on public.update_logs         from anon, authenticated;
revoke update, delete            on public.report_feedback  from anon, authenticated;
revoke update, delete            on public.favorites        from anon, authenticated;

-- 视图需要显式授权，PostgREST 通过 anon 角色读取
grant select on public.exam_timelines to anon, authenticated;

-- -----------------------------------------------------------------------------
-- 4. 常用查询封装（可选）
--    把「按残疾类别找岗位」收敛成一个视图，前端不必自己拼 join
-- -----------------------------------------------------------------------------
create or replace view public.position_feed as
select
  p.id,
  p.position_name,
  p.recruit_unit,
  p.region_dept,
  p.quota,
  p.education,
  p.degree,
  p.major,
  p.description,
  p.other_requirements,
  p.position_origin,
  p.province_code,
  p.year,
  p.is_disability_only,
  p.cycle_id,
  c.status            as cycle_status,
  d.disability_types,
  d.is_exclusive,
  d.accessible_exam_room,
  d.sign_language_interpreter
from public.positions p
left join public.exam_cycles c         on c.id = p.cycle_id
left join public.position_disability d on d.position_id = p.id
where p.is_active;

comment on view public.position_feed is '列表页聚合视图：岗位 + 批次状态 + 适配标签，一次查询拿全';

grant select on public.position_feed to anon, authenticated;
