-- Drop the existing overly broad trigger
DROP TRIGGER IF EXISTS prevent_transaction_update;

-- Create surgical trigger that only protects truly immutable fields
CREATE TRIGGER prevent_immutable_field_update
    BEFORE UPDATE ON transactions
    WHEN
        NEW.amount_paise != OLD.amount_paise OR
        NEW.date != OLD.date OR
        NEW.description != OLD.description OR
        NEW.account_id != OLD.account_id OR
        (NEW.hash_signature != OLD.hash_signature
         AND OLD.hash_signature IS NOT NULL)
    BEGIN
        SELECT RAISE(ABORT,
            'Cannot modify immutable transaction fields: amount, date, description, account_id');
    END;