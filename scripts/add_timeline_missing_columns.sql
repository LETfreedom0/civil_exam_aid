-- 为 exam_timelines 表添加缺失的时间段字段
ALTER TABLE public.exam_timelines
ADD COLUMN IF NOT EXISTS payment_start date,   -- 缴费开始时间
ADD COLUMN IF NOT EXISTS admit_card_end date,  -- 准考证打印结束时间
ADD COLUMN IF NOT EXISTS exam_end_date date;   -- 笔试结束时间（针对多天考试情况）
