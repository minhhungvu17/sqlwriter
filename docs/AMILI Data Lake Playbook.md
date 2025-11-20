# AMILI Data Lake Playbook

#### I. Introduction

The purpose of the AMILI Data Lake Playbook is to provide a comprehensive and authoritative reference for all activities, standards, and processes related to the Data Lake at AMILI.

This document is intended to ensure that any stakeholder — whether an internal team member, a new joiner, or an external collaborator — can readily obtain a clear understanding of the current state, ongoing initiatives, and established practices governing the Data Lake.

- Active and historical projects and datasets ingested into the Data Lake.
-  Metadata standards, naming conventions, and classword harmonisation.
- Survey governance procedures and demographic data harmonisation.
- End-to-end data ingestion workflows across Lab, Data Engineering, Data Science, and Analytics teams.
- Governance structures, including access controls, data classification, and quality assurance.
- Supporting resources such as SOPs, templates, and pipeline specifications.

#### II. Data Lake Architecture

As-Is (Current State)

- Data Science access: Sequencing files are being accessed directly from S3, outside of a controlled data ingestion pipeline.
- Metadata: Maintained separately in Postgres & Excel files, leading to fragmentation between raw data (S3) and metadata (Postgres & Excel).
- Pipeline gaps: Lack of a unified framework for validation, standardisation, and harmonisation across datasets.
- Amili Analytics: AA team often receives outputs post-hoc, sometimes after manual cleaning in Excel, reducing reproducibility.
- Lab Team: Maps and preprocesses their own data before passing it to Data Engineering, resulting in heavily transformed datasets that enter the pipeline without consistent governance or traceability.

Over-processed data limits the ability to perform deeper analysis. To enable scalability and advanced insights, consistent standardization must be enforced, with Lakehouse serving as the single source of truth.

#### III. Metadata Standards

- Metadata for all tables stored in the database will follow the prescribed structure:metadata_dictionary_template_extended.xlsx
- All datasets must be harmonised prior to ingestion into the database, adhering to the standardised flow.
- The Data Dictionary will be sourced either from the source system owner or the Data Science team.
- Harmonisation will be applied once the Data Dictionary is retrieved. Field names must:
  - End with an approved classword, assigned appropriately.
  - Be shortened to fit within the 63-character limit using acronyms and abbreviations from the approved list.
  - Be written in lowercase, with underscores as separators.

#### IV. Data Sources (SSOT)

- Sequencing data from s3 (16s, shotgun) - Amazon Web Services

- Refer to amili-global-archive s3 bucket

  Metadata for different datasets (from multiple teams) - Lab team and AA team

• Survey data from Qualtrics - Login | Qualtrics

• LILAC db datasets

5. Survey Data SOP


AS-IS

• Current survey questions are not validated, resulting in multiple variations of

questions capturing the same information.

• A Survey Data SOP has been introduced, starting with the Activation Survey.

TO-BE

• A Master Question Bank will be maintained as the single source of truth.

• An approval workflow will govern the addition of any new questions to ensure

consistency and standardisation.

6. Data Ingestion Workflow


AS-IS

• Manual cleansing: Data is cleaned ad hoc by Data Engineering, often row-by-row.

• No raw retention: Raw source files do not centrally persist (no immutable landing zone).

• Missing audit fields: Tables lack standard audit columns (e.g., created_by, created_at,

updated_by, updated_at, source_file, load_id).

• Fragmented codebase: Transformation scripts are split between individual local

machines and GitHub, with inconsistent environments.

• No observability: Logs are not retained; there is no centralized run history, error

handling, or alerting.

• Limited lineage & reproducibility: End-to-end traceability is weak, making reruns and

investigations difficult.

TO-BE

• S3 as Drop Zone: All raw files are first deposited into S3.

• AWS Glue: Picks up the files from S3, performs the required transformations, and loads

the cleaned/structured data into Postgres.

• Data Science Access: The Data Science team queries relevant tables from Postgres (as

part of the data lake) to run through their pipelines (ideally hosted on SageMaker).

• Output Handling: Pipeline outputs can be written back to Postgres if needed for

downstream visualization (e.g., dashboards, BI tools).

7. Datasets within AMILI


AMD (AMILI Microbiome Donor) Project

The AMILI Microbiome Donor (AMD) initiative is one of our largest and ongoing projects.

Under the AMD umbrella, multiple surveys and questionnaires are conducted to capture a

wide range of demographic, lifestyle, and health-related information from donors. This

information is then leveraged in conjunction with sequencing data to better understand

how the gut microbiome varies across different categories of people.

Surveys Under AMD

• AMILI Lifestyle and Wellness Questionnaire

• #PoopSavesLives 2022 (Version 3)

• Microbiome Donor (Version 2, 2021)

• #PoopSavesLives (Version 4)

• Microsite – Age and BMI (Updated 23 May 2020 Copy)

These surveys provide rich datasets on demographics, medical history, and lifestyle

attributes that can be integrated with sequencing data for comprehensive analysis.

Additional Questionnaires Completed by Donors

To complement the above surveys, donors may also complete validated clinical and lifestyle

questionnaires, such as:

• FFQ – Food Frequency Questionnaire

• GPAQ – Global Physical Activity Questionnaire

• K10 – Kessler Psychological Distress Scale

• PSS – Perceived Stress Scale

• PSQI – Pittsburgh Sleep Quality Index

• CCMQ – Constitution in Chinese Medicine Questionnaire

Together, these surveys and questionnaires form a multi-dimensional dataset that supports

deeper insights into the interplay between lifestyle, clinical factors, and the gut microbiome.

Surveys under FMT

• FMT Pre-Screener Question

• Pre CI Questionnaire

• Clinician Interview Questionnaire

• Combined FSQ Pre CI

\* for the list of surveys parked under each project kindly refer to xxx

Lab ID Format from Qualtrics Response.xlsx

8. Datasets with external parties -(public domain too) - completion of


Healthy Cohort

• 1000MY - Malaysian/Singaporean healthy adults reference cohort for gut-microbiome

baselines.

• Remedy - Healthy volunteers trialling regional ingredients to discover pre/post-biotics.

• DYNAMO (controls arm) - Non-diabetic controls within the diabetes-complication

study.

• SG70 - 3 000 middle-aged Singaporeans tracked 10-15 y for healthy-ageing signals.

• SingHeart - 912 clinically characterised, cardio-metabolically “normal” Singaporeans.

• Microbiome NUS-AMILI - General healthy population samples for reference database.

• SSHSPH Microbiota Vault - Rural/indigenous healthy donors preserved for biodiversity.

Prebiotics / Probiotics

• 1000MY - Baseline diet-microbiome links for probiotic target discovery.

• Yeo’s - 42-day chrysanthemum-tea intervention tracking probiotic-like effects.

• Kale Stalk / Dole - Two-week kale-rich diet and green-banana/pineapple fibre trials.

• WhatIF / Amway - Ingredient blends screened for microbiome modulation.

• DYNAMO - Explores probiotic potential for diabetes-related complications.

• REMEDY - Screens regional foods for prebiotic/postbiotic candidates.

• Colon T2 - Looks at probiotic signatures protective against colorectal cancer.

• SG70 (nutrition sub-studies) - Long-term diet and supplement exposure.

Food R&D

• Yeo’s - Industry partner studying functional beverage impact on the gut.

• Kale Stalk / Dole - Product-development tests on fruit- and vegetable-based fibres.

• WhatIF / Amway, Amway millet drink, Sempera, Sago Grub, WellSpent - In-vitro

screens of novel ingredients (honey, mushroom, insect protein, nut milk, etc.).

• REMEDY - End-to-end pipeline from ingredient discovery to metabolic read-outs.

• DYNAMO - Food R&D angle on dietary patterns in diabetes cohorts.

4 Weight Management

• HELMS (weight-loss arm) - Maternal weight-loss trajectories from pre-conception

onward.

• EMULSION - Bariatric-surgery patients for liver/weight interplay.

• Clean-Label Plant-Based Meals - 3-week partial-feeding study on plant-based menus. -

double check

• HELMS weight-management sub-data - Stool + clinical data across pregnancy/post-

partum.

Liver & Metabolic Disease

• ELEGANCE - Microbiome/metabolome signals leading to hepatocellular carcinoma. - FFQ

• EMULSION - Liver-fat and metabolic markers in a weight-management cohort.

• HELMS - Maternal metabolic health and later NCD risk.

• DYNAMO - Microbiome links to diabetic retinopathy & nephropathy.

• SGH-KID - Oxalobacter prevalence in kidney-stone formers.

• STATIN - Gut signatures associated with statin response and SAM risk.

• CGH GMM - Microbiome shifts before and after gall-bladder removal.

• SingHeart - Early metabolic-syndrome markers in a healthy cohort. - FFQ

• NUH CABG (LEAP trial) - AKG intervention on post-surgery inflammation & microbiome.

FMT Donor Matching / Therapeutics

• AMD / FMT - Core donor-screening pipeline and biobank.

• MOMA - Identifies exceptional responders to cancer therapy as potential donors.

• FMT IBS - Capsules supplied for irritable-bowel-syndrome intervention.

• FMT Alopecia - Pilot FMT for alopecia areata hair-regrowth.

• FMT Donor Programme (screening surveys + labs) - End-to-end eligibility workflow.

Healthy Aging

• SG70 - Decade-long multi-omics ageing trajectory.

• 1000MY - Age-stratified healthy Asian reference.

• NUS LONGER (rapamycin) - 12-week mTOR-modulation trial and microbiome response.

• NUS CEDIRA (multivitamin) - 12-month supplement-ageing RCT with stool sampling.

• NUS ABLE (Ca-AKG) - Six-month ageing-biomarker trial with gut profiling.

• HALEON - Perimenopausal women’s microbiome during hormonal transition.

• SG70, LOI (maternal-child allergy origin) - Lifespan immuno-interactome.

Women’s & Baby’s Health

• HELMS - Pre-conception to post-partum lifestyle intervention for mother & child.

• LOI (Immuno-Interactome) - Microbiome-immune development in early life.

• HELMS weight-loss & metabolic sub-studies feed into women’s health analytics.

ILETIS

Cancer Research

• ELEGANCE - Early biomarkers for liver-cancer development.

• Colon T2 - 5 000-subject cohort for microbiome + miRNA early-CRC detection.

• Neomycin-CRC - Antibiotic-microbiome dynamics around CRC surgery & SSI risk.

• MOMA - Stool profiles of cancer-treatment responders vs. non-responders.

• NCCS-Immunotherapy - Longitudinal gut profiles of immuno-oncology patients.

• NCCS-IOToxDatabase - Biomarkers predicting IO response and toxicity.

• Prostate Cancer NCCS - Microbiome correlates of prostate-cancer progression.

• CGH GMM - Post-cholecystectomy microbiome as cancer-risk model.

Link: Data Catalogue.xlsx (reference for further information)

9. Data Classification


Data

Tier

Stage Time

Estimate

Problem

Raw Locate

complete

data

~2-7 days Survey data has multiple iterations, sitting in different

locations. Local files are everywhere ranging from DS, Lab

Team and AA.

Bronze Populate

with

metadata*

~1-2

weeks

Metadata can be generated from multiple pipelines, with

disparate versions on personal devices (not on AWS).

Pipeline version information may be unavailable.

Silver Add raw file

source to

metadata

~3-7 days Linking samples to taxa and abundance is challenging due to

lost context from team turnover.

Gold Organise and

clean survey

data

~1.5-3

weeks

Scores are inconsistently collected due to variations in

survey design. For example, the GPAQ may contain only 16

questions, but is sometimes stored as 18 because of

differences in question sets.

10. Data Collection (To-Be Implemented) Process Flow


• Start with EMULSION as the initial project.

• Data Science team and Product Manager / External Source System Owner upload data

into the S3 bucket and provide the corresponding data dictionary (refer to template

below)Data Dictionary

Template.xlsx

• Data Science PIC completes the data requirements form.Data Requirements

Form.docx

• Data Engineer, Data Product Manager, and Data Science PIC jointly review and sign off

the requirements form.

• Data Engineer begins data cleaning and processing.

• Data Science team performs verification, with the Data Product Manager overseeing

the process.

• Once data is cleaned, ingested, and verified in the data lake, the Data Science team

can begin using it for analysis.

** Within the Data Requirements Form we will be collecting the key users tapping on those

tables, which allows us to maintain RBAC roles for multiple teams in the future

(Lab,DS,DE,AA,PM)

** PII vs non PII data handling (To-Be Discussed)

** Workflow of schema changes

11. Data Engineering Process Flow


• Receive dataset from source system.

• Harmonize fields to comply with naming standards:

o Field names must end with an approved classword.

o Field names must not exceed 63 characters.

o Use only approved acronyms and abbreviations.

• Review harmonized field names with the Data Science team for validation.

• Once approved, proceed with ingestion into the data lake.List of approved

classwords.xlsxAcronyms &

Abbreviations.xlsxData Standards and

governance.docx

12. Analytics & Self-Service



1. How DS Pipelines Connect (Silver/Gold Layer)


• Provide a SageMaker (or equivalent) integration where DS pipelines can directly read

from the Silver/Gold layer tables.

• Silver layer should expose standardized schemas (post-harmonization) for easy model

training and feature engineering.

• Include metadata tags (dataset owner, last refresh date, harmonization status) in the

portal so DS knows what’s trustworthy.

• DS team can launch containerized notebooks (Jupyter/SageMaker Studio) directly from

the portal, already pre-authenticated to the lakehouse.

• Optionally allow API endpoints for DS to hook external tools (RStudio, VSCode,

Databricks if needed).

2. How AA Teams Consume (Gold Layer → Tableau/Power BI)


• Gold layer datasets exposed as curated, business-ready views (with clear naming

conventions + descriptions).

• Portal should have a dataset catalog (think mini Data Dictionary) so AA teams know

which table to use for what.

• Direct connectors (ODBC/JDBC or Tableau/Power BI certified connectors) to gold layer

tables.

• Add “one-click copy connection string” feature so AA teams can self-serve connections

into visualization tools.

• Provide version history / refresh frequency for each gold table so AA doesn’t pull stale

data.

3. Pre-FMA AI Query Tool Usage Guidelines


• Integrated AI assistant in the portal to query Pre-FMA datasets (structured + PubMed

ingestion).

• Guidelines to include:

o Input format: plain English questions → AI generates SQL / harmonized outputs.

o Scope: Pre-FMA only (not production EMR or regulated datasets).

o Validation: AI outputs must be reviewed by DS before being shared externally.

o Logging: All queries are logged in the portal for reproducibility & governance.

• Potential to integrate with LangChain / RAG architecture so queries can reference

metadata tables and public literature simultaneously.

13. Monitoring & Maintenance


\- Logging & auditing

\- Data quality metrics (completeness, freshness, accuracy)

\- Incident response SOP (pipeline failure, corrupted files, missing data)