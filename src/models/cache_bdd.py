import sqlite3
import hashlib
from datetime import datetime

class CacheResumenes:
    def __init__(self, db_path="cache_resumenes.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Crea la tabla si no existe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_documento TEXT UNIQUE NOT NULL,
                pliego_id TEXT,
                url_pdf TEXT,
                resumen TEXT NOT NULL,
                modelo_usado TEXT,
                fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()
    
    def _generar_hash(self, texto):
        """Genera hash único del documento para identificarlo"""
        return hashlib.sha256(texto.encode('utf-8')).hexdigest()
    
    def obtener_resumen(self, texto_pdf, pliego_id=None):
        """Intenta recuperar resumen existente"""
        hash_doc = self._generar_hash(texto_pdf)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT resumen, modelo_usado, fecha_generacion, version 
            FROM resumenes 
            WHERE hash_documento = ? 
            ORDER BY version DESC LIMIT 1
        """, (hash_doc,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                "resumen": resultado[0],
                "modelo": resultado[1],
                "fecha": resultado[2],
                "version": resultado[3],
                "desde_cache": True
            }
        return None
    
    def guardar_resumen(self, texto_pdf, resumen, modelo="deepseek-r1:14b", pliego_id=None, url_pdf=None):
        """Guarda un nuevo resumen o versión"""
        hash_doc = self._generar_hash(texto_pdf)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute("SELECT MAX(version) FROM resumenes WHERE hash_documento = ?", (hash_doc,))
        max_version = cursor.fetchone()[0]
        nueva_version = (max_version or 0) + 1
        
        cursor.execute("""
            INSERT INTO resumenes (hash_documento, pliego_id, url_pdf, resumen, modelo_usado, version)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (hash_doc, pliego_id, url_pdf, resumen, modelo, nueva_version))
        
        conn.commit()
        conn.close()
        
        return nueva_version
    
    def listar_versiones(self, texto_pdf):
        """Muestra todas las versiones generadas de un documento"""
        hash_doc = self._generar_hash(texto_pdf)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT version, modelo_usado, fecha_generacion, substr(resumen, 1, 100) || '...' as preview
            FROM resumenes 
            WHERE hash_documento = ?
            ORDER BY version DESC
        """, (hash_doc,))
        
        versiones = cursor.fetchall()
        conn.close()
        return versiones