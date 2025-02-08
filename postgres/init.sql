-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Create Korean dictionary and configuration
CREATE TEXT SEARCH CONFIGURATION korean (COPY = simple);

-- Set weights for different fields
ALTER TEXT SEARCH CONFIGURATION korean
    ALTER MAPPING FOR asciiword, asciihword, hword, hword_part, word, hword_asciipart
    WITH simple;

-- Function to create search vector update trigger
CREATE OR REPLACE FUNCTION create_post_search_trigger() RETURNS void AS $$
BEGIN
    -- Check if the table exists
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'blog_post') THEN
        -- Create or replace the trigger function
        CREATE OR REPLACE FUNCTION post_search_vector_update() RETURNS trigger AS $trigger$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('korean', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('korean', COALESCE(NEW.content, '')), 'B');
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;

        -- Drop the trigger if it exists and create it
        DROP TRIGGER IF EXISTS post_search_vector_update ON blog_post;
        CREATE TRIGGER post_search_vector_update
            BEFORE INSERT OR UPDATE OF title, content
            ON blog_post
            FOR EACH ROW
            EXECUTE FUNCTION post_search_vector_update();
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Execute the function (it will only create the trigger if the table exists)
SELECT create_post_search_trigger(); 