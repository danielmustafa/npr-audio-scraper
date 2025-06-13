WITH random_gender AS (
  SELECT gender
  FROM correspondents
  ORDER BY random()
  limit 1
),
random_correspondents AS (
  SELECT id AS correspondent_id
  FROM correspondents
  WHERE gender = (select gender from random_gender)
  ORDER BY random()
  LIMIT 10
),
random_segments AS (
  SELECT DISTINCT ON (corr.id)
    corr.id AS correct_correspondent_id,
    corr.fullname AS correct_correspondent_name,
    audio.url AS audio_url,
    asegs.start_time_sec,
    asegs.end_time_sec
  FROM 
    random_correspondents rc
    JOIN correspondents corr ON corr.id = rc.correspondent_id
    JOIN audio ON audio.correspondent_id = corr.id
    JOIN audio_segments asegs ON audio.id = asegs.audio_id
  ORDER BY corr.id, random()
),
question_with_choices AS (
  SELECT 
    rs.*,
    (
      SELECT json_agg(json_build_object('id', id, 'fullname', fullname))
      FROM (
        SELECT id, fullname FROM (
          -- Select 3 random incorrect correspondents
          SELECT c.id, c.fullname
          FROM correspondents c
          WHERE c.id != rs.correct_correspondent_id
          ORDER BY random()
          LIMIT 3
        ) distractors

        UNION ALL

        -- Include the correct correspondent
        SELECT rs.correct_correspondent_id, rs.correct_correspondent_name
      ) all_choices
      ORDER BY random()
    ) AS multiple_choice
  FROM random_segments rs
)
SELECT * FROM question_with_choices;