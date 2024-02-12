import requests
from flask import Flask, request, jsonify
import json
import base64

app = Flask(__name__)

class ActaResponse:
    def __init__(self, Type, Search, curp, Nombres, Apellidos, Cadena, Estado, Comments, PDF):
        self.Type = Type
        self.Search = Search
        self.curp = curp
        self.Nombres = Nombres
        self.Apellidos = Apellidos
        self.Cadena = Cadena
        self.Estado = Estado
        self.Comments = Comments
        self.PDF = PDF

class ApiResponse:
    def __init__(self, data, status, error):
        self.data = data
        self.status = status
        self.error = error

global_config = {
    'token': None,
    'userId': None,
    'username': None,
    'version': None,
}

def update_global_config():
    global global_config
    global_config['token'] = request.headers.get('Authorization')
    global_config['userId'] = request.headers.get('UserId')
    global_config['username'] = request.headers.get('User')
    global_config['version'] = request.headers.get('Version')
    print("Configuración global actualizada:", global_config)

def get_api_url():
    version_mapping = {
        1: "https://registrocivil.puebla.gob.mx:8001",
        2: "https://registrocivil.puebla.gob.mx:8001",
        3: "https://registrocivil.puebla.gob.mx:8001",
        4: "https://registrocivil.puebla.gob.mx:8001",
    }
    return version_mapping.get(global_config['version'], "https://registrocivil.puebla.gob.mx:8001")

def create_http_client():
    session = requests.Session()
    session.verify = False
    session.headers.update({
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "es-MX,es;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
        "Host": "registrocivil.puebla.gob.mx:8001",
        "Referer": "https://registrocivil.puebla.gob.mx:8001/sirabi/acto/certificacion.html?v=18082023",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": "_ga=GA1.3.19656314.1699328287; _ga_K5N72QPG72=GS1.1.1699328286.1.1.1699328300.0.0.0; _ga_N442TC03Q1=GS1.3.1702441506.1.0.1702441506.0.0.0"
    })
    print("Cliente HTTP creado")
    return session



def buscar(type, search, data):
    client = create_http_client()
    url = f"{get_api_url()}/sirabi-consultas/{type}/{search}/{data}/{global_config['token']}/{global_config['userId']}/{global_config['username'].upper()}?access_token={global_config['token']}&{data}="
    try:
        response = client.get(url, verify=False)
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error al realizar la solicitud HTTP: {e}")
        return None

def obtener_pdf(folio, cadena):
    client = create_http_client()
    url = f"{get_api_url()}/sirabi-consultas/acta/folio/{folio}-S/{cadena}/1/{global_config['userId']}/F/{global_config['token']}/{global_config['userId']}/{global_config['username'].upper()}?access_token={global_config['token']}"
    response = client.get(url)
    if response.ok:
        return response.content
    else:
        return response.content

@app.route('/api/actas/sid/new', methods=['POST'])
def handle_request():
    update_global_config()
    data = request.get_json()
    
    type = data.get('type')
    search = data.get('search')
    curp = data.get('Curp')
    state = data.get('state')
    
    resultado_busqueda = buscar(type, search, curp)
    if resultado_busqueda:
        folio = resultado_busqueda[0].get('folio')
        cadena = resultado_busqueda[0].get('cadena')
        pdf_bytes = obtener_pdf(folio, cadena)
        print(pdf_bytes)
        if pdf_bytes:
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            acta_response = ActaResponse(type, search, curp, curp, cadena, cadena, state, "Descargado", pdf_base64)
            api_response = ApiResponse(acta_response.__dict__, 200, None)
            return jsonify(api_response.__dict__), 200
        else:
            api_response = ApiResponse(None, 404, "PDF no encontrado")
            return jsonify(api_response.__dict__), 404
    else:
        api_response = ApiResponse(None, 404, "Datos no encontrados")
        return jsonify(api_response.__dict__), 404

if __name__ == '__main__':
    app.run(debug=True, port=8062)
