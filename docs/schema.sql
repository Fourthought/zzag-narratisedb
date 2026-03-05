-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.authors (
  id bigint NOT NULL,
  name text NOT NULL,
  email text,
  phone_number text,
  address text,
  website text,
  CONSTRAINT authors_pkey PRIMARY KEY (id)
);

ALTER TABLE public.authors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authors: Authenticated delete" ON public.authors FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Authors: Authenticated insert" ON public.authors FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Authors: Authenticated update" ON public.authors FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Authors: Public read access" ON public.authors FOR SELECT USING (true);

CREATE TABLE public.chirp_analysis (
  id bigint NOT NULL,
  sentence_id bigint,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_analysis_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_analysis_sentence_id_fkey FOREIGN KEY (sentence_id) REFERENCES public.sentences(id) ON DELETE CASCADE
);

ALTER TABLE public.chirp_analysis ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Analysis: Authenticated delete" ON public.chirp_analysis FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis: Authenticated insert" ON public.chirp_analysis FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis: Authenticated update" ON public.chirp_analysis FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis: Public read access" ON public.chirp_analysis FOR SELECT USING (true);

CREATE TABLE public.chirp_analysis_shield_codes (
  sentence_id bigint NOT NULL,
  shield_code_id bigint NOT NULL,
  CONSTRAINT chirp_analysis_shield_codes_pkey PRIMARY KEY (sentence_id, shield_code_id),
  CONSTRAINT chirp_analysis_shield_codes_sentence_id_fkey FOREIGN KEY (sentence_id) REFERENCES public.sentences(id) ON DELETE CASCADE,
  CONSTRAINT chirp_analysis_shield_codes_shield_code_id_fkey FOREIGN KEY (shield_code_id) REFERENCES public.chirp_shield_codes(id) ON DELETE CASCADE
);

ALTER TABLE public.chirp_analysis_shield_codes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Analysis Shield Codes: Authenticated delete" ON public.chirp_analysis_shield_codes FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Authenticated insert" ON public.chirp_analysis_shield_codes FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Analysis Shield Codes: Public read access" ON public.chirp_analysis_shield_codes FOR SELECT USING (true);

CREATE TABLE public.chirp_organisations (
  id bigint NOT NULL,
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
  id bigint NOT NULL,
  document_id bigint,
  recommendation text NOT NULL,
  organisation_id bigint,
  is_implemented boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_recommendations_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_recommendations_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE,
  CONSTRAINT chirp_recommendations_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.chirp_organisations(id) ON DELETE SET NULL
);

ALTER TABLE public.chirp_recommendations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Recommendations: Authenticated delete" ON public.chirp_recommendations FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Recommendations: Authenticated insert" ON public.chirp_recommendations FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Recommendations: Authenticated update" ON public.chirp_recommendations FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Recommendations: Public read access" ON public.chirp_recommendations FOR SELECT USING (true);

CREATE TABLE public.chirp_report_metadata (
  id bigint NOT NULL,
  document_id bigint,
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
  CONSTRAINT chirp_report_metadata_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_report_metadata_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE
);

ALTER TABLE public.chirp_report_metadata ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Report Metadata: Authenticated delete" ON public.chirp_report_metadata FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Report Metadata: Authenticated insert" ON public.chirp_report_metadata FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Report Metadata: Authenticated update" ON public.chirp_report_metadata FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Report Metadata: Public read access" ON public.chirp_report_metadata FOR SELECT USING (true);

CREATE TABLE public.chirp_safety_issue_sentences (
  id bigint NOT NULL,
  safety_issue_id bigint,
  sentence_id bigint,
  CONSTRAINT chirp_safety_issue_sentences_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_safety_issue_sentences_safety_issue_id_fkey FOREIGN KEY (safety_issue_id) REFERENCES public.chirp_safety_issues(id) ON DELETE CASCADE,
  CONSTRAINT chirp_safety_issue_sentences_sentence_id_fkey FOREIGN KEY (sentence_id) REFERENCES public.sentences(id) ON DELETE CASCADE
);

ALTER TABLE public.chirp_safety_issue_sentences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Safety Issue Sentences: Authenticated delete" ON public.chirp_safety_issue_sentences FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Sentences: Authenticated insert" ON public.chirp_safety_issue_sentences FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issue Sentences: Public read access" ON public.chirp_safety_issue_sentences FOR SELECT USING (true);

CREATE TABLE public.chirp_safety_issues (
  id bigint NOT NULL,
  document_id bigint,
  name text,
  CONSTRAINT chirp_safety_issues_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_safety_issues_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE
);

ALTER TABLE public.chirp_safety_issues ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Safety Issues: Authenticated delete" ON public.chirp_safety_issues FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issues: Authenticated insert" ON public.chirp_safety_issues FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issues: Authenticated update" ON public.chirp_safety_issues FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Safety Issues: Public read access" ON public.chirp_safety_issues FOR SELECT USING (true);

CREATE TABLE public.chirp_shield_code_categories (
  id bigint NOT NULL,
  name text NOT NULL,
  CONSTRAINT chirp_shield_code_categories_pkey PRIMARY KEY (id)
);

ALTER TABLE public.chirp_shield_code_categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Shield Code Categories: Authenticated delete" ON public.chirp_shield_code_categories FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Code Categories: Authenticated insert" ON public.chirp_shield_code_categories FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Code Categories: Authenticated update" ON public.chirp_shield_code_categories FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Code Categories: Public read access" ON public.chirp_shield_code_categories FOR SELECT USING (true);

CREATE TABLE public.chirp_shield_codes (
  id bigint NOT NULL,
  code text NOT NULL,
  category_id bigint,
  title text NOT NULL,
  definition text,
  CONSTRAINT chirp_shield_codes_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_shield_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.chirp_shield_code_categories(id) ON DELETE SET NULL
);

ALTER TABLE public.chirp_shield_codes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Chirp Shield Codes: Authenticated delete" ON public.chirp_shield_codes FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Codes: Authenticated insert" ON public.chirp_shield_codes FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Codes: Authenticated update" ON public.chirp_shield_codes FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Chirp Shield Codes: Public read access" ON public.chirp_shield_codes FOR SELECT USING (true);

CREATE TABLE public.documents (
  id bigint NOT NULL,
  title text NOT NULL,
  url text,
  publication_date date,
  filename text,
  hash text NOT NULL,
  author_id bigint,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT documents_pkey PRIMARY KEY (id),
  CONSTRAINT documents_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id) ON DELETE SET NULL
);

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Documents: Authenticated delete" ON public.documents FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Documents: Authenticated insert" ON public.documents FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Documents: Authenticated update" ON public.documents FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Documents: Public read access" ON public.documents FOR SELECT USING (true);

CREATE TABLE public.sections (
  id bigint NOT NULL,
  name text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  document_id bigint,
  "position" integer,
  CONSTRAINT sections_pkey PRIMARY KEY (id),
  CONSTRAINT sections_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id)
);

ALTER TABLE public.sections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Sections: Authenticated delete" ON public.sections FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Sections: Authenticated insert" ON public.sections FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Sections: Authenticated update" ON public.sections FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Sections: Public read access" ON public.sections FOR SELECT USING (true);

CREATE TABLE public.sentences (
  id bigint NOT NULL,
  text text NOT NULL,
  text_type text NOT NULL,
  "position" integer,
  document_id bigint,
  section_id bigint,
  relevance_score integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT sentences_pkey PRIMARY KEY (id),
  CONSTRAINT sentences_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE,
  CONSTRAINT sentences_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id) ON DELETE SET NULL
);

ALTER TABLE public.sentences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Sentences: Authenticated delete" ON public.sentences FOR DELETE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Sentences: Authenticated insert" ON public.sentences FOR INSERT WITH CHECK ((auth.uid() IS NOT NULL));
CREATE POLICY "Sentences: Authenticated update" ON public.sentences FOR UPDATE USING ((auth.uid() IS NOT NULL));
CREATE POLICY "Sentences: Public read access" ON public.sentences FOR SELECT USING (true);
