-- Schema redesign migration
-- Changes:
--   - Migrate all bigint IDs to uuid
--   - Drop chirp_analysis (replaced by generic analysis table)
--   - Drop chirp_safety_issue_sentences (replaced by chunk_sentences)
--   - Recreate chirp_analysis_shield_codes with analysis_id FK + human verification fields
--   - Add chunk_id + human verification fields to chirp_safety_issues and chirp_recommendations
--   - Add new tables: chunks, chunk_sentences, analysis, legislation, chirp_safety_issue_legislation
--
-- NOTE: This migration truncates all tables to enable the bigint → uuid ID migration.
-- Re-ingest documents and re-seed reference data after applying.


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
-- STEP 2: Drop tables being replaced
-- ============================================================

DROP TABLE IF EXISTS public.chirp_analysis_shield_codes;
DROP TABLE IF EXISTS public.chirp_analysis;
DROP TABLE IF EXISTS public.chirp_safety_issue_sentences;
DROP TABLE IF EXISTS public.sections CASCADE;


-- ============================================================
-- STEP 3: Drop all FK constraints before altering column types
-- ============================================================

ALTER TABLE public.sentences DROP CONSTRAINT IF EXISTS sentences_document_id_fkey;
ALTER TABLE public.sentences DROP CONSTRAINT IF EXISTS sentences_section_id_fkey;
ALTER TABLE public.documents DROP CONSTRAINT IF EXISTS documents_author_id_fkey;
ALTER TABLE public.chirp_safety_issues DROP CONSTRAINT IF EXISTS chirp_safety_issues_document_id_fkey;
ALTER TABLE public.chirp_recommendations DROP CONSTRAINT IF EXISTS chirp_recommendations_document_id_fkey;
ALTER TABLE public.chirp_recommendations DROP CONSTRAINT IF EXISTS chirp_recommendations_organisation_id_fkey;
ALTER TABLE public.chirp_report_metadata DROP CONSTRAINT IF EXISTS chirp_report_metadata_document_id_fkey;
ALTER TABLE public.chirp_shield_codes DROP CONSTRAINT IF EXISTS chirp_shield_codes_category_id_fkey;


-- ============================================================
-- STEP 4: Migrate PK columns from bigint identity to uuid
-- ============================================================

-- authors
ALTER TABLE public.authors DROP CONSTRAINT authors_pkey;
ALTER TABLE public.authors ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.authors ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.authors ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.authors ADD CONSTRAINT authors_pkey PRIMARY KEY (id);

-- documents
ALTER TABLE public.documents DROP CONSTRAINT documents_pkey;
ALTER TABLE public.documents ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.documents ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.documents ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.documents ADD CONSTRAINT documents_pkey PRIMARY KEY (id);

-- sentences
ALTER TABLE public.sentences DROP CONSTRAINT sentences_pkey;
ALTER TABLE public.sentences ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.sentences ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.sentences ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.sentences ADD CONSTRAINT sentences_pkey PRIMARY KEY (id);

-- chirp_shield_code_categories
ALTER TABLE public.chirp_shield_code_categories DROP CONSTRAINT chirp_shield_code_categories_pkey;
ALTER TABLE public.chirp_shield_code_categories ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.chirp_shield_code_categories ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.chirp_shield_code_categories ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.chirp_shield_code_categories ADD CONSTRAINT chirp_shield_code_categories_pkey PRIMARY KEY (id);

-- chirp_shield_codes
ALTER TABLE public.chirp_shield_codes DROP CONSTRAINT chirp_shield_codes_pkey;
ALTER TABLE public.chirp_shield_codes ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.chirp_shield_codes ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.chirp_shield_codes ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.chirp_shield_codes ADD CONSTRAINT chirp_shield_codes_pkey PRIMARY KEY (id);

-- chirp_organisations
ALTER TABLE public.chirp_organisations DROP CONSTRAINT chirp_organisations_pkey;
ALTER TABLE public.chirp_organisations ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.chirp_organisations ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.chirp_organisations ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.chirp_organisations ADD CONSTRAINT chirp_organisations_pkey PRIMARY KEY (id);

-- chirp_report_metadata
ALTER TABLE public.chirp_report_metadata DROP CONSTRAINT chirp_report_metadata_pkey;
ALTER TABLE public.chirp_report_metadata ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.chirp_report_metadata ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.chirp_report_metadata ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.chirp_report_metadata ADD CONSTRAINT chirp_report_metadata_pkey PRIMARY KEY (id);

-- chirp_safety_issues
ALTER TABLE public.chirp_safety_issues DROP CONSTRAINT chirp_safety_issues_pkey;
ALTER TABLE public.chirp_safety_issues ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.chirp_safety_issues ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.chirp_safety_issues ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.chirp_safety_issues ADD CONSTRAINT chirp_safety_issues_pkey PRIMARY KEY (id);

-- chirp_recommendations
ALTER TABLE public.chirp_recommendations DROP CONSTRAINT chirp_recommendations_pkey;
ALTER TABLE public.chirp_recommendations ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE public.chirp_recommendations ALTER COLUMN id TYPE uuid USING gen_random_uuid();
ALTER TABLE public.chirp_recommendations ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE public.chirp_recommendations ADD CONSTRAINT chirp_recommendations_pkey PRIMARY KEY (id);


-- ============================================================
-- STEP 5: Migrate FK columns (drop and re-add as uuid)
-- ============================================================

-- documents.author_id
ALTER TABLE public.documents DROP COLUMN author_id;
ALTER TABLE public.documents ADD COLUMN author_id uuid;

-- sentences.document_id (section_id dropped entirely — sections table removed)
ALTER TABLE public.sentences DROP COLUMN document_id;
ALTER TABLE public.sentences ADD COLUMN document_id uuid;
ALTER TABLE public.sentences DROP COLUMN section_id;

-- chirp_shield_codes.category_id
ALTER TABLE public.chirp_shield_codes DROP COLUMN category_id;
ALTER TABLE public.chirp_shield_codes ADD COLUMN category_id uuid;

-- chirp_report_metadata.document_id
ALTER TABLE public.chirp_report_metadata DROP COLUMN document_id;
ALTER TABLE public.chirp_report_metadata ADD COLUMN document_id uuid;

-- chirp_recommendations.organisation_id
ALTER TABLE public.chirp_recommendations DROP COLUMN organisation_id;
ALTER TABLE public.chirp_recommendations ADD COLUMN organisation_id uuid;

-- chirp_safety_issues.document_id (kept alongside chunk_id — denormalised for query ergonomics)
ALTER TABLE public.chirp_safety_issues DROP COLUMN document_id;
ALTER TABLE public.chirp_safety_issues ADD COLUMN document_id uuid;

-- chirp_recommendations.document_id (kept alongside chunk_id — denormalised for query ergonomics)
ALTER TABLE public.chirp_recommendations DROP COLUMN document_id;
ALTER TABLE public.chirp_recommendations ADD COLUMN document_id uuid;


-- ============================================================
-- STEP 6: Restore FK constraints on existing tables
-- ============================================================

ALTER TABLE public.documents
  ADD CONSTRAINT documents_author_id_fkey
  FOREIGN KEY (author_id) REFERENCES public.authors(id) ON DELETE SET NULL;

ALTER TABLE public.sentences
  ADD CONSTRAINT sentences_document_id_fkey
  FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;

ALTER TABLE public.chirp_shield_codes
  ADD CONSTRAINT chirp_shield_codes_category_id_fkey
  FOREIGN KEY (category_id) REFERENCES public.chirp_shield_code_categories(id) ON DELETE SET NULL;

ALTER TABLE public.chirp_report_metadata
  ADD CONSTRAINT chirp_report_metadata_document_id_fkey
  FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;

ALTER TABLE public.chirp_recommendations
  ADD CONSTRAINT chirp_recommendations_organisation_id_fkey
  FOREIGN KEY (organisation_id) REFERENCES public.chirp_organisations(id) ON DELETE SET NULL;

ALTER TABLE public.chirp_safety_issues
  ADD CONSTRAINT chirp_safety_issues_document_id_fkey
  FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;

ALTER TABLE public.chirp_recommendations
  ADD CONSTRAINT chirp_recommendations_document_id_fkey
  FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


-- ============================================================
-- STEP 7: Add missing timestamps to existing tables
-- ============================================================

ALTER TABLE public.authors
  ADD COLUMN created_at timestamp with time zone DEFAULT now(),
  ADD COLUMN updated_at timestamp with time zone DEFAULT now();

ALTER TABLE public.chirp_shield_code_categories
  ADD COLUMN created_at timestamp with time zone DEFAULT now(),
  ADD COLUMN updated_at timestamp with time zone DEFAULT now();

ALTER TABLE public.chirp_shield_codes
  ADD COLUMN created_at timestamp with time zone DEFAULT now(),
  ADD COLUMN updated_at timestamp with time zone DEFAULT now();


-- ============================================================
-- STEP 8: Create chunks and chunk_sentences
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


-- ============================================================
-- STEP 9: Create generic analysis table
-- ============================================================

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


-- ============================================================
-- STEP 10: Add chunk_id, verification fields, and timestamps to CHIRP domain tables
-- ============================================================

ALTER TABLE public.chirp_safety_issues
  ADD COLUMN chunk_id uuid,
  ADD COLUMN is_verified boolean DEFAULT false,
  ADD COLUMN verified_at timestamp with time zone,
  ADD COLUMN created_at timestamp with time zone DEFAULT now(),
  ADD COLUMN updated_at timestamp with time zone DEFAULT now();

ALTER TABLE public.chirp_safety_issues
  ADD CONSTRAINT chirp_safety_issues_chunk_id_fkey
  FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE SET NULL;

ALTER TABLE public.chirp_recommendations
  ADD COLUMN chunk_id uuid,
  ADD COLUMN is_verified boolean DEFAULT false,
  ADD COLUMN verified_at timestamp with time zone;

ALTER TABLE public.chirp_recommendations
  ADD CONSTRAINT chirp_recommendations_chunk_id_fkey
  FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE SET NULL;


-- ============================================================
-- STEP 11: Recreate chirp_analysis_shield_codes with new structure
-- ============================================================

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


-- ============================================================
-- STEP 12: Create legislation and chirp_safety_issue_legislation
-- ============================================================

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
-- STEP 13: Create author_identifiers
-- ============================================================

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
-- STEP 14: RLS policies for new and recreated tables
-- ============================================================

-- author_identifiers
CREATE POLICY "Author Identifiers: Public read access" ON public.author_identifiers FOR SELECT USING (true);
CREATE POLICY "Author Identifiers: Authenticated insert" ON public.author_identifiers FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Author Identifiers: Authenticated update" ON public.author_identifiers FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Author Identifiers: Authenticated delete" ON public.author_identifiers FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chunks
CREATE POLICY "Chunks: Public read access" ON public.chunks FOR SELECT USING (true);
CREATE POLICY "Chunks: Authenticated insert" ON public.chunks FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunks: Authenticated update" ON public.chunks FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunks: Authenticated delete" ON public.chunks FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chunk_sentences
CREATE POLICY "Chunk Sentences: Public read access" ON public.chunk_sentences FOR SELECT USING (true);
CREATE POLICY "Chunk Sentences: Authenticated insert" ON public.chunk_sentences FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunk Sentences: Authenticated update" ON public.chunk_sentences FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunk Sentences: Authenticated delete" ON public.chunk_sentences FOR DELETE USING ((auth.uid() IS NOT NULL));

-- analysis
CREATE POLICY "Analysis: Public read access" ON public.analysis FOR SELECT USING (true);
CREATE POLICY "Analysis: Authenticated insert" ON public.analysis FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Analysis: Authenticated update" ON public.analysis FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Analysis: Authenticated delete" ON public.analysis FOR DELETE USING ((auth.uid() IS NOT NULL));

-- legislation
CREATE POLICY "Legislation: Public read access" ON public.legislation FOR SELECT USING (true);
CREATE POLICY "Legislation: Authenticated insert" ON public.legislation FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Legislation: Authenticated update" ON public.legislation FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Legislation: Authenticated delete" ON public.legislation FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chirp_analysis_shield_codes (recreated)
CREATE POLICY "Chirp Analysis Shield Codes: Public read access" ON public.chirp_analysis_shield_codes FOR SELECT USING (true);
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated insert" ON public.chirp_analysis_shield_codes FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated update" ON public.chirp_analysis_shield_codes FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated delete" ON public.chirp_analysis_shield_codes FOR DELETE USING ((auth.uid() IS NOT NULL));

-- chirp_safety_issue_legislation
CREATE POLICY "Chirp Safety Issue Legislation: Public read access" ON public.chirp_safety_issue_legislation FOR SELECT USING (true);
CREATE POLICY "Chirp Safety Issue Legislation: Authenticated insert" ON public.chirp_safety_issue_legislation FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Legislation: Authenticated update" ON public.chirp_safety_issue_legislation FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Legislation: Authenticated delete" ON public.chirp_safety_issue_legislation FOR DELETE USING ((auth.uid() IS NOT NULL));


-- ============================================================
-- STEP 15: Grants for new and recreated tables
-- ============================================================

GRANT ALL ON TABLE public.author_identifiers TO anon;
GRANT ALL ON TABLE public.author_identifiers TO authenticated;
GRANT ALL ON TABLE public.author_identifiers TO service_role;

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

GRANT ALL ON TABLE public.chirp_analysis_shield_codes TO anon;
GRANT ALL ON TABLE public.chirp_analysis_shield_codes TO authenticated;
GRANT ALL ON TABLE public.chirp_analysis_shield_codes TO service_role;

GRANT ALL ON TABLE public.chirp_safety_issue_legislation TO anon;
GRANT ALL ON TABLE public.chirp_safety_issue_legislation TO authenticated;
GRANT ALL ON TABLE public.chirp_safety_issue_legislation TO service_role;
