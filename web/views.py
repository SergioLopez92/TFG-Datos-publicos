from flask import abort, render_template, redirect, flash, url_for, jsonify, make_response, session
from web import app
from web.forms.consulta import Consulta
import web.consulta
import web.mapa


@app.route('/')
def index():
    """
    Página de inicio
    """
    return render_template('index.html')


@app.route('/consulta', methods=('GET', 'POST'))
def consulta():
    """
    Formulario de consulta
    """
    columnas = web.consulta.todas_columnas()
    fuentes = web.consulta.todas_fuentes()
    form = Consulta(fuentes=fuentes, columnas=columnas)
    if form.is_submitted():
        form_data = form.data
        datos = web.consulta.consulta(form_data)
        if datos.empty:
            flash('No hay resultados.')
            return redirect(url_for('consulta'))
        # Guarda los datos del formulario para la descarga
        session['consulta'] = form_data
        mostrar_form = form_data['mostrar']
        mostrar = float('Inf') if not mostrar_form or mostrar_form < 0 else mostrar_form
        if len(datos) >= mostrar:
            flash('Mostrando {} de {} filas'.format(mostrar, len(datos)))
        columnas_numericas = list(datos.select_dtypes(exclude=['object']).columns.values)
        datos_mostrar = datos.head(mostrar) if mostrar != float('Inf') else datos
        return render_template('resultados-consulta.html',
                               datos=datos_mostrar,
                               columnas_numericas=columnas_numericas)
    return render_template('consulta.html', form=form)


@app.route('/api/fuente/<fuente>')
def actualiza_columnas(fuente):
    """
    Obtiene todas las columnas de una fuente en formato json
    """
    columnas = web.consulta.columnas_coleccion(fuente)
    descripcion = web.consulta.descripcion_fuente(fuente)
    return jsonify({
        'columnas': columnas,
        'descripcion': descripcion
    })


@app.route('/consulta/descarga/<formato>')
def descarga_consulta(formato):
    """
    Descarga un dataframe en el formato especificado
    """
    form_data = session.get('consulta')
    # No se ha hecho una consulta
    if not form_data:
        return abort(403)
    # Hace la consulta
    datos = web.consulta.consulta(form_data)
    # Según el formato
    if formato == 'csv':
        contenido = datos.to_csv()
    elif formato == 'json':
        contenido = datos.to_json()
    else:
        return abort(403)
    # Respuesta
    resp = make_response(contenido)
    resp.headers['Content-type'] = 'text/{}'.format(formato)
    resp.headers["Content-Disposition"] = 'attachment; filename=consulta.{}'.format(formato)
    return resp


@app.route('/consulta/mapa/<territorio>/<metodo>/<columna>')
def visualiza_mapa(metodo, territorio, columna):
    """
    Visualiza en el mapa una consulta.
    """
    form_data = session.get('consulta')
    # No se ha hecho una consulta
    if not form_data:
        return abort(403)
    df = web.consulta.consulta(form_data)
    try:
        mapa = web.mapa.visualiza_mapa(df, columna, territorio, metodo)
    except KeyError as ex:
        key = ex.args[0].split('[')[1].split(']')[0]
        flash('Selecciona {} en columnas a mostrar'.format(key))
        return redirect(url_for('consulta'))
    return render_template('visualiza-mapa.html', mapa=mapa)
