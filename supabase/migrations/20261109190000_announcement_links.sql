-- =============================================================================
-- 公告链接贯通：让每条岗位都能一键直达考试公告
--
-- 现状问题：
--   positions_full.source_url 全空，announcement_id 只有 2 行有值；
--   notices.url 存的是附件 xlsx 直链，不是公告页，用户点进去只能下载文件。
--
-- 本迁移做四件事：
--   1. announcements 加 url 唯一索引（导入端 upsert 幂等用）
--   2. notices 加 kind 区分「公告页 / 采集附件」
--   3. 回填 positions / positions_full 的 announcement_id + source_url
--   4. 回填 exam_cycles 的公告标题与链接（批次维度）
-- =============================================================================

-- 1) 公告主表：url 唯一，供 PostgREST on_conflict=url upsert ------------------
CREATE UNIQUE INDEX IF NOT EXISTS announcements_url_uidx
  ON public.announcements (url);

CREATE INDEX IF NOT EXISTS announcements_province_year_idx
  ON public.announcements (province_code, year);

-- 2) notices：区分公告页与附件 ------------------------------------------------
ALTER TABLE public.notices
  ADD COLUMN IF NOT EXISTS kind text NOT NULL DEFAULT 'attachment';

ALTER TABLE public.notices DROP CONSTRAINT IF EXISTS notices_kind_chk;
ALTER TABLE public.notices
  ADD CONSTRAINT notices_kind_chk CHECK (kind IN ('announcement', 'attachment'));

CREATE INDEX IF NOT EXISTS notices_kind_idx ON public.notices (kind);

-- 3) 存量回填：把已知公告挂到同省同年岗位 ------------------------------------
--    广西 2026：3360 行（采集自 gxpta 公告页）
--    广东 2026：2 行（announcement_id 已是 1，补 source_url）
INSERT INTO public.announcements (province_code, year, title, url, exam_type)
SELECT '450000', 2026,
       '广西壮族自治区2026年度考试录用公务员公告',
       'https://www.gxpta.com.cn/ksxm/gwyzlks/gx2026ndkslygwyxdszt/2026ngwygg/t13229.html',
       '省考'
WHERE NOT EXISTS (
  SELECT 1 FROM public.announcements
   WHERE url = 'https://www.gxpta.com.cn/ksxm/gwyzlks/gx2026ndkslygwyxdszt/2026ngwygg/t13229.html'
);

UPDATE public.positions_full p
   SET announcement_id = a.id,
       source_url = a.url
  FROM public.announcements a
 WHERE a.province_code = p.province_code
   AND a.year = p.year
   AND (p.announcement_id IS NULL OR p.source_url IS NULL);

UPDATE public.positions p
   SET announcement_id = a.id,
       source_url = a.url
  FROM public.announcements a
 WHERE a.province_code = p.province_code
   AND a.year = p.year
   AND (p.announcement_id IS NULL OR p.source_url IS NULL);

-- 4) 批次（exam_cycles）同步公告信息 -----------------------------------------
UPDATE public.exam_cycles c
   SET announcement_url = a.url,
       announcement_title = a.title
  FROM public.announcements a
 WHERE a.province_code = c.province_code
   AND a.year = c.year
   AND (c.announcement_url IS NULL OR c.announcement_title IS NULL);

-- 5) 回填一批公告页记录到 notices（历史附件记录保持 attachment） ------------
INSERT INTO public.notices (url, title, source_id, kind)
SELECT a.url, a.title, NULL, 'announcement'
  FROM public.announcements a
 WHERE a.url IS NOT NULL
ON CONFLICT (url) DO UPDATE
   SET kind = 'announcement',
       title = COALESCE(public.notices.title, EXCLUDED.title);
