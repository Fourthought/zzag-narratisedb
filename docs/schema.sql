-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.authors (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name text NOT NULL,
  email text,
  phone_number text,
  address text,
  website text,
  CONSTRAINT authors_pkey PRIMARY KEY (id)
);
CREATE TABLE public.chirp_analysis (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  sentence_id bigint,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_analysis_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_analysis_sentence_id_fkey FOREIGN KEY (sentence_id) REFERENCES public.sentences(id)
);
CREATE TABLE public.chirp_analysis_shield_codes (
  sentence_id bigint NOT NULL,
  shield_code_id bigint NOT NULL,
  CONSTRAINT chirp_analysis_shield_codes_pkey PRIMARY KEY (sentence_id, shield_code_id),
  CONSTRAINT chirp_analysis_shield_codes_sentence_id_fkey FOREIGN KEY (sentence_id) REFERENCES public.sentences(id),
  CONSTRAINT chirp_analysis_shield_codes_shield_code_id_fkey FOREIGN KEY (shield_code_id) REFERENCES public.chirp_shield_codes(id)
);
CREATE TABLE public.chirp_organisations (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_organisations_pkey PRIMARY KEY (id)
);
CREATE TABLE public.chirp_recommendations (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  document_id bigint,
  recommendation text NOT NULL,
  organisation_id bigint,
  is_implemented boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT chirp_recommendations_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_recommendations_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id),
  CONSTRAINT chirp_recommendations_organisation_id_fkey FOREIGN KEY (organisation_id) REFERENCES public.chirp_organisations(id)
);
CREATE TABLE public.chirp_report_metadata (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
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
  CONSTRAINT chirp_report_metadata_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id)
);
CREATE TABLE public.chirp_safety_issue_sentences (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  safety_issue_id bigint,
  sentence_id bigint,
  CONSTRAINT chirp_safety_issue_sentences_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_safety_issue_sentences_safety_issue_id_fkey FOREIGN KEY (safety_issue_id) REFERENCES public.chirp_safety_issues(id),
  CONSTRAINT chirp_safety_issue_sentences_sentence_id_fkey FOREIGN KEY (sentence_id) REFERENCES public.sentences(id)
);
CREATE TABLE public.chirp_safety_issues (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  document_id bigint,
  name text,
  CONSTRAINT chirp_safety_issues_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_safety_issues_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id)
);
CREATE TABLE public.chirp_shield_code_categories (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name text NOT NULL,
  CONSTRAINT chirp_shield_code_categories_pkey PRIMARY KEY (id)
);
CREATE TABLE public.chirp_shield_codes (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  code text NOT NULL,
  category_id bigint,
  title text NOT NULL,
  definition text,
  CONSTRAINT chirp_shield_codes_pkey PRIMARY KEY (id),
  CONSTRAINT chirp_shield_codes_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.chirp_shield_code_categories(id)
);
CREATE TABLE public.documents (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  title text NOT NULL,
  url text,
  publication_date date,
  filename text,
  hash text NOT NULL,
  author_id bigint,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT documents_pkey PRIMARY KEY (id),
  CONSTRAINT documents_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id)
);
CREATE TABLE public.sections (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  document_id bigint,
  position integer,
  CONSTRAINT sections_pkey PRIMARY KEY (id),
  CONSTRAINT sections_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id)
);
CREATE TABLE public.sentences (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  text text NOT NULL,
  text_type text NOT NULL,
  position integer,
  document_id bigint,
  section_id bigint,
  relevance_score integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT sentences_pkey PRIMARY KEY (id),
  CONSTRAINT sentences_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id),
  CONSTRAINT sentences_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id)
);
