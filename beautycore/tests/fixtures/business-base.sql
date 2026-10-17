-- Isolated test database only. Snapshot of the pre-feature schema; no production connection.
CREATE TYPE user_role AS ENUM('admin','stylist','client');
CREATE TYPE style_type AS ENUM('hair','nail');
CREATE TYPE appointment_status AS ENUM('pending','confirmed','completed','cancelled');
CREATE TYPE product_status AS ENUM('in_stock','low_stock','out_of_stock');
CREATE TABLE users(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),email varchar(255) UNIQUE NOT NULL,name varchar(255) NOT NULL,password_hash text NOT NULL,role user_role NOT NULL DEFAULT 'client',avatar text,created_at timestamp NOT NULL DEFAULT now());
CREATE TABLE client_profiles(user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,hair_preferences text,nail_preferences text,style_history jsonb,created_at timestamp NOT NULL DEFAULT now());
CREATE TABLE appointments(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),client_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,stylist_id uuid REFERENCES users(id) ON DELETE SET NULL,service_name varchar(255) NOT NULL,service_type varchar(100) NOT NULL,appointment_date timestamp NOT NULL,status appointment_status NOT NULL DEFAULT 'pending',total_price integer,notes text,created_at timestamp NOT NULL DEFAULT now());
CREATE TABLE ai_generations(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),client_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,source_image_url text NOT NULL,prompt_text text NOT NULL,generated_image_url text,style_type style_type NOT NULL,analysis_result jsonb,created_at timestamp NOT NULL DEFAULT now());
CREATE TABLE inventory(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),product_name varchar(255) NOT NULL,category varchar(100) NOT NULL,current_stock integer NOT NULL DEFAULT 0,minimum_threshold integer NOT NULL DEFAULT 10,unit_price integer,status product_status NOT NULL DEFAULT 'in_stock',last_restocked timestamp,created_at timestamp NOT NULL DEFAULT now());
