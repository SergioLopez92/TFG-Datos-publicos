import pandas as pd
from fuentes.Fuente import Fuente
from fuentes.ine import Ine
from fuentes.irpf2015 import Irpf2015
from fuentes import Database
from config import Config as config
from fuentes.ine import InePoblacion
from fuentes.mir import MirEleccionesGenerales
from fuentes.turismo import Turismo
from sklearn.ensemble import RandomForestRegressor
from sklearn import tree
from sklearn.model_selection import cross_val_predict
from sklearn.linear_model import LinearRegression
import numpy as np
import math
import os
import difflib



import numpy as np
import matplotlib.pyplot as plt

class Sklearn(Fuente):
    
    def __init__(self):        
        descripcion = ''
        super().__init__('sklearn', 'predicciones', descripcion)
        
        
    def obtenerDatosIne(self):
        
        dfo = self.lee_dataframe(InePoblacion)
        #print(dfo)
        df = dfo[['Provincia', 'Municipio', 'Ambos sexos-Total-Total', 'Codigo Municipio', 'Codigo Provincia']].copy()
        
        df['Ambos sexos-Total-Menores de 16 años'] = dfo['Ambos sexos-Total-Menores de 16 años'] / dfo['Ambos sexos-Total-Total']
        df['Ambos sexos-Total-De 16 a 64 años'] = dfo['Ambos sexos-Total-De 16 a 64 años'] / dfo['Ambos sexos-Total-Total']
        df['Ambos sexos-Total-De 65 y más años'] = dfo['Ambos sexos-Total-De 65 y más años'] / dfo['Ambos sexos-Total-Total']
        df['Ambos sexos-extranjeros-Total'] = dfo['Ambos sexos-extranjeros-Total'] / dfo['Ambos sexos-Total-Total']
        df['Ambos sexos-extranjeros-Menores de 16 años'] = dfo['Ambos sexos-extranjeros-Menores de 16 años'] / dfo['Ambos sexos-Total-Total']
        df['Ambos sexos-extranjeros-De 16 a 64 años'] = dfo['Ambos sexos-extranjeros-De 16 a 64 años'] / dfo['Ambos sexos-Total-Total']
        df['Ambos sexos-extranjeros-De 65 y más años'] = dfo['Ambos sexos-extranjeros-De 65 y más años'] / dfo['Ambos sexos-Total-Total']
        df['Hombres-Total-Total'] = dfo['Hombres-Total-Total'] / dfo['Ambos sexos-Total-Total']
        df['Hombres-Total-Menores de 16 años'] = dfo['Hombres-Total-Menores de 16 años'] / dfo['Ambos sexos-Total-Total']
        df['Hombres-Total-De 16 a 64 años'] = dfo['Hombres-Total-De 16 a 64 años'] / dfo['Ambos sexos-Total-Total']
        df['Hombres-Total-De 65 y más años'] = dfo['Hombres-Total-De 65 y más años'] / dfo['Ambos sexos-Total-Total']
        df['Hombres-extranjeros-Total'] = dfo['Hombres-extranjeros-Total'] / dfo['Ambos sexos-Total-Total']
        df['Hombres-extranjeros-Menores de 16 años'] = dfo['Hombres-extranjeros-Menores de 16 años'] / dfo['Ambos sexos-Total-Total']
        df['Hombres-extranjeros-De 16 a 64 años'] = dfo['Hombres-extranjeros-De 16 a 64 años'] / dfo['Ambos sexos-Total-Total']
        df['Hombres-extranjeros-De 65 y más años'] = dfo['Hombres-extranjeros-De 65 y más años'] / dfo['Ambos sexos-Total-Total']
        
        return df
        
    def obtenerDatosMir(self):
        
        dfo = self.lee_dataframe(MirEleccionesGenerales)
        
        df = dfo[dfo.Año == 2015]
        df = df.dropna(axis = 'columns')
        
        df['Codigo Municipio'] = df['Codigo Provincia'].astype(str).str.zfill(2) + df['Codigo Municipio'].astype(str).str.zfill(3)
        df = df.drop(['_id', 'Nombre de Municipio', 'Nombre de Provincia', 'Codigo Provincia'], axis = 1)
        
        columnas_principio = ['Año', 'Codigo Municipio', 'Nombre de Comunidad', 'Número de mesas', 'Población',
                       'Total censo electoral', 'Total votantes', 'Votos a candidaturas',
                       'Votos en blanco', 'Votos nulos', 'Votos válidos']
        #Reordenar columnas
        df = df[[c for c in columnas_principio if c in df] + [c for c in df if c not in columnas_principio]]
        
        #print(df.columns.values)
        return df
    
    def obtenerDatosGini(self):
        dfo = self.lee_dataframe(Irpf2015)
        
        df = dfo[['Codigo Municipio', 'Gini despues imp', 'Renta despues imp']]
        df = df.drop(df[df['Codigo Municipio'] == '00000'].index, axis = 0)
        return df
    
    def obtenerDatosTurismo(self):
        dfo = self.lee_dataframe(Turismo)
        df = dfo.drop(['Codigo Provincia', 'Comunidad Autónoma', 'Municipio', 'Provincia', '_id'], axis = 1)
        
        return df
       
    def lee_dataframe(self, fuente):
        db = Database.Database(
            database=config.MONGO_DBNAME,
            host=config.MONGO_HOST,
            port=config.MONGO_PORT,
            username=config.MONGO_USERNAME,
            password=config.MONGO_PASSWORD,
            authSource=config.MONGO_DBNAME
        )
        coleccion = fuente().coleccion()
        df = db.lee_datos(coleccion)
        df = pd.DataFrame(list(df.find()))        
        return df
    
    def buscaSimilares(self, muniDF, porEncontrar, encontrados, delitosDF):
        sinEncontrar = list()
        #me quedo unicamente con los que aun no han sido encontrados
        muniDF = muniDF[~muniDF['Municipio'].isin(encontrados)]
        print(porEncontrar)
        for e in porEncontrar:
            #me quedo con los de la misma provincia
            aux = muniDF[muniDF['CodProv'] == e[2]]
            nombresMuni = aux['Municipio'].tolist()
            similares = difflib.get_close_matches(e[1], nombresMuni, n=10 )
            print(e[1], similares)
            num = int(input())
            if num >= 0:
                index = delitosDF[delitosDF['Nombre'] == e[1]].index.values
                #Cambio el nombre para que coincidan
                delitosDF.loc[index, 'Nombre'] = similares[num]
            else:
                sinEncontrar.append(e)
            
            
        dir = os.path.dirname(__file__)
        url = os.path.join(dir, 'datos\\para_predecir.csv')
        delitosDF.to_csv(url, sep=';', encoding = "ISO-8859-1")
            
    
    
    def procesaCodMunicipios(self):
        dir = os.path.dirname(__file__)

        url = os.path.join(dir, 'datos\para_predecir.csv')
        urlMuni = os.path.join(dir, 'datos\Municipios.csv')
        delitosDF = pd.read_csv(url, sep=';', header=0, encoding = "ISO-8859-1")
        #delitosDF.columns = ['Codigo Municipio', 'Nombre', 'Clase']
        muniDF = pd.read_csv(urlMuni, sep=';', header=0, encoding = "ISO-8859-1")
        delitosNom = delitosDF['Nombre'].tolist()

        '''
        #usado para quitar el codigo de municipio delante del nombre la primera vez
        #(ver documentacion)
        delitosNom = delitosDF['Nombre'].str.split('-', 1).tolist()
        #normalizar la primera vez
        delitosNom = [x[1].upper() for x in delitosNom]
        delitosNom = [Turismo.normalize(self, x) for x in delitosNom]
        '''
        
        delitosNom = [x.upper() for x in delitosNom]
        delitosNom = [Turismo.normalize(self, x) for x in delitosNom]

        #delitosDF['Nombre'] = delitosNom
        muniNom = muniDF['Municipio'].tolist()
        muniNom = [x.upper() for x in muniNom]
        muniNom = [Turismo.normalize(self, x) for x in muniNom]
        
        #Para quedarme con el primer nombre en caso de tener (valido para la primera vez)
        #delitosNom = [x.split('/',1)[0] for x in delitosNom]
        for i in range(len(delitosNom)):
            if ',' in delitosNom[i]:
                articulo = delitosNom[i].split(',', 1)[1]
                articulo = articulo[1:]
                articulo = '(' + articulo + ')'
                delitosNom[i] = delitosNom[i].split(',',1)[0] + ' ' + articulo
        
        delitosDF['Nombre'] = delitosNom
        delitosDF['Codigo Municipio'] = delitosDF['Codigo Municipio'].astype(str).str.zfill(5)
        codigosProvincia = delitosDF['Codigo Municipio'].tolist()
        codigosProvincia = [x[0:2] for x in codigosProvincia]
        delitosDF['CodProv'] = codigosProvincia
        
        muniDF['Municipio'] = muniNom
        muniDF['Código'] = muniDF['Código'].astype(str).str.zfill(5)
        codigosProvincia = muniDF['Código'].tolist()
        codigosProvincia = [x[0:2] for x in codigosProvincia]
        muniDF['CodProv'] = codigosProvincia
        
        #codigosNuevos = list()
        porEncontrar = list()
        encontrados = list()


        codigos_a_cambiar =[0] * len(muniDF['Código'].tolist())
        for i in range (len(delitosDF)):
            #print('...', i)
            muniDF_acotado = muniDF[muniDF['CodProv'] == delitosDF['CodProv'][i]]
            municipioBuscado = muniDF_acotado[muniDF_acotado['Municipio'] == delitosDF['Nombre'][i]]
        
            #municipioBuscado = municipioBuscado.reset_index()
            #print(municipioBuscado)
            if len(municipioBuscado) != 1:
                if len(municipioBuscado) > 1:
                    index = municipioBuscado.index.values
                    encontrados.append(municipioBuscado['Municipio'].tolist()[0])
                    for j in index:
                        codigos_a_cambiar[j] = delitosDF['Codigo Municipio'][i]
                else:
                    porEncontrar.append([delitosDF['Codigo Municipio'][i], delitosDF['Nombre'][i], delitosDF['CodProv'][i]])
            else:
                index = municipioBuscado.index.values[0]
                #print(codigos_a_cambiar[index])
                codigos_a_cambiar[index] = delitosDF['Codigo Municipio'][i]
                encontrados.append(municipioBuscado['Municipio'].tolist()[0])
                #print(codigos_a_cambiar[index])
                #print('...')
            
        #print(len(porEncontrar))
        #print(porEncontrar)
        muniDF['Codigo_Mapa'] = codigos_a_cambiar
        muniDF = muniDF[['Comunidad Autónoma', 'Provincia', 'Municipio', 'Código', 'CodProv', 'Codigo_Mapa']]
        dir = os.path.dirname(__file__)
        url = os.path.join(dir, 'datos\\Municipios.csv')
        muniDF.to_csv(url, sep=';', encoding = "ISO-8859-1")
        #self.buscaSimilares(muniDF, porEncontrar, encontrados, delitosDF)
        
        return porEncontrar
    def carga(self):
        porEncontrar = self.procesaCodMunicipios()
        #Me quedo unicamente con el codigo del municipio no encontrado
        for i in range(len(porEncontrar)):
            porEncontrar[i] = porEncontrar[i][0]
        df_Ine = self.obtenerDatosIne()
        df_Mir = self.obtenerDatosMir()
        df_Gini = self.obtenerDatosGini() 
        df_Turismo = self.obtenerDatosTurismo()
        
        enero16 ={ # Modificado, a las coaliciones les doy la media aritmetica
        "PP": 8.28,
        "PSOE": 4.49,
        "PODEMOS": 2.26,
        'IU-UPeC': 2.27,  #sOLO iu
        "PODEMOS-COM": 2.42, # media de Podemos, compromis 
        "C's": 6.65,
        "EN COMÚ": 2.73, # En comu Podems
        "ERC-CATSI": 3.01, #Solo ERC
        "DL": 6.34,    #Democràcia i Llibertat
        "EAJ-PNV": 5.97,
        "EH Bildu": 2.92,
        "PODEMOS-En": 2.32,#Media podemos en marea
        "CCa-PNC": 5.96 #CC
    }

        
        df_Mir = df_Mir.apply(lambda x: self.procesa_municipio(x,enero16),axis=1)
        
        df = pd.merge(df_Ine, df_Mir, on='Codigo Municipio')
        df = pd.merge(df, df_Gini, on='Codigo Municipio')
        
        df = pd.merge(df, df_Turismo, on='Codigo Municipio')

        
        regr = RandomForestRegressor()
        
        dir = os.path.dirname(__file__)
        url = os.path.join(dir, 'datos\para_predecir.csv')
        
        delitos = pd.read_csv(url, sep=';', header=0, encoding = "ISO-8859-1")
        #delitos.columns = ['Codigo Municipio', 'Nombre', 'Clase']
        delitos['Codigo Municipio'] = delitos['Codigo Municipio'].astype(str).str.zfill(5)
        for e in porEncontrar:
            delitos = delitos.drop(delitos[delitos['Codigo Municipio'] == e].index, axis = 0)
        #df = df.drop(df[df.score < 50].index)
        delitos = delitos.drop(['Nombre'], axis = 1)
        
        df_train = pd.merge(df, delitos, on='Codigo Municipio')
       
        #Desordeno las filas de forma aleatoria
        df_train = df_train.sample(frac=1).reset_index(drop=True) 

        train_data = df_train.drop(["Provincia", "Municipio", "Codigo Municipio", "Codigo Provincia", "Nombre de Comunidad", "Clase"], axis=1)
        mio = train_data
        train_data = train_data.values
        target_data = df_train["Clase"].values
        
        #regr = regr.fit(train_data, target_data)
        print('cross_val_predict')
        pred = cross_val_predict(regr, train_data, target_data, cv=10)
        
        regr.fit(train_data, target_data)
        importances = regr.feature_importances_
        
        cont=0
        for e in mio.columns:
            print(cont, e)
            cont += 1
            
        #print(importances)
        
        
        
        
        
        
        
        #print(pred[-20:-1])  
        #print(target_data[-20:-1])     
        df_train['Prediccion'] = pred
        df_train['Error'] = (df_train['Prediccion'] - df_train['Clase']).abs()
        
        errorMedio = df_train['Error'].mean()
        mediaDel = target_data.mean()
        print(errorMedio)
        #print(df_train.head(5))                        
        
        print(df_train['Error'].min())
        
        
        
        std = np.std([tree.feature_importances_ for tree in regr.estimators_],
             axis=0)
        indices = np.argsort(importances)[::-1]
        
        # Print the feature ranking
        print("Feature ranking:")
        
        for f in range(train_data.shape[1]):
            print("%d. feature %d (%f)" % (f + 1, indices[f], importances[indices[f]]))
        
        # Plot the feature importances of the regr
        plt.figure()
        plt.title("Feature importances")
        plt.bar(range(train_data.shape[1]), importances[indices],
               color="r", yerr=std[indices], align="center")
        plt.xticks(range(train_data.shape[1]), indices)
        plt.xlim([-1, train_data.shape[1]])
        plt.show()
        
        
        df_train.rename(columns={'Clase':'Delitos', 'Prediccion':'Delitos Predichos'}, inplace=True)
        
        
        #probar con delito por habitante
        #time.sleep(20)
        return df_train
    


    def weighted_avg_and_std(self, values, weights):

        average = np.average(values, weights=weights)
        # Fast and numerically precise:
        variance = np.average((values-average)**2, weights=weights)
        return (average, math.sqrt(variance))
    
    
    def procesa_municipio(self, municipioDF, partido_escala):
        
        values_dict ={}
        
        
        primer_partido_idx = 11
                   
        comunidad = municipioDF["Nombre de Comunidad"]
        #provinciaC = municipioDF["Código de Provincia"]
        #provincia = municipioDF["Nombre de Provincia"]
        municipioC = municipioDF["Codigo Municipio"]
        #municipioN = municipioDF["Nombre de Municipio"]
        
        total = int(municipioDF["Total censo electoral"])
        votos = int(municipioDF["Total votantes"])
        nulos = int(municipioDF["Votos en blanco"])
        blancos = int(municipioDF["Votos nulos"])
        a_candidaturas = int(municipioDF["Votos a candidaturas"])
        
        a_candidaturas_mayoritarias = 0
        partidos = municipioDF[primer_partido_idx:].index
        for partido in partidos:
            escala = partido_escala.get(partido)
            if escala is not None:
                a_candidaturas_mayoritarias += municipioDF[partido]
                
                valor = values_dict.get(escala)
                if valor is None:
                    values_dict[escala]=0
                values_dict[escala] += municipioDF[partido]
                
                
        values = list(values_dict.keys())
        weights = list(values_dict.values())
        
        weighted_avg, weighted_std = self.weighted_avg_and_std(values,weights)
        
        index = ["Nombre de Comunidad","Codigo Municipio",  
                 "Participacion","Blancos","Nulos","ACandidaturas",
                 "%CandMayoritarias","EscalaAvg","EscalaStd"]
        # cambia para que estén tambien todos lso datos que ayudan a hacer el merge
        vals = [comunidad,municipioC,votos/total,blancos/votos,nulos/votos,
                a_candidaturas/votos,a_candidaturas_mayoritarias/votos,
                weighted_avg,weighted_std]
        
        return pd.Series(vals,index)
    
                
