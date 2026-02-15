
# ETL-Project-Manager

## Resumen
Este proyecto es un gestor ETL minimalista para cargas de archivos y registro de logs, con autenticación y control de roles. El esquema de base de datos está gestionado externamente en PostgreSQL y solo se manejan las tablas `role`, `user` y `etl_project_logs`.

## Arquitectura
- **Backend:** Flask + SQLAlchemy
- **Autenticación:** Flask-Login
- **Gestión de variables:** `.env` (requiere `DATABASE_URL` y `SECRET_KEY`)
- **Modelos:**
	- `role`: roles de usuario (admin, analista, etc.)
	- `user`: usuarios autenticados, vinculados a un rol
	- `etl_project_logs`: logs de cargas de archivos
- **Carga de archivos:** Los archivos se procesan en memoria (pandas DataFrame), no se almacenan en la base de datos.

## Configuración rápida
1. Crea y configura tu base de datos PostgreSQL según `schema.sql`.
2. Crea un archivo `.env` con la variable `DATABASE_URL` y tu `SECRET_KEY`.
3. Instala dependencias:
	 ```bash
	 pip install -r requirements.txt
	 ```
4. Ejecuta la app:
	 ```bash
	 python run.py
	 ```

## Comandos útiles
- Crear usuario admin:
	```bash
	flask create_admin
	```

## Notas
- El proyecto no crea ni modifica el esquema de la base de datos automáticamente.
- Solo se gestionan usuarios, roles y logs de carga.
- Para agregar roles iniciales, usa el script SQL proporcionado.
