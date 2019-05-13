import json
from pymongo import MongoClient


class Database:
    """
    Carga datos de DataFrames de pandas en la base de datos.
    """

    def __init__(self, database, *args, **kwargs):
        self.client = MongoClient(*args, **kwargs)
        self.database = self.client[database]

    def carga_datos(self, df, coleccion):
        """
        Carga los datos de un dataframe en la base de datos.
        """
        db = self.database[coleccion]

        # Borra la colección
        db.drop()

        # Convierte el DataFrame a json
        df_json = json.loads(df.T.to_json()).values()

        # Inserta los datos en el documetno de la base de datos
        db.insert_many(df_json)
        
    
    def lee_datos(self, coleccion):
        
        tabla = self.database[coleccion]
        
        return tabla

    def close(self):
        """
        Cierra la conexión con la base de datos.
        """
        self.client.close()
