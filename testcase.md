Finding subject and its related paths that have no hypertension, hyperlipidemia, type 2 diabetes and have a healthy bmi

```select sequence_shotgun.* from response_medical_mastersheet
 select sequence_shotgun.* from response_medical_mastersheet
 inner join response_physiology
 on response_physiology.response_id = response_medical_mastersheet.response_id
 inner join response_metadata
 on response_metadata.response_id = response_medical_mastersheet.response_id
 inner join sequence_shotgun 
 on sequence_shotgun.lab_id = response_metadata.amd_code
 where "Hyperlipidemia/Cholesterol" = 'FALSE'
 and hypertension = 'FALSE'
 and "Type II Diabetes" = 'FALSE'
 and "physiology-bmi-bmi" < 23
```

Finding subjects in the emulsion cohort that act as a control

```/*
 SELECT * from emulsion_clinical_metadata
 inner join emulsion_subject_ind_metadata
 on emulsion_clinical_metadata.subject_id = emulsion_subject_ind_metadata.subject_id
 where flip_algo_name = 'not NAFLD'
 and diabetes_ind = 0 and hypertension_ind = 0
 and dyslipidemia_ind = 0 and bmi_val <23
```

use case for fmt, ftp donor patient matching

```SELECT
  y.gender_cd AS donor_gender,
  y.age_no AS donor_age,
  y.bmi_val AS donor_bmi,
  z.*
 FROM
  (
    SELECT
      a.*,
      b.*
    FROM
      fmt_donor_biomarker a
      INNER JOIN fmt_donor_biomarker_mapping b ON a.sp_cd = b.sp_cd
      AND a.new_id = b.new_id
  ) y
  INNER JOIN (
    SELECT
      complete.fmt_id AS fmt_id,
      ssg.batch AS donor_batch,
      complete.donor_seq_no,
      ssg.kneaddata_fastq AS donor_kneaddata_fastq,
      ssg.stat_csv AS donor_stat_csv,
      ssg.metaphlan_file AS donor_metaphlan_file,
      ssg.pathway_abun AS donor_pathway_abun,
      ssg.ec_abun AS donor_ec_abun,
      complete.kit_id_pre_ftp,
      complete.sequence_number_pre,
      complete.pre_kneaddata_fastq,
      complete.pre_metaphlan_file,
      complete.pre_stat_csv,
      complete.pre_pathway_abun,
      complete.pre_ec_abun,
      complete.kit_id_post_ftp,
      complete.sequence_number_post,
      complete.post_kneaddata_fastq,
      complete.post_metaphlan_file,
      complete.post_stat_csv,
      complete.post_pathway_abun,
      complete.post_ec_abun
    FROM
      sequence_shotgun AS ssg
      INNER JOIN (
        SELECT
          fsm.fmt_id,
          fsm.fmt_prep,
          fsm.sequence_number AS donor_seq_no,
          ftp.*
        FROM
          fmt_sequence_mapping AS fsm
          INNER JOIN (
            SELECT
              d.*,
              e.*
            FROM
              ( -- Pre-FTP section
                SELECT
                  a.kit_id AS kit_id_pre_ftp,
                  a.fmt_prep AS connecting_id_pre,
                  b.kit_id,
                  b.sequence_number AS sequence_number_pre,
                  b.fmt_prep,
                  c.sequence_number,
                  c.kneaddata_fastq AS pre_kneaddata_fastq,
                  c.metaphlan_file AS pre_metaphlan_file,
                  c.stat_csv AS pre_stat_csv,
                  c.pathway_abun AS pre_pathway_abun,
                  c.ec_abun AS pre_ec_abun
                FROM
                  pre_ftp_raw AS a
                  LEFT JOIN ftp_sequence_mapping AS b ON UPPER(a.kit_id) = UPPER(b.kit_id)
                  LEFT JOIN sequence_shotgun AS c ON b.sequence_number = c.sequence_number
                WHERE
                  b.kit_id IS NOT NULL
              ) AS d
              INNER JOIN ( -- Post-FTP section
                SELECT
                  a.kit_id AS kit_id_post_ftp,
                  b.kit_id,
                  a.fmt_prep AS connecting_id_post,
                  b.fmt_prep,
                  b.sequence_number AS sequence_number_post,
                  c.sequence_number,
                  c.kneaddata_fastq AS post_kneaddata_fastq,
                  c.metaphlan_file AS post_metaphlan_file,
                  c.stat_csv AS post_stat_csv,
                  c.pathway_abun AS post_pathway_abun,
                  c.ec_abun AS post_ec_abun
                FROM
                  post_ftp_raw AS a
                  LEFT JOIN ftp_sequence_mapping AS b ON UPPER(a.kit_id) = UPPER(b.kit_id)
                  LEFT JOIN sequence_shotgun AS c ON b.sequence_number = c.sequence_number
                WHERE
                  b.kit_id IS NOT NULL
              ) AS e ON d.connecting_id_pre = e.connecting_id_post
          ) AS ftp ON LEFT(TRIM(ftp.connecting_id_pre), LENGTH(TRIM(ftp.connecting_id_pre)) -2) = fsm.fmt_prep
      ) AS complete ON ssg.sequence_number = complete.donor_seq_no
  ) z ON y.sequence_number = z.donor_seq_no;