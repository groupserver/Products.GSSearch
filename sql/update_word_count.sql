-- Update script for the word_count table
BEGIN;
-- Yes, we do intend to delete all the records from
--   the word_count table; it is faster this way.
DELETE FROM word_count;

-- Aggregate the data from the topic_word_count table.
INSERT INTO word_count SELECT word, SUM(count) 
FROM topic_word_count GROUP BY word;
COMMIT;

