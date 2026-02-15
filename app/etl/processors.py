"""
Procesador de datos para ETL.
Utiliza Pandas para limpiar, validar y transformar datos.
"""
import os
import pandas as pd
import io
from werkzeug.utils import secure_filename


class DataProcessor:
    """Clase para procesar datos de archivos cargados."""
    
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    MAX_PREVIEW_ROWS = 10
    
    @staticmethod
    def allowed_file(filename):
        """Verificar si la extensión del archivo está permitida."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in DataProcessor.ALLOWED_EXTENSIONS
    
    @staticmethod
    def read_file(file_path):
        """
        Leer archivo (CSV o Excel).
        Retorna un DataFrame de Pandas.
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower().strip('.')
            
            if file_extension == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f'Formato de archivo no soportado: {file_extension}')
            
            return df, None
        except Exception as e:
            return None, f'Error al leer el archivo: {str(e)}'
    
    @staticmethod
    def clean_data(df):
        """
        Realizar limpieza inicial de datos.
        - Eliminar filas completamente vacías
        - Limpiar nombres de columnas
        - Detectar valores nulos
        """
        errors = []
        warnings = []
        
        try:
            # Guardar información original
            original_shape = df.shape
            
            # Eliminar filas completamente vacías
            df = df.dropna(how='all')
            
            # Limpiar nombres de columnas
            # Convertir a minúsculas, eliminar espacios, reemplazar caracteres especiales
            df.columns = [
                col.strip()
                .lower()
                .replace(' ', '_')
                .replace('-', '_')
                .replace('(', '')
                .replace(')', '')
                for col in df.columns
            ]
            
            # Eliminar columnas duplicadas (si las hay)
            df = df.loc[:, ~df.columns.duplicated()]
            
            final_shape = df.shape
            
            # Registrar cambios
            removed_rows = original_shape[0] - final_shape[0]
            if removed_rows > 0:
                warnings.append(f'Se eliminaron {removed_rows} filas vacías')
            
            # Detectar valores nulos
            null_counts = df.isnull().sum()
            null_columns = null_counts[null_counts > 0]
            
            if len(null_columns) > 0:
                for col, count in null_columns.items():
                    pct = (count / len(df)) * 100
                    warnings.append(f'Columna "{col}": {count} valores nulos ({pct:.1f}%)')
            
            # Validar que haya datos
            if final_shape[0] == 0:
                errors.append('El archivo no contiene datos válidos')
            
            if final_shape[1] == 0:
                errors.append('El archivo no contiene columnas')
            
            return df, warnings, errors
        
        except Exception as e:
            errors.append(f'Error durante la limpieza: {str(e)}')
            return None, warnings, errors
    
    @staticmethod
    def get_data_preview(df, max_rows=None):
        """
        Obtener vista previa de los datos.
        Retorna información sobre las columnas y una muestra de filas.
        """
        if df is None or df.empty:
            return None, 'No hay datos para mostrar'
        
        if max_rows is None:
            max_rows = DataProcessor.MAX_PREVIEW_ROWS
        
        try:
            preview_data = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': [],
                'sample_data': []
            }
            
            # Información de columnas
            for col in df.columns:
                dtype_str = str(df[col].dtype)
                non_null = df[col].notna().sum()
                null_count = df[col].isna().sum()
                
                preview_data['columns'].append({
                    'name': col,
                    'type': dtype_str,
                    'non_null': int(non_null),
                    'null': int(null_count)
                })
            
            # Muestra de datos (primeras N filas)
            sample_rows = df.head(max_rows)
            
            # Convertir a diccionarios para la plantilla
            for idx, row in sample_rows.iterrows():
                row_dict = {}
                for col in df.columns:
                    value = row[col]
                    # Manejar valores especiales
                    if pd.isna(value):
                        row_dict[col] = 'NULL'
                    elif isinstance(value, (int, float)):
                        row_dict[col] = f'{value:.2f}' if isinstance(value, float) else str(value)
                    else:
                        row_dict[col] = str(value)[:50]  # Limitar longitud
                
                preview_data['sample_data'].append(row_dict)
            
            return preview_data, None
        
        except Exception as e:
            return None, f'Error al generar vista previa: {str(e)}'
    
    @staticmethod
    def validate_data(df):
        """
        Validaciones específicas del negocio.
        Retorna lista de validaciones exitosas y de errores.
        """
        validations = []
        errors = []
        
        try:
            # Ejemplo: Validaciones personalizadas según el modelo de datos
            # Estas son ejemplos que se ajustarán según las necesidades
            
            # Validar si existen columnas críticas (ejemplos)
            # critical_columns = ['fecha', 'cantidad', 'monto']
            # for col in critical_columns:
            #     if col in df.columns:
            #         validations.append(f'✓ Columna crítica encontrada: {col}')
            #     else:
            #         errors.append(f'✗ Falta columna crítica: {col}')
            
            # Validar tipos de datos
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64']:
                    validations.append(f'✓ Columna "{col}" es numérica')
                elif df[col].dtype == 'object':
                    validations.append(f'✓ Columna "{col}" contiene texto')
            
            return validations, errors
        
        except Exception as e:
            errors.append(f'Error en validación: {str(e)}')
            return validations, errors
    
    @staticmethod
    def get_statistics(df):
        """
        Obtener estadísticas básicas del dataframe.
        """
        try:
            stats = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'memory_usage': df.memory_usage(deep=True).sum() / 1024**2,  # MB
                'dtypes': df.dtypes.value_counts().to_dict(),
                'null_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            }
            return stats
        except Exception as e:
            return None
