-- Replace earlier placeholder hashes with valid bcrypt demo credentials.
UPDATE app_users SET hashed_password = '$2b$12$ug0GbmCtlhFDk9JEGOWD0ujC3BogvQhOsPcxyTnXRLSN/U8kxypoG'
WHERE email = 'demo@thinkfive.ai';
UPDATE app_users SET hashed_password = '$2b$12$NafccG65kpW7LzK9Y/F08uqYhrdsHYuHkru6KMDGD5LUdFN9ku6bW'
WHERE email = 'analyst@thinkfive.ai';
UPDATE app_users SET hashed_password = '$2b$12$fzzS7LTiuNTwxZGiwMgGFOUBU0xrpp5scSccZoAaz86NfCuporMZe'
WHERE email = 'supervisor@thinkfive.ai';
UPDATE app_users SET hashed_password = '$2b$12$SegobeOZAaIqwRa7RacoGOR.EMgPiwCMVnz5jo5AZLfYZ6r17tRzy'
WHERE email = 'admin@thinkfive.ai';

INSERT INTO backend_schema_migrations (migration_id, description, checksum)
VALUES ('006_demo_passwords', 'Valid bcrypt hashes for demo users', 'v1')
ON CONFLICT (migration_id) DO NOTHING;
