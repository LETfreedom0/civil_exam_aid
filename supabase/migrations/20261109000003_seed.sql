-- =============================================================================
-- 助残公考 · 数据结构 v2
-- 迁移 3/3：字典与种子数据
-- 幂等：可重复执行
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. 学历档位
-- -----------------------------------------------------------------------------
insert into public.education_levels (code, name, rank) values
  ('high_school', '高中/中专', 1),
  ('college',     '大专',      2),
  ('bachelor',    '本科',      3),
  ('master',      '硕士',      4),
  ('doctor',      '博士',      5)
on conflict (code) do update
  set name = excluded.name,
      rank = excluded.rank;

-- -----------------------------------------------------------------------------
-- 2. 残疾类别字典（界面展示用，DB 里只存 code）
-- -----------------------------------------------------------------------------
create table if not exists public.disability_types (
  code       text primary key,
  name       text not null,
  sort_order smallint not null default 0
);

insert into public.disability_types (code, name, sort_order) values
  ('vision',       '视力残疾',   1),
  ('hearing',      '听力残疾',   2),
  ('speech',       '言语残疾',   3),
  ('physical',     '肢体残疾',   4),
  ('intellectual', '智力残疾',   5),
  ('mental',       '精神残疾',   6),
  ('multiple',     '多重残疾',   7)
on conflict (code) do update
  set name = excluded.name,
      sort_order = excluded.sort_order;

-- -----------------------------------------------------------------------------
-- 3. 省份补齐：兵团是独立考区，旧 schema 漏了；同时补全称与区域分组
-- -----------------------------------------------------------------------------
insert into public.provinces (code, name) values ('660000', '兵团')
on conflict (code) do nothing;

update public.provinces p set
  short_name = v.short_name,
  region_group = v.region_group,
  pinyin = v.pinyin
from (values
  ('110000','北京','北京','华北','beijing'),
  ('120000','天津','天津','华北','tianjin'),
  ('130000','河北','河北','华北','hebei'),
  ('140000','山西','山西','华北','shanxi'),
  ('150000','内蒙古','内蒙古自治区','华北','neimenggu'),
  ('210000','辽宁','辽宁','东北','liaoning'),
  ('220000','吉林','吉林','东北','jilin'),
  ('230000','黑龙江','黑龙江','东北','heilongjiang'),
  ('310000','上海','上海','华东','shanghai'),
  ('320000','江苏','江苏','华东','jiangsu'),
  ('330000','浙江','浙江','华东','zhejiang'),
  ('340000','安徽','安徽','华东','anhui'),
  ('350000','福建','福建','华东','fujian'),
  ('360000','江西','江西','华东','jiangxi'),
  ('370000','山东','山东','华东','shandong'),
  ('410000','河南','河南','华中','henan'),
  ('420000','湖北','湖北','华中','hubei'),
  ('430000','湖南','湖南','华中','hunan'),
  ('440000','广东','广东','华南','guangdong'),
  ('450000','广西','广西壮族自治区','华南','guangxi'),
  ('460000','海南','海南','华南','hainan'),
  ('500000','重庆','重庆','西南','chongqing'),
  ('510000','四川','四川','西南','sichuan'),
  ('520000','贵州','贵州','西南','guizhou'),
  ('530000','云南','云南','西南','yunnan'),
  ('540000','西藏','西藏自治区','西南','xizang'),
  ('610000','陕西','陕西','西北','shaanxi'),
  ('620000','甘肃','甘肃','西北','gansu'),
  ('630000','青海','青海','西北','qinghai'),
  ('640000','宁夏','宁夏回族自治区','西北','ningxia'),
  ('650000','新疆','新疆维吾尔自治区','西北','xinjiang'),
  ('660000','兵团','新疆生产建设兵团','西北','bingtuan')
) as v(code, name, short_name, region_group, pinyin)
where p.code = v.code;

-- -----------------------------------------------------------------------------
-- 4. 专业目录示例（完整目录需导入教育部《普通高等学校本科专业目录》）
--    这里只放足以验证树形结构与匹配逻辑的样本
-- -----------------------------------------------------------------------------
insert into public.majors (code, name, level, discipline) values
  ('08',      '工学',             1, '工学'),
  ('0809',    '计算机类',          2, '工学'),
  ('080901',  '计算机科学与技术',   3, '工学'),
  ('080902',  '软件工程',          3, '工学'),
  ('0301',    '法学类',            2, '法学'),
  ('030101K', '法学',              3, '法学'),
  ('0501',    '中国语言文学类',     2, '文学'),
  ('050101',  '汉语言文学',        3, '文学')
on conflict (code) do nothing;

-- 建立父子关系
update public.majors c set parent_id = p.id
from public.majors p
where c.code in ('080901','080902') and p.code = '0809';

update public.majors c set parent_id = p.id
from public.majors p
where c.code = '0809' and p.code = '08';

update public.majors c set parent_id = p.id
from public.majors p
where c.code = '030101K' and p.code = '0301';

update public.majors c set parent_id = p.id
from public.majors p
where c.code = '050101' and p.code = '0501';

-- 别名，用于「计科」「软工」这类口语化搜索
update public.majors set keywords = array['计科','计算机']
where code = '080901';
update public.majors set keywords = array['软工']
where code = '080902';
