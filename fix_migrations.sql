-- Fix migration history inconsistency
-- Run this in your MySQL database: mysql -u your_user -p beii_new < fix_migrations.sql

-- Delete the problematic admin migration entry
DELETE FROM django_migrations WHERE app='admin' AND name='0001_initial';

-- Add it back with correct dependency order (after users)
-- This will be re-added when you run migrate again
