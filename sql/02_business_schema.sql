-- 1. CREACIÓN DE LA BASE DE DATOS
CREATE DATABASE IF NOT EXISTS etl_ventas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE etl_ventas_db;

-- 2. TABLA DEPARTAMENTO (Maestro DANE)
CREATE TABLE Dim_Departamento (
    id_departamento VARCHAR(2) PRIMARY KEY, 
    nombre_depto VARCHAR(100) NOT NULL
) ENGINE=InnoDB;


-- 3. TABLA MUNICIPIO (Maestro DANE asociado a Departamento)
CREATE TABLE Dim_Municipio (
    id_municipio VARCHAR(5) PRIMARY KEY,
    id_departamento VARCHAR(2) NOT NULL,
    nombre_municipio VARCHAR(100) NOT NULL,
    CONSTRAINT fk_municipio_depto 
        FOREIGN KEY (id_departamento) 
        REFERENCES Dim_Departamento (id_departamento) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 4. DIMENSIÓN TIEMPO (Detalle diario para análisis de sorteos)
CREATE TABLE Dim_Tiempo (
    id_tiempo INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE UNIQUE NOT NULL,
    anio INT NOT NULL,
    mes INT NOT NULL,
    dia INT NOT NULL,
    dia_semana_nombre VARCHAR(20), -- Lunes, Martes...
    dia_semana_num INT,            -- 1 (Lunes) a 7 (Domingo)
    es_fin_semana BOOLEAN,
    trimestre INT
) ENGINE=InnoDB;

-- 5. DIMENSIÓN DISTRIBUIDOR (Jerarquía integrada: Sucursal -> Razón Social)
CREATE TABLE Dim_Distribuidor (
    id_distribuidor INT AUTO_INCREMENT PRIMARY KEY,
    codigo_sucursal VARCHAR(20) UNIQUE NOT NULL, -- El código de 6 dígitos del archivo
    nombre_sucursal VARCHAR(255) NOT NULL,
    nit VARCHAR(20) NOT NULL,                    -- Agrupador para Razón Social
    razon_social VARCHAR(255),
    cupo_asignado DECIMAL(15,2) DEFAULT 0.00,
    grupo VARCHAR(50),                           -- GRUPO A, B, C...
    id_municipio VARCHAR(5),                            -- Ubicación física de la sucursal
    activo BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_dist_municipio FOREIGN KEY (id_municipio) 
        REFERENCES Dim_Municipio(id_municipio)
) ENGINE=InnoDB;

-- 6. TABLA DE HECHOS: VENTAS (Movimientos diarios)
CREATE TABLE Fact_Ventas (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    id_tiempo INT NOT NULL,
    id_distribuidor INT NOT NULL,
    id_municipio VARCHAR(5) NOT NULL,      -- Para reportes geográficos rápidos
    sorteo INT NOT NULL,
    cantidad_despachada INT DEFAULT 0,
    cantidad_devuelta INT DEFAULT 0,
    cantidad_vendida INT DEFAULT 0,
    bruto_despacho DECIMAL(15,2) DEFAULT 0.00,
    bruto_devuelto DECIMAL(15,2) DEFAULT 0.00,
    bruto_vendido DECIMAL(15,2) DEFAULT 0.00,
    neto_vendido DECIMAL(15,2) DEFAULT 0.00,
    porcentaje_comision DECIMAL(5,2),
    
    CONSTRAINT fk_fac_tiempo FOREIGN KEY (id_tiempo) REFERENCES Dim_Tiempo(id_tiempo),
    CONSTRAINT fk_fac_dist FOREIGN KEY (id_distribuidor) REFERENCES Dim_Distribuidor(id_distribuidor),
    CONSTRAINT fk_fac_muni FOREIGN KEY (id_municipio) REFERENCES Dim_Municipio(id_municipio)
) ENGINE=InnoDB;