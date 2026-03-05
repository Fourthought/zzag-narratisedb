-- Schema redesign migration
-- Changes:
--   - Migrate all bigint IDs to uuid
--   - Drop chirp_analysis (replaced by generic analysis table)
--   - Drop chirp_safety_issue_sentences (replaced by chunk_sentences)
--   - Drop sections (no longer needed)
--   - Recreate chirp_analysis_shield_codes with analysis_id FK + human verification fields
--   - Add chunk_id + document_id + human verification fields to chirp_safety_issues and chirp_recommendations
--   - Add new tables: chunks, chunk_sentences, analysis, legislation, chirp_safety_issue_legislation, author_identifiers
--   - Reorder columns on all tables: id, parent FKs, content, classification, state, verification, timestamps
--
-- NOTE: This migration truncates all tables to enable the bigint → uuid ID migration.
-- Re-ingest documents and re-seed reference data after applying.

-- Column order convention:
--   1. id
--   2. parent / ownership FKs
--   3. core content / payload
--   4. classification / categorisation
--   5. scalar metadata / state
--   6. is_verified, verified_at (paired)
--   7. created_at, updated_at


-- ============================================================
-- STEP 1: Truncate all data
-- ============================================================

TRUNCATE TABLE
  public.chirp_analysis_shield_codes,
  public.chirp_analysis,
  public.chirp_safety_issue_sentences,
  public.chirp_safety_issues,
  public.chirp_recommendations,
  public.chirp_report_metadata,
  public.chirp_shield_codes,
  public.chirp_shield_code_categories,
  public.chirp_organisations,
  public.sentences,
  public.sections,
  public.documents,
  public.authors
CASCADE;


-- ============================================================
-- STEP 2: Drop all tables being removed or recreated
-- ============================================================

-- Removed entirely
DROP TABLE IF EXISTS public.chirp_analysis_shield_codes;
DROP TABLE IF EXISTS public.chirp_analysis;
DROP TABLE IF EXISTS public.chirp_safety_issue_sentences;
DROP TABLE IF EXISTS public.sections CASCADE;

-- Recreated with corrected column order (CASCADE drops any remaining FK constraints)
DROP TABLE IF EXISTS public.chirp_recommendations CASCADE;
DROP TABLE IF EXISTS public.chirp_safety_issues CASCADE;
DROP TABLE IF EXISTS public.chirp_report_metadata;
DROP TABLE IF EXISTS public.chirp_shield_codes CASCADE;
DROP TABLE IF EXISTS public.sentences CASCADE;
DROP TABLE IF EXISTS public.documents CASCADE;


-- ============================================================
-- STEP 3: Migrate simple tables in-place
-- (No FK columns — no ordering issues, just id type + timestamps)
-- ============================================================

-- authors
ALTER TABLE public.authors DROP CONSTRAINT authors_pkey;
ALTER TABLE public.authors ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.authors ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.authors ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.authors ADD CONSTRAINT authors_pkey PRIMARY KEY (id);
ALTER TABLE public.authors
  ADD COLUMN created_at timestamp with time zone DEFAULT now(),
  ADD COLUMN updated_at timestamp with time zone DEFAULT now();

-- chirp_shield_code_categories
ALTER TABLE public.chirp_shield_code_categories DROP CONSTRAINT chirp_shield_code_categories_pkey;
ALTER TABLE public.chirp_shield_code_categories ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.chirp_shield_code_categories ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.chirp_shield_code_categories ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.chirp_shield_code_categories ADD CONSTRAINT chirp_shield_code_categories_pkey PRIMARY KEY (id);
ALTER TABLE public.chirp_shield_code_categories
  ADD COLUMN created_at timestamp with time zone DEFAULT now(),
  ADD COLUMN updated_at timestamp with time zone DEFAULT now();

-- chirp_organisations
ALTER TABLE public.chirp_organisations DROP CONSTRAINT chirp_organisations_pkey;
ALTER TABLE public.chirp_organisations ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.chirp_organisations ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.chirp_organisations ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.chirp_organisations ADD CONSTRAINT chirp_organisations_pkey PRIMARY KEY (id);


-- ============================================================
-- STEP 4: Recreate generic tables with correct column order
-- ============================================================

CREATE TABLE public.documents (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  author_id uuid,
  title text NOT NULL,
  url text,
  filename text,
  hash text NOT NULL,
  publication_date date,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT documents_pkey PRIMARY KEY (id),
  CONSTRAINT documents_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id) ON DELETE SET NULL
);
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.sentences (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  document_id uuid,
  text text NOT NULL,
  text_type text NOT NULL,
  position integer,
  relevance_score integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT sentences_pkey PRIMARY KEY (id),
  CONSTRAINT sentences_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE
);
ALTER TABLE public.sentences ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- STEP 5: Recreate CHIRP reference tables with correct column order
-- ============================================================

CREATE TABLE public.chirp_shield_codes (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  category_id uuid,
  code text NOT NULL,
  title text NOT NULL,
  definition text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_shield_codes_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_shield_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.chirp_shield_code_categories(id) ON DELETE SET NULL
);
ALTER TABLE public.chirp_shield_codes ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.chirp_report_metadata (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  document_id uuid,
  vessel_name text,
  vessel_type text,
  accident_type text,
  accident_date date,
  accident_location text,
  severity text,
  loss_of_life integer,
  port_of_origin text,
  destination text,
  page_count integer,
  pdf_subject text,
  pdf_author text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_report_metadata_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_report_metadata_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE
);
ALTER TABLE public.chirp_report_metadata ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- STEP 6: Create new generic tables
-- ============================================================

CREATE TABLE public.chunks (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chunks_pkey PRIMARY KEY (id)
);
ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.chunk_sentences (
  chunk_id uuid NOT NULL,
  sentence_id uuid NOT NULL,
  position integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chunk_sentences_pkey PRIMARY KEY (chunk_id, sentence_id),
  CONSTRAINT chunk_sentences_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE CASCADE,
  CONSTRAINT chunk_sentences_sentence_id_fkey FOREIGN KEY (sentence_id) REFERENCES public.sentences(id) ON DELETE CASCADE
);
ALTER TABLE public.chunk_sentences ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  chunk_id uuid,
  analysis_type text,
  content text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT analysis_pkey PRIMARY KEY (id),
  CONSTRAINT analysis_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE CASCADE
);
ALTER TABLE public.analysis ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.legislation (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  reference text,
  jurisdiction text,
  url text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT legislation_pkey PRIMARY KEY (id)
);
ALTER TABLE public.legislation ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.author_identifiers (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  author_id uuid NOT NULL,
  identifier text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT author_identifiers_pkey PRIMARY KEY (id),
  CONSTRAINT author_identifiers_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id) ON DELETE CASCADE
);
ALTER TABLE public.author_identifiers ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- STEP 7: Recreate CHIRP domain tables with correct column order
-- ============================================================

CREATE TABLE public.chirp_safety_issues (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  document_id uuid,
  chunk_id uuid,
  name text,
  is_verified boolean DEFAULT false,
  verified_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_safety_issues_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_safety_issues_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE,
  CONSTRAINT chirp_safety_issues_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE SET NULL
);
ALTER TABLE public.chirp_safety_issues ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.chirp_recommendations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  document_id uuid,
  chunk_id uuid,
  organisation_id uuid,
  recommendation text NOT NULL,
  is_implemented boolean DEFAULT false,
  is_verified boolean DEFAULT false,
  verified_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_recommendations_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_recommendations_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE,
  CONSTRAINT chirp_recommendations_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE SET NULL,
  CONSTRAINT chirp_recommendations_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.chirp_organisations(id) ON DELETE SET NULL
);
ALTER TABLE public.chirp_recommendations ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.chirp_analysis_shield_codes (
  analysis_id uuid NOT NULL,
  shield_code_id uuid NOT NULL,
  is_verified boolean DEFAULT false,
  verified_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_analysis_shield_codes_pkey PRIMARY KEY (analysis_id, shield_code_id),
  CONSTRAINT chirp_analysis_shield_codes_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.analysis(id) ON DELETE CASCADE,
  CONSTRAINT chirp_analysis_shield_codes_shield_code_id_fkey FOREIGN KEY (shield_code_id) REFERENCES public.chirp_shield_codes(id) ON DELETE CASCADE
);
ALTER TABLE public.chirp_analysis_shield_codes ENABLE ROW LEVEL SECURITY;

CREATE TABLE public.chirp_safety_issue_legislation (
  safety_issue_id uuid NOT NULL,
  legislation_id uuid NOT NULL,
  extract text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_safety_issue_legislation_pkey PRIMARY KEY (safety_issue_id, legislation_id),
  CONSTRAINT chirp_safety_issue_legislation_safety_issue_id_fkey FOREIGN KEY (safety_issue_id) REFERENCES public.chirp_safety_issues(id) ON DELETE CASCADE,
  CONSTRAINT chirp_safety_issue_legislation_legislation_id_fkey FOREIGN KEY (legislation_id) REFERENCES public.legislation(id) ON DELETE CASCADE
);
ALTER TABLE public.chirp_safety_issue_legislation ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- STEP 8: RLS policies
-- ============================================================

-- authors (existing table, policies already exist — no change needed)

-- documents (recreated)
CREATE POLICY "Documents: Public read access" ON public.documents FOR SELECT USING (true);
CREATE POLICY "Documents: Authenticated insert" ON public.documents FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Documents: Authenticated update" ON public.documents FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Documents: Authenticated delete" ON public.documents FOR DELETE USING ((auth.uid() IS NOT NULL));

-- sentences (recreated)
CREATE POLICY "Sentences: Public read access" ON public.sentences FOR SELECT USING (true);
CREATE POLICY "Sentences: Authenticated insert" ON public.sentences FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Sentences: Authenticated update" ON public.sentences FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Sentences: Authenticated delete" ON public.sentences FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chirp_shield_codes (recreated)
CREATE POLICY "Chirp Shield Codes: Public read access" ON public.chirp_shield_codes FOR SELECT USING (true);
CREATE POLICY "Chirp Shield Codes: Authenticated insert" ON public.chirp_shield_codes FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Codes: Authenticated update" ON public.chirp_shield_codes FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Codes: Authenticated delete" ON public.chirp_shield_codes FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chirp_report_metadata (recreated)
CREATE POLICY "Chirp Report Metadata: Public read access" ON public.chirp_report_metadata FOR SELECT USING (true);
CREATE POLICY "Chirp Report Metadata: Authenticated insert" ON public.chirp_report_metadata FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Report Metadata: Authenticated update" ON public.chirp_report_metadata FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Report Metadata: Authenticated delete" ON public.chirp_report_metadata FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chunks (new)
CREATE POLICY "Chunks: Public read access" ON public.chunks FOR SELECT USING (true);
CREATE POLICY "Chunks: Authenticated insert" ON public.chunks FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunks: Authenticated update" ON public.chunks FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunks: Authenticated delete" ON public.chunks FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chunk_sentences (new)
CREATE POLICY "Chunk Sentences: Public read access" ON public.chunk_sentences FOR SELECT USING (true);
CREATE POLICY "Chunk Sentences: Authenticated insert" ON public.chunk_sentences FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunk Sentences: Authenticated update" ON public.chunk_sentences FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunk Sentences: Authenticated delete" ON public.chunk_sentences FOR DELETE USING ((auth.uid() IS NOT NULL));

-- analysis (new)
CREATE POLICY "Analysis: Public read access" ON public.analysis FOR SELECT USING (true);
CREATE POLICY "Analysis: Authenticated insert" ON public.analysis FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Analysis: Authenticated update" ON public.analysis FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Analysis: Authenticated delete" ON public.analysis FOR DELETE USING ((auth.uid() IS NOT NULL));

-- legislation (new)
CREATE POLICY "Legislation: Public read access" ON public.legislation FOR SELECT USING (true);
CREATE POLICY "Legislation: Authenticated insert" ON public.legislation FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Legislation: Authenticated update" ON public.legislation FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Legislation: Authenticated delete" ON public.legislation FOR DELETE USING ((auth.uid() IS NOT NULL));

-- author_identifiers (new)
CREATE POLICY "Author Identifiers: Public read access" ON public.author_identifiers FOR SELECT USING (true);
CREATE POLICY "Author Identifiers: Authenticated insert" ON public.author_identifiers FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Author Identifiers: Authenticated update" ON public.author_identifiers FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Author Identifiers: Authenticated delete" ON public.author_identifiers FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chirp_safety_issues (recreated)
CREATE POLICY "Chirp Safety Issues: Public read access" ON public.chirp_safety_issues FOR SELECT USING (true);
CREATE POLICY "Chirp Safety Issues: Authenticated insert" ON public.chirp_safety_issues FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issues: Authenticated update" ON public.chirp_safety_issues FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issues: Authenticated delete" ON public.chirp_safety_issues FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chirp_recommendations (recreated)
CREATE POLICY "Chirp Recommendations: Public read access" ON public.chirp_recommendations FOR SELECT USING (true);
CREATE POLICY "Chirp Recommendations: Authenticated insert" ON public.chirp_recommendations FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Recommendations: Authenticated update" ON public.chirp_recommendations FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Recommendations: Authenticated delete" ON public.chirp_recommendations FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chirp_analysis_shield_codes (recreated)
CREATE POLICY "Chirp Analysis Shield Codes: Public read access" ON public.chirp_analysis_shield_codes FOR SELECT USING (true);
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated insert" ON public.chirp_analysis_shield_codes FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated update" ON public.chirp_analysis_shield_codes FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated delete" ON public.chirp_analysis_shield_codes FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chirp_safety_issue_legislation (new)
CREATE POLICY "Chirp Safety Issue Legislation: Public read access" ON public.chirp_safety_issue_legislation FOR SELECT USING (true);
CREATE POLICY "Chirp Safety Issue Legislation: Authenticated insert" ON public.chirp_safety_issue_legislation FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Legislation: Authenticated update" ON public.chirp_safety_issue_legislation FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Legislation: Authenticated delete" ON public.chirp_safety_issue_legislation FOR DELETE USING ((auth.uid() IS NOT NULL));


-- ============================================================
-- STEP 9: Grants for recreated and new tables
-- ============================================================

GRANT ALL ON TABLE public.documents TO anon;
GRANT ALL ON TABLE public.documents TO authenticated;
GRANT ALL ON TABLE public.documents TO service_role;

GRANT ALL ON TABLE public.sentences TO anon;
GRANT ALL ON TABLE public.sentences TO authenticated;
GRANT ALL ON TABLE public.sentences TO service_role;

GRANT ALL ON TABLE public.chirp_shield_codes TO anon;
GRANT ALL ON TABLE public.chirp_shield_codes TO authenticated;
GRANT ALL ON TABLE public.chirp_shield_codes TO service_role;

GRANT ALL ON TABLE public.chirp_report_metadata TO anon;
GRANT ALL ON TABLE public.chirp_report_metadata TO authenticated;
GRANT ALL ON TABLE public.chirp_report_metadata TO service_role;

GRANT ALL ON TABLE public.chunks TO anon;
GRANT ALL ON TABLE public.chunks TO authenticated;
GRANT ALL ON TABLE public.chunks TO service_role;

GRANT ALL ON TABLE public.chunk_sentences TO anon;
GRANT ALL ON TABLE public.chunk_sentences TO authenticated;
GRANT ALL ON TABLE public.chunk_sentences TO service_role;

GRANT ALL ON TABLE public.analysis TO anon;
GRANT ALL ON TABLE public.analysis TO authenticated;
GRANT ALL ON TABLE public.analysis TO service_role;

GRANT ALL ON TABLE public.legislation TO anon;
GRANT ALL ON TABLE public.legislation TO authenticated;
GRANT ALL ON TABLE public.legislation TO service_role;

GRANT ALL ON TABLE public.author_identifiers TO anon;
GRANT ALL ON TABLE public.author_identifiers TO authenticated;
GRANT ALL ON TABLE public.author_identifiers TO service_role;

GRANT ALL ON TABLE public.chirp_safety_issues TO anon;
GRANT ALL ON TABLE public.chirp_safety_issues TO authenticated;
GRANT ALL ON TABLE public.chirp_safety_issues TO service_role;

GRANT ALL ON TABLE public.chirp_recommendations TO anon;
GRANT ALL ON TABLE public.chirp_recommendations TO authenticated;
GRANT ALL ON TABLE public.chirp_recommendations TO service_role;

GRANT ALL ON TABLE public.chirp_analysis_shield_codes TO anon;
GRANT ALL ON TABLE public.chirp_analysis_shield_codes TO authenticated;
GRANT ALL ON TABLE public.chirp_analysis_shield_codes TO service_role;

GRANT ALL ON TABLE public.chirp_safety_issue_legislation TO anon;
GRANT ALL ON TABLE public.chirp_safety_issue_legislation TO authenticated;
GRANT ALL ON TABLE public.chirp_safety_issue_legislation TO service_role;
