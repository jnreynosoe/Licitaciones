import pandas as pd
from sqlalchemy import create_engine, text, inspect
import pymysql

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

DB_CONFIG = {
    'host': '192.168.49.79',
    'port': 3307,
    'user': 'BI',
    'password': 'masterkey',
    'database': 'bbddlicitaciones',
    'charset': 'utf8mb4'
}

# ============================================================================
# FUNCIONES
# ============================================================================

def crear_engine():
    """Crea el engine de SQLAlchemy para conectar con MariaDB."""
    connection_string = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset={DB_CONFIG['charset']}"
    )
    engine = create_engine(connection_string, pool_pre_ping=True)
    return engine


def verificar_y_exportar():
    """Verifica los datos en MariaDB y exporta a Parquet."""
    
    print("=" * 80)
    print("VERIFICACIÓN DE DATOS EN MARIADB")
    print("=" * 80)
    
    try:
        # Conectar a la base de datos
        print(f"\n🔌 Conectando a {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
        engine = crear_engine()
        
        with engine.connect() as conn:
            print("✅ Conexión exitosa\n")
            
            # Verificar cada tabla
            tablas = ['pliegos', 'req_pliegos', 'crit_pliegos', 'doc_pliegos']
            
            print("📊 RESUMEN DE TABLAS:")

            inspector = inspect(engine)

            for table in inspector.get_table_names():
                print(table)
            # cursor_aux = conn.cursor()
            # cursor_aux.execute("SHOW TABLES")

            # for (table_name,) in cursor_aux.fetchall():
            #     print(table_name)
            # print()
            print("-" * 80)
            
            for tabla in tablas:
                try:
                    # Contar registros
                    query = text(f"SELECT COUNT(*) as total FROM {tabla}")
                    result = conn.execute(query)
                    total = result.fetchone()[0]
                    print(f"   {tabla:30s}: {total:,} registros")
                except Exception as e:
                    print(f"   {tabla:30s}: ❌ Error - {e}")
            
            print("-" * 80)
            
            # Cargar tabla de pliegos
            print("\n📥 Cargando tabla 'pliegos_general'...")
            df_pliegos = pd.read_sql_table('pliegos', engine)
            
            print(f"✅ Cargados {len(df_pliegos):,} registros")
            
            # Mostrar información de la tabla
            print("\n📋 INFORMACIÓN DE LA TABLA:")
            print("-" * 80)
            print(f"Columnas: {list(df_pliegos.columns)}")
            print(f"Dimensiones: {df_pliegos.shape[0]} filas x {df_pliegos.shape[1]} columnas")
            
            # Mostrar estadísticas por estado
            if 'ESTADO' in df_pliegos.columns:
                print("\n📈 DISTRIBUCIÓN POR ESTADO:")
                print("-" * 80)
                estados = df_pliegos['ESTADO'].value_counts()
                for estado, count in estados.items():
                    print(f"   {estado:40s}: {count:,}")
            
            # Mostrar primeros registros
            print("\n🔍 PRIMEROS 5 REGISTROS:")
            print("-" * 80)
            print(df_pliegos.head().to_string())
            
            # Exportar a Parquet
            print("\n💾 Exportando a Parquet...")
            nombre_archivo = "Pliegos_Prueba.parquet"
            df_pliegos.to_parquet(nombre_archivo, index=False, compression='snappy')
            
            # Verificar archivo creado
            import os
            tamano_mb = os.path.getsize(nombre_archivo) / (1024 * 1024)
            print(f"✅ Archivo creado: {nombre_archivo}")
            print(f"   Tamaño: {tamano_mb:.2f} MB")
            
            # Verificar que se puede leer el Parquet
            print("\n🔄 Verificando archivo Parquet...")
            df_verificacion = pd.read_parquet(nombre_archivo)
            print(f"✅ Verificación exitosa: {len(df_verificacion):,} registros leídos")
            
            # Información adicional útil
            if 'FECHA_PUBLICACION' in df_pliegos.columns:
                print("\n📅 RANGO DE FECHAS DE PUBLICACIÓN:")
                print("-" * 80)
                # Convertir a datetime si es string
                try:
                    df_pliegos['FECHA_PUBLICACION'] = pd.to_datetime(df_pliegos['FECHA_PUBLICACION'], errors='coerce')
                    fecha_min = df_pliegos['FECHA_PUBLICACION'].min()
                    fecha_max = df_pliegos['FECHA_PUBLICACION'].max()
                    print(f"   Desde: {fecha_min}")
                    print(f"   Hasta: {fecha_max}")
                except:
                    print("   No se pudieron convertir las fechas")
            
            # Cerrar conexión
            engine.dispose()
            
        print("\n" + "=" * 80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    verificar_y_exportar()