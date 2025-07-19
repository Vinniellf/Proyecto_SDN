#!/usr/bin/python3
import cgi
import subprocess
import os
import sys
import json
import time
import io
import csv

# Configuration
controllerRestIp = "192.168.200.200:8080"
circuitName = "nuevo"
srcAddress = "10.0.0.1"
dstAddress2 = "10.0.0.2"
dstAddress3 = "10.0.0.3"

# Database file in /tmp to avoid permission issues
DB_FILE = '/tmp/circuits.json'
if not os.path.exists(DB_FILE):
    open(DB_FILE, 'a').close()

with open(DB_FILE, 'r') as circuitDb:
    lines = circuitDb.readlines()

def install_flows(flujos):
    #print(flujos)
    """
    Crea reglas de flujo entre srcAddress y dstAddress en el controlador SDN.
    """
    with open(DB_FILE, 'a') as circuitDb:
        # Evita duplicados
        for line in lines:
            data = json.loads(line)
            if data.get('name') == circuitName:
                #print(f"Circuit {circuitName} exists already. Use new name to create.")
                sys.exit()

        # Consultar dispositivo origen
        cmd_dev_src = f"curl -s http://{controllerRestIp}/wm/device/?ipv4={srcAddress}"
        result_src = subprocess.check_output(cmd_dev_src, shell=True).decode()
        parsed_src = json.loads(result_src)
        #print(cmd_dev_src + "\n")

        try:
            source_info = parsed_src[0]['attachmentPoint'][0]
            sourceSwitch = source_info['switchDPID']
            sourcePort = source_info['port']
        except (IndexError, KeyError):
            #print(f"ERROR: endpoint {srcAddress} not known to controller.")
            sys.exit()

        # Consultar dispositivo destino 2
        cmd_dev_dst2 = f"curl -s http://{controllerRestIp}/wm/device/?ipv4={dstAddress2}"
        result_dst2 = subprocess.check_output(cmd_dev_dst2, shell=True).decode()
        parsed_dst2 = json.loads(result_dst2)
        #print(cmd_dev_dst2 + "\n")

        try:
            dest_info2 = parsed_dst2[0]['attachmentPoint'][0]
            destSwitch2 = dest_info2['switchDPID']
            destPort2 = dest_info2['port']
        except (IndexError, KeyError):
            #print(f"ERROR: endpoint {dstAddress2} not known to controller.")
            sys.exit()

        
        # Consultar dispositivo destino 3
        cmd_dev_dst3 = f"curl -s http://{controllerRestIp}/wm/device/?ipv4={dstAddress3}"
        result_dst3 = subprocess.check_output(cmd_dev_dst3, shell=True).decode()
        parsed_dst3 = json.loads(result_dst3)
        #print(cmd_dev_dst3 + "\n")

        try:
            dest_info3 = parsed_dst3[0]['attachmentPoint'][0]
            destSwitch3 = dest_info3['switchDPID']
            destPort3 = dest_info3['port']
        except (IndexError, KeyError):
            #print(f"ERROR: endpoint {dstAddress3} not known to controller.")
            sys.exit()


        #print("Creating circuit:")
        #print(f"from source {sourceSwitch}:{sourcePort} to dest {destSwitch3}:{destPort3}")

        # Obtener ruta 2
        cmd_route2 = (
            f"curl -s http://{controllerRestIp}/wm/topology/route/"
            f"{sourceSwitch}/{sourcePort}/{destSwitch2}/{destPort2}/json"
        )

        # Obtener ruta 3
        cmd_route3 = (
            f"curl -s http://{controllerRestIp}/wm/topology/route/"
            f"{sourceSwitch}/{sourcePort}/{destSwitch3}/{destPort3}/json"
        ) 

        route_res2 = subprocess.check_output(cmd_route2, shell=True).decode()
        route_res3 = subprocess.check_output(cmd_route3, shell=True).decode()
        #print(route_res2 + "\n")
        #print(cmd_route2 + "\n")
        hops2 = json.loads(route_res2)
        hops3 = json.loads(route_res3)
        
        for j, flujo in enumerate(flujos):
            if j % 2 == 1:
                continue
            if flujo['dst'] == dstAddress2:
                hops = hops2
            elif flujo['dst'] == dstAddress3:
                hops = hops3
            else:
                #print(f"ERROR: No route found for {flujo['src']}")
                continue

            for i, hop in enumerate(hops):
                if i % 2 == 0:
                    ap1Dpid = hop['switch']
                    ap1Port = hop['port']['shortPortNumber']
                else:
                    ap2Dpid = hop['switch']
                    ap2Port = hop['port']['shortPortNumber']
                    # forward
                    criteria_obj = json.loads(flujo['criteria'])
                    payload_f = {
                        "switch": ap1Dpid,
                        "name": f"{ap1Dpid}.{circuitName}.{flujo['name']}",
                        "priority": "32768",
                        "in_port": str(ap1Port),
                        "actions": f"output={ap2Port}",
                        "match": criteria_obj
                    }
                    cmd_f = (
                        f"curl -s -H 'Content-Type: application/json' "
                        f"-d '{json.dumps(payload_f)}' "
                        f"http://{controllerRestIp}/wm/staticflowpusher/json"
                    )
                    #print(cmd_f)
                    subprocess.run(cmd_f, shell=True, check=True)

                    criteria_objj = json.loads(flujos[j+1]['criteria'])
                    # reversa
                    payload_r = {
                        "switch": ap1Dpid,
                        "name": f"{ap1Dpid}.{circuitName}.{flujos[j+1]['name']}",
                        "priority": "32768",
                        "in_port": str(ap2Port),
                        "actions": f"output={ap1Port}",
                        "match": criteria_objj
                    }
                    cmd_r = (
                        f"curl -s -H 'Content-Type: application/json' "
                        f"-d '{json.dumps(payload_r)}' "
                        f"http://{controllerRestIp}/wm/staticflowpusher/json"
                    )
                    #print(cmd_r)
                    subprocess.run(cmd_r, shell=True, check=True)

                    # Registrar localmente
                    record = {
                        'name': circuitName,
                        'Dpid': ap1Dpid,
                        'inPort': ap1Port,
                        'outPort': ap2Port,
                        'timestamp': time.asctime()
                    }
                    circuitDb.write(json.dumps(record) + "\n")

        # Confirmar flujos en controlador
        cmd_show = f"curl -s http://{controllerRestIp}/wm/core/switch/all/flow/json | python3 -mjson.tool"
        #print(cmd_show + "\n")
        #print(subprocess.check_output(cmd_show, shell=True).decode())



def render_login(error_msg=None):
    """Muestra el formulario de login. Si error_msg no es None, lo enseña arriba."""
    print("Content-Type: text/html\n")
    print("""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Portal Cautivo</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f5f5f5; display: flex; height: 100vh; justify-content: center; align-items: center; margin:0; }
    .container { background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); width: 300px; }
    h1 { text-align: center; margin-bottom: 1rem; }
    label { display:block; margin-top: 0.5rem; }
    input { width:100%; padding:0.5rem; margin-top:0.25rem; border:1px solid #ccc; border-radius:4px; }
    .btn { width:100%; padding:0.5rem; margin-top:1rem; background:#007bff; color:#fff; border:none; border-radius:4px; cursor:pointer; }
    .btn:hover { background:#0056b3; }
    .error { color:#c00; text-align:center; margin-bottom:1rem; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Bienvenido</h1>""")
    if error_msg:
        print(f'    <div class="error">{error_msg}</div>')
    print("""    <form action="/cgi-bin/login.py" method="POST">
      <label for="usuario">Usuario:</label>
      <input type="text" id="usuario" name="usuario" required>
      <label for="clave">Contraseña:</label>
      <input type="password" id="clave" name="clave" required>
      <button class="btn" type="submit">Ingresar</button>
    </form>
  </div>
</body>
</html>""")

def render_welcome(rol):
    """Muestra la página tras login exitoso con botón de logout."""
    print("Content-Type: text/html\n")
    print(f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Portal Cautivo - {rol}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #eef6ff; display:flex; height:100vh; justify-content:center; align-items:center; margin:0; }}
    .panel {{ background:#fff; padding:2rem; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.1); text-align:center; }}
    h1 {{ margin-bottom:1rem; }}
    .btn-logout {{ margin-top:1rem; padding:0.5rem 1rem; background:#dc3545; color:#fff; border:none; border-radius:4px; cursor:pointer; }}
    .btn-logout:hover {{ background:#a71d2a; }}
  </style>
</head>
<body>
  <div class="panel">
    <h1>✅ Acceso concedido</h1>
    <p>Bienvenido, <strong>{rol}</strong>.</p>
    <form action="/cgi-bin/logout.py" method="POST">
      <input type="hidden" name="usuario" value="{usuario}">
      <input type="hidden" name="clave"   value="{clave}">
      <button class="btn-logout" type="submit">Cerrar sesión</button>
    </form>
  </div>
</body>
</html>""")

# --- CGI principal ---
form = cgi.FieldStorage()
usuario = form.getvalue("usuario")
clave   = form.getvalue("clave")

# Si no han enviado credenciales (visita directa), mostramos el formulario
if usuario is None or clave is None:
    render_login()
    sys.exit()

consulta = (
    "SELECT rol.name FROM user "
    "JOIN rol ON user.table1_idRol = rol.idRol "
    "WHERE username=%s AND password=%s;"
)

consultaRules = (
    "SELECT "
     "rg.id, "
     "rg.nameRule    AS regla_nombre, "
    "rg.regla       AS criterio_json, "
    "rg.ip_src      AS origen, "
    "rg.ip_dst      AS destino "
    "FROM user u "
    "JOIN rol_has_regla rr "
    "ON u.table1_idRol = rr.rol_idRol "
    "JOIN regla rg "
    "ON rr.regla_id = rg.id "
    "WHERE u.username = %s "
    "AND u.password = %s;"
)

cmd_check = [
    "mysql", "--user=root", "--password=root", "-D", "mydb", "-se",
    consulta % (f"'{usuario}'", f"'{clave}'")
]

cmd_checkRules = [
    "mysql", "--user=root", "--password=root", "-D", "mydb", "-se",
    consultaRules % (f"'{usuario}'", f"'{clave}'")
]

try:
    resultado = subprocess.check_output(cmd_checkRules).decode().strip()
    resultadoRol = subprocess.check_output(cmd_check).decode().strip()
    if resultadoRol:
        #print(resultado)
        # 1) Parseamos la salida CSV-like
        f = io.StringIO(resultado)
        reader = csv.reader(f, delimiter='\t', quotechar="'", skipinitialspace=True)

        # 2) Construimos la lista de flujos
        flows = []
        for row in reader:
            # row == ['15','FTP3i','{"eth_type":...}','10.0.0.1','10.0.0.3']
            flows.append({
                "id":       row[0],
                "name":     row[1],
                "criteria": row[2],    # JSON con los matchfields
                "src":      row[3],
                "dst":      row[4],
            })

        rol = resultadoRol
    

        #print(flows)
         # 4) Le pasamos la lista entera a install_flows
        #    (o, si tu instalador necesita un dst genérico, extraes todos los dst)
        install_flows(flows)

        # Mostramos portal de bienvenida
        render_welcome(rol)
    else:
        # Error de credenciales: volvemos a mostrar el login con mensaje
        render_login("❌ Usuario o contraseña incorrectos.")
except Exception as e:
    render_login(f"❌as Error en el sistema. {e}")
