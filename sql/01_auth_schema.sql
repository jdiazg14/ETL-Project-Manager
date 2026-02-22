-- 1. Tabla de Roles (Perfiles)
CREATE TABLE role (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL, -- 'admin', 'analista', 'operador'
    description VARCHAR(255)
);


-- 2. Tabla de Usuarios (Relacionada con Roles)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES role(id)
);

-- 3. Tabla de Logs de Proyectos ETL
CREATE TABLE etl_project_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    user_id INT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- INSERTAR ROLES INICIALES
INSERT INTO role (name, description) VALUES 
('admin', 'Acceso total y configuración'),
('analista', 'Solo carga y visualización de datos');