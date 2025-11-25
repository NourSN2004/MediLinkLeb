-- Create test users directly in database
-- Password: Password123! (hashed with Django's PBKDF2)

-- Doctor user
INSERT INTO auth_users (username, email, password, first_name, last_name, role, phone_number, is_active, is_staff, is_superuser, date_joined)
VALUES ('doctor1', 'doctor1@medilink.com', 'pbkdf2_sha256$600000$1234567890abcdef$abcdefghijklmnopqrstuvwxyz1234567890ABCD==', 'John', 'Smith', 'doctor', '+96170123456', true, false, false, NOW());

-- Patient user
INSERT INTO auth_users (username, email, password, first_name, last_name, role, phone_number, is_active, is_staff, is_superuser, date_joined)
VALUES ('patient1', 'patient1@medilink.com', 'pbkdf2_sha256$600000$1234567890abcdef$abcdefghijklmnopqrstuvwxyz1234567890ABCD==', 'Jane', 'Doe', 'patient', '+96170234567', true, false, false, NOW());

-- Pharmacy user
INSERT INTO auth_users (username, email, password, first_name, last_name, role, phone_number, is_active, is_staff, is_superuser, date_joined)
VALUES ('pharmacy1', 'pharmacy1@medilink.com', 'pbkdf2_sha256$600000$1234567890abcdef$abcdefghijklmnopqrstuvwxyz1234567890ABCD==', 'City', 'Pharmacy', 'pharmacy', '+96170345678', true, false, false, NOW());

-- Note: These passwords are hashed but won't work for login
-- You need to use the signup form to create properly hashed passwords
