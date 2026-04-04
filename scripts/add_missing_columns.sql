-- 添加缺失的字段
ALTER TABLE public.positions 
ADD COLUMN IF NOT EXISTS exam_region text, -- 考区
ADD COLUMN IF NOT EXISTS unit_level text, -- 单位层级
ADD COLUMN IF NOT EXISTS position_nature text, -- 职位性质
ADD COLUMN IF NOT EXISTS exam_subjects text, -- 笔试考试科目
ADD COLUMN IF NOT EXISTS candidate_identity text, -- 报考人员身份要求
ADD COLUMN IF NOT EXISTS gender text, -- 性别要求
ADD COLUMN IF NOT EXISTS max_age text, -- 最高年龄要求
ADD COLUMN IF NOT EXISTS domicile text, -- 户籍要求
ADD COLUMN IF NOT EXISTS certification text, -- 职业资格证书等要求
ADD COLUMN IF NOT EXISTS min_service_years text, -- 最低服务年限要求
ADD COLUMN IF NOT EXISTS physical_test_standards text, -- 体能测评项目和标准
ADD COLUMN IF NOT EXISTS medical_test_standards text, -- 体检标准
ADD COLUMN IF NOT EXISTS phone1 text, -- 咨询电话1
ADD COLUMN IF NOT EXISTS phone2 text; -- 咨询电话2

-- 如果需要将旧的 phone 字段数据迁移到 phone1，可以取消注释以下行：
-- UPDATE public.positions SET phone1 = phone WHERE phone1 IS NULL AND phone IS NOT NULL;
