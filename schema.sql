-- 1. Tabla de Roles (Perfiles)
CREATE TABLE role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL, -- 'admin', 'analista', 'operador'
    description VARCHAR(255)
);

-- 2. Tabla de Usuarios (Relacionada con Roles)
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES role(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla de Logs de Proyectos ETL
CREATE TABLE etl_project_logs (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    user_id INTEGER REFERENCES "user"(id),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INSERTAR ROLES INICIALES
INSERT INTO role (name, description) VALUES 
('admin', 'Acceso total y configuración'),
('analista', 'Solo carga y visualización de datos');