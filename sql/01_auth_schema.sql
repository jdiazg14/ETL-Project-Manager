-- 1. CREACIÓN DE LA BASE DE DATOS
CREATE DATABASE IF NOT EXISTS etl_ventas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE etl_ventas_db;

-- 2. Tabla de Roles (Perfiles)
CREATE TABLE role (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL, -- 'admin', 'analista', 'operador'
    description VARCHAR(255)
);


-- 3. Tabla de Usuarios (Relacionada con Roles)
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

-- 4. Tabla de Logs de Proyectos ETL
CREATE TABLE etl_project_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    fecha_carga_archivo DATETIME NOT NULL,
    registros_afectados INT NOT NULL DEFAULT 0,
    user_id INT,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 5. INSERTAR ROLES INICIALES
INSERT INTO role (name, description) VALUES 
('admin', 'Acceso total y configuración'),
('analista', 'Solo carga y visualización de datos');