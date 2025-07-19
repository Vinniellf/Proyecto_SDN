#!/usr/bin/python3
import cgi
import subprocess
import os
import sys
import json

# Configuración (debe coincidir con login.py)
controllerRestIp = "192.168.200.200:8080"
circuitName     = "nuevo"

# Mismo fichero DB que usas para registrar los flujos
DB_FILE = '/tmp/circuits.json'

# Leemos los registros previos
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r') as f:
        lines = f.readlines()
else:
    lines = []

# Cabecera CGI
print("Content-Type: text/html\n")

# HTML de notificación
print("""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Cerrando Sesión</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f5f5f5; display: flex; height:100vh; justify-content: center; align-items: center; margin:0; }
    .panel { background: #fff; padding: 2rem; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.1); text-align:center; }
    .btn { margin-top:1rem; padding:0.5rem 1rem; background: #007bff; color:#fff; border:none; border-radius:4px; text-decoration:none; }
    .btn:hover { background: #0056b3; }
  </style>
</head>
<body>
  <div class="panel">
    <h1>🔄 Cerrando sesión...</h1>
    <p>Eliminando flujos en el controlador SDN.</p>
""")

# --- CGI principal ---
form = cgi.FieldStorage()
usuario = form.getvalue("usuario")
clave   = form.getvalue("clave")

consulta = (
            "SELECT "
        "rg.nameRule " 
        "FROM user u "
        "JOIN rol_has_regla rr "
            "ON u.table1_idRol = rr.rol_idRol "
        "JOIN regla rg "
            "ON rr.regla_id = rg.id "
        "WHERE u.username = %s"
        "AND u.password = %s;"
    
)

cmd_check = [
    "mysql", "--user=root", "--password=root", "-D", "mydb", "-se",
    consulta % (f"'{usuario}'", f"'{clave}'")
]

resultado = subprocess.check_output(cmd_check).decode().strip()
# cada línea es un rol distinto
flow_suffixes = [r for r in resultado.splitlines() if r]

for line in lines:
    try:
        rec = json.loads(line)
        dpid = rec["Dpid"]
    except (json.JSONDecodeError, KeyError):
        continue

    for suf in flow_suffixes:
        flow_name = f"{dpid}.{circuitName}.{suf}"
        payload = {"switch": dpid, "name": flow_name}
        cmd = (
            f"curl -s -X DELETE "
            f"-H 'Content-Type: application/json' "
            f"-d '{json.dumps(payload)}' "
            f"http://{controllerRestIp}/wm/staticflowpusher/json"
        )
        # Imprimimos el comando para debug; opcional
        print(f"<pre>{cmd}</pre>")
        subprocess.run(cmd, shell=True, check=False)

# Limpiamos el fichero de registros
open(DB_FILE, 'w').close()

# Mensaje final y enlace de retorno
print("""
    <p>✅ Flujos eliminados correctamente.</p>
    <a class="btn" href="/cgi-bin/login.py">Volver al login</a>
  </div>
</body>
</html>
""")
