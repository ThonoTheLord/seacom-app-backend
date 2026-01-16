-- This script fixes the broken audit_report_changes trigger in Supabase
-- The trigger has a bug in its PL/pgSQL code where 'key' is undefined

-- Option 1: Drop the broken trigger entirely (if you don't need audit logging)
-- Drop trigger first, then function
DROP TRIGGER IF EXISTS trg_audit_report_changes ON reports;
DROP FUNCTION IF EXISTS audit_report_changes() CASCADE;


-- Option 2 (ALTERNATIVE): Fix the trigger to work correctly
-- Uncomment the code below to use this instead of Option 1

/*
CREATE OR REPLACE FUNCTION audit_report_changes() 
RETURNS TRIGGER AS $$
DECLARE
  v_changed_fields jsonb;
BEGIN
  -- Build a JSON object of changed fields with old and new values
  -- Only for JSONB fields like 'data'
  IF OLD.data IS DISTINCT FROM NEW.data THEN
    v_changed_fields := jsonb_build_object(
      'data', jsonb_build_object(
        'old', OLD.data,
        'new', NEW.data
      )
    );
  ELSE
    v_changed_fields := '{}'::jsonb;
  END IF;

  -- You could log this to an audit table here if needed
  -- INSERT INTO audit_log (table_name, record_id, changes) 
  -- VALUES ('reports', NEW.id, v_changed_fields);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_report_changes
  AFTER UPDATE ON reports
  FOR EACH ROW
  EXECUTE FUNCTION audit_report_changes();
*/
