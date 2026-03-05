-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.analysis (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  chunk_id uuid,
  analysis_type text,
  content text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT analysis_pkey PRIMARY KEY (id),
  CONSTRAINT analysis_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE CASCADE
);

ALTER TABLE public.analysis ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Analysis: Authenticated delete" ON public.analysis FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Analysis: Authenticated insert" ON public.analysis FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Analysis: Authenticated update" ON public.analysis FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Analysis: Public read access" ON public.analysis FOR SELECT USING (true);

CREATE TABLE public.author_identifiers (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  author_id uuid NOT NULL,
  identifier text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT author_identifiers_pkey PRIMARY KEY (id),
  CONSTRAINT author_identifiers_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id) ON DELETE CASCADE
);

ALTER TABLE public.author_identifiers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Author Identifiers: Authenticated delete" ON public.author_identifiers FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Author Identifiers: Authenticated insert" ON public.author_identifiers FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Author Identifiers: Authenticated update" ON public.author_identifiers FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Author Identifiers: Public read access" ON public.author_identifiers FOR SELECT USING (true);

CREATE TABLE public.authors (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  name text NOT NULL,
  email text,
  phone_number text,
  address text,
  website text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT authors_pkey PRIMARY KEY (id)
);

ALTER TABLE public.authors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authors: Authenticated delete" ON public.authors FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Authors: Authenticated insert" ON public.authors FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Authors: Authenticated update" ON public.authors FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Authors: Public read access" ON public.authors FOR SELECT USING (true);

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

CREATE POLICY "Chirp Analysis Shield Codes: Authenticated delete" ON public.chirp_analysis_shield_codes FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated insert" ON public.chirp_analysis_shield_codes FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated update" ON public.chirp_analysis_shield_codes FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Public read access" ON public.chirp_analysis_shield_codes FOR SELECT USING (true);

CREATE TABLE public.chirp_organisations (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  name text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_organisations_pkey PRIMARY KEY (id)
);

ALTER TABLE public.chirp_organisations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Organisations: Authenticated delete" ON public.chirp_organisations FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Organisations: Authenticated insert" ON public.chirp_organisations FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Organisations: Authenticated update" ON public.chirp_organisations FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Organisations: Public read access" ON public.chirp_organisations FOR SELECT USING (true);

CREATE TABLE public.chirp_recommendations (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  recommendation text NOT NULL,
  is_implemented boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  organisation_id uuid,
  chunk_id uuid,
  is_verified boolean DEFAULT false,
  verified_at timestamp with time zone,
  CONSTRAINT chirp_recommendations_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_recommendations_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE SET NULL,
  CONSTRAINT chirp_recommendations_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.chirp_organisations(id) ON DELETE SET NULL
);

ALTER TABLE public.chirp_recommendations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Recommendations: Authenticated delete" ON public.chirp_recommendations FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Recommendations: Authenticated insert" ON public.chirp_recommendations FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Recommendations: Authenticated update" ON public.chirp_recommendations FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Recommendations: Public read access" ON public.chirp_recommendations FOR SELECT USING (true);

CREATE TABLE public.chirp_report_metadata (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  accident_date date,
  accident_location text,
  severity text,
  loss_of_life integer,
  port_of_origin text,
  destination text,
  accident_type text,
  vessel_type text,
  vessel_name text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  page_count integer,
  pdf_subject text,
  pdf_author text,
  document_id uuid,
  CONSTRAINT chirp_report_metadata_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_report_metadata_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE
);

ALTER TABLE public.chirp_report_metadata ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Report Metadata: Authenticated delete" ON public.chirp_report_metadata FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Report Metadata: Authenticated insert" ON public.chirp_report_metadata FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Report Metadata: Authenticated update" ON public.chirp_report_metadata FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Report Metadata: Public read access" ON public.chirp_report_metadata FOR SELECT USING (true);

CREATE TABLE public.chirp_safety_issue_legislation (
  safety_issue_id uuid NOT NULL,
  legislation_id uuid NOT NULL,
  "extract" text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_safety_issue_legislation_pkey PRIMARY KEY (safety_issue_id, legislation_id),
  CONSTRAINT chirp_safety_issue_legislation_legislation_id_fkey FOREIGN KEY (legislation_id) REFERENCES public.legislation(id) ON DELETE CASCADE,
  CONSTRAINT chirp_safety_issue_legislation_safety_issue_id_fkey FOREIGN KEY (safety_issue_id) REFERENCES public.chirp_safety_issues(id) ON DELETE CASCADE
);

ALTER TABLE public.chirp_safety_issue_legislation ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Safety Issue Legislation: Authenticated delete" ON public.chirp_safety_issue_legislation FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Legislation: Authenticated insert" ON public.chirp_safety_issue_legislation FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Legislation: Authenticated update" ON public.chirp_safety_issue_legislation FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Legislation: Public read access" ON public.chirp_safety_issue_legislation FOR SELECT USING (true);

CREATE TABLE public.chirp_safety_issues (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  name text,
  chunk_id uuid,
  is_verified boolean DEFAULT false,
  verified_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_safety_issues_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_safety_issues_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE SET NULL
);

ALTER TABLE public.chirp_safety_issues ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Safety Issues: Authenticated delete" ON public.chirp_safety_issues FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issues: Authenticated insert" ON public.chirp_safety_issues FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issues: Authenticated update" ON public.chirp_safety_issues FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issues: Public read access" ON public.chirp_safety_issues FOR SELECT USING (true);

CREATE TABLE public.chirp_shield_code_categories (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  name text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_shield_code_categories_pkey PRIMARY KEY (id)
);

ALTER TABLE public.chirp_shield_code_categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Shield Code Categories: Authenticated delete" ON public.chirp_shield_code_categories FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Code Categories: Authenticated insert" ON public.chirp_shield_code_categories FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Code Categories: Authenticated update" ON public.chirp_shield_code_categories FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Code Categories: Public read access" ON public.chirp_shield_code_categories FOR SELECT USING (true);

CREATE TABLE public.chirp_shield_codes (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  code text NOT NULL,
  title text NOT NULL,
  definition text,
  category_id uuid,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_shield_codes_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_shield_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.chirp_shield_code_categories(id) ON DELETE SET NULL
);

ALTER TABLE public.chirp_shield_codes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Shield Codes: Authenticated delete" ON public.chirp_shield_codes FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Codes: Authenticated insert" ON public.chirp_shield_codes FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Codes: Authenticated update" ON public.chirp_shield_codes FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Codes: Public read access" ON public.chirp_shield_codes FOR SELECT USING (true);

CREATE TABLE public.chunk_sentences (
  chunk_id uuid NOT NULL,
  sentence_id uuid NOT NULL,
  "position" integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chunk_sentences_pkey PRIMARY KEY (chunk_id, sentence_id),
  CONSTRAINT chunk_sentences_chunk_id_fkey FOREIGN KEY (chunk_id) REFERENCES public.chunks(id) ON DELETE CASCADE,
  CONSTRAINT chunk_sentences_sentence_id_fkey FOREIGN KEY (sentence_id) REFERENCES public.sentences(id) ON DELETE CASCADE
);

ALTER TABLE public.chunk_sentences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chunk Sentences: Authenticated delete" ON public.chunk_sentences FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunk Sentences: Authenticated insert" ON public.chunk_sentences FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunk Sentences: Authenticated update" ON public.chunk_sentences FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunk Sentences: Public read access" ON public.chunk_sentences FOR SELECT USING (true);

CREATE TABLE public.chunks (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chunks_pkey PRIMARY KEY (id)
);

ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chunks: Authenticated delete" ON public.chunks FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunks: Authenticated insert" ON public.chunks FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunks: Authenticated update" ON public.chunks FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chunks: Public read access" ON public.chunks FOR SELECT USING (true);

CREATE TABLE public.documents (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  title text NOT NULL,
  url text,
  publication_date date,
  filename text,
  hash text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  author_id uuid,
  CONSTRAINT documents_pkey PRIMARY KEY (id),
  CONSTRAINT documents_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id) ON DELETE SET NULL
);

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Documents: Authenticated delete" ON public.documents FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Documents: Authenticated insert" ON public.documents FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Documents: Authenticated update" ON public.documents FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Documents: Public read access" ON public.documents FOR SELECT USING (true);

CREATE TABLE public.legislation (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  name text NOT NULL,
  reference text,
  jurisdiction text,
  url text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT legislation_pkey PRIMARY KEY (id)
);

ALTER TABLE public.legislation ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Legislation: Authenticated delete" ON public.legislation FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Legislation: Authenticated insert" ON public.legislation FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Legislation: Authenticated update" ON public.legislation FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Legislation: Public read access" ON public.legislation FOR SELECT USING (true);

CREATE TABLE public.sentences (
  id uuid DEFAULT gen_random_uuid() NOT NULL,
  text text NOT NULL,
  text_type text NOT NULL,
  "position" integer,
  relevance_score integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  document_id uuid,
  CONSTRAINT sentences_pkey PRIMARY KEY (id),
  CONSTRAINT sentences_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE
);

ALTER TABLE public.sentences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Sentences: Authenticated delete" ON public.sentences FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Sentences: Authenticated insert" ON public.sentences FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Sentences: Authenticated update" ON public.sentences FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Sentences: Public read access" ON public.sentences FOR SELECT USING (true);
