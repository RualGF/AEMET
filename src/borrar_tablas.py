from sqlalchemy import text
from conectar import conexion_a_bd as conectar


# Conexión

engine = conectar()

def borrar_por_lotes(nombre_tabla: str, tam_lote: int = 10000):
    """
        Función para borrado por lotes.
        La tabla de datos meteorológicos es demasiado grande para borrarla del tirón
    """
    with engine.begin() as conn:
        total_borradas = 0
        while True:
            result = conn.execute(text(f"DELETE FROM {nombre_tabla} LIMIT {tam_lote}"))
            borradas = result.rowcount
            total_borradas += borradas
            print(f"🧹 Borradas {borradas} filas...")
            if borradas == 0:
                break
        print(f"✅ Total filas borradas de '{nombre_tabla}': {total_borradas}")

if __name__ == "__main__":
    borrar_por_lotes("datos_meteorologicos", tam_lote = 10000)
