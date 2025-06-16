with random_correspondents AS (
  SELECT id AS correspondent_id
  FROM correspondents
  ORDER BY random()
  LIMIT 10
),
random_segments AS (
  SELECT DISTINCT ON (corr.id)
    corr.id AS correct_correspondent_id,
    corr.fullname AS correct_correspondent_name,
	corr.gender AS correct_correspondent_gender,
    asegs.public_url AS audio_url
  FROM 
    random_correspondents rc
    JOIN correspondents corr ON corr.id = rc.correspondent_id
    JOIN audio ON audio.correspondent_id = corr.id
    JOIN audio_segments asegs ON audio.id = asegs.audio_id
  ORDER BY corr.id, random()
),
question_with_options AS (
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
		  AND c.gender = rs.correct_correspondent_gender
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
SELECT json_agg(row_to_json(payload)) FROM 
(select
	correct_correspondent_id correspondent_id,
	correct_correspondent_name correspondent_name,
	audio_url,
	multiple_choice options
	from question_with_options
) payload