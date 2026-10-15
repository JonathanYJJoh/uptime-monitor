-- Undo migration 000001. Drop in reverse order: child tables before the table they reference.
DROP TABLE IF EXISTS incidents;
DROP TABLE IF EXISTS checks;
DROP TABLE IF EXISTS monitors;
