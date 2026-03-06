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


-- 5.1. TABLA: GRUPO DE DISTRIBUIDORES
CREATE TABLE Dim_GrupoDistribuidor (
    id_grupo INT AUTO_INCREMENT PRIMARY KEY,
    nit VARCHAR(15) UNIQUE NULL,  -- permite nulos (nsi no se conoce el NIT)
    nombre_grupo VARCHAR(100) NOT NULL UNIQUE,
    plan VARCHAR(15),
    activo BOOLEAN DEFAULT 1
) ENGINE=InnoDB;

-- 5.2. DIMENSIÓN DISTRIBUIDOR (Sucursal -> Grupo)
CREATE TABLE Dim_Distribuidor (
    id_distribuidor INT AUTO_INCREMENT PRIMARY KEY,
    codigo_distribuidor VARCHAR(20) UNIQUE NOT NULL,
    nombre_distribuidor VARCHAR(255) NOT NULL,
    cupo_asignado DECIMAL(15,2) DEFAULT 0.00,
    id_municipio VARCHAR(5),
    activo BOOLEAN DEFAULT 1,
    id_grupo INT NULL,
    CONSTRAINT fk_dist_municipio FOREIGN KEY (id_municipio) REFERENCES Dim_Municipio(id_municipio),
    CONSTRAINT fk_dist_grupo FOREIGN KEY (id_grupo) REFERENCES Dim_GrupoDistribuidor(id_grupo)
) ENGINE=InnoDB;

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