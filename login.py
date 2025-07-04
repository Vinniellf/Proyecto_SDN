#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
import subprocess
import requests
import time

print("Content-Type: text/html\n")

# --- Configuración de red / Floodlight ---
DPIDS = [
    "00:00:1a:74:72:3f:ef:44",
    "00:00:f2:20:f9:45:4c:4e",
    "00:00:aa:51:aa:ba:72:41",
    "00:00:72:e0:80:7e:85:4c",
    "00:00:5e:c7:6e:c6:11:4c"
]
# Floodlight Static Flow Pusher endpoint (IP CORRECTA de tu controlador)
URL = "http://localhost:8080/wm/staticflowpusher/json"

def push_flow(dpid, flow):
    data = flow.copy()
    data["switch"] = dpid
    return requests.post(URL, json=data, timeout=5)

def install_flows(src, dst):
    for dpid in DPIDS:
        # ARP
        push_flow(dpid, {
            "name": f"flow_arp_{dpid}",
            "priority":"300","eth_type":"0x0806",
            "active":"true","actions":"output=normal"
        })
        # ICMP
        push_flow(dpid, {
            "name":f"flow_icmp_{dpid}",
            "priority":"200","eth_type":"0x0800","ip_proto":"1",
            "ipv4_src": src, "ipv4_dst": dst,
            "active":"true","actions":"output=normal"
        })
        push_flow(dpid, {
            "name":f"flow_icmp_rev_{dpid}",
            "priority":"200","eth_type":"0x0800","ip_proto":"1",
            "ipv4_src": dst, "ipv4_dst": src,
            "active":"true","actions":"output=normal"
        })
        # SSH
        push_flow(dpid, {
            "name":f"flow_ssh_{dpid}",
            "priority":"200","eth_type":"0x0800","ip_proto":"6",
            "ipv4_src": src, "ipv4_dst": dst, "tcp_dst":"22",
            "active":"true","actions":"output=normal"
        })
        push_flow(dpid, {
            "name":f"flow_ssh_rev_{dpid}",
            "priority":"200","eth_type":"0x0800","ip_proto":"6",
            "ipv4_src": dst, "ipv4_dst": src, "tcp_src":"22",
            "active":"true","actions":"output=normal"
        })
        # HTTP
        push_flow(dpid, {
            "name":f"flow_http_{dpid}",
            "priority":"200","eth_type":"0x0800","ip_proto":"6",
            "ipv4_src": src, "ipv4_dst": dst, "tcp_dst":"80",
            "active":"true","actions":"output=normal"
        })
        push_flow(dpid, {
            "name":f"flow_http_rev_{dpid}",
            "priority":"200","eth_type":"0x0800","ip_proto":"6",
            "ipv4_src": dst, "ipv4_dst": src, "tcp_src":"80",
            "active":"true","actions":"output=normal"
        })

# --- CGI / autenticación ---
form    = cgi.FieldStorage()
usuario = form.getvalue("usuario")
clave   = form.getvalue("clave")

# Consulta para obtener el rol
consulta = f"""
SELECT rol.nombre_rol
FROM user
JOIN rol ON user.rol_id_rol = rol.id_rol
WHERE username='{usuario}' AND passwd='{clave}';
"""
cmd_check = f"mysql -u root -proot -D portal_cautivo -se \"{consulta}\""

try:
    resultado = subprocess.check_output(cmd_check, shell=True, stderr=subprocess.DEVNULL).decode().strip()
    if not resultado:
        print("❌ Usuario o contraseña incorrectos.")
        sys.exit(0)

    rol = resultado

    # Marcar auth=1
    subprocess.check_call(
        f"mysql -u root -proot -D portal_cautivo -se "
        f"\"UPDATE user SET auth=1 WHERE username='{usuario}';\"",
        shell=True, stderr=subprocess.DEVNULL
    )

    # Define destino según rol
    if rol in ("Alumno", "Profesor"):
        target = "10.0.0.2"
    elif rol == "SuperAdmin":
        target = "10.0.0.3"
    else:
        print(f"✅ Usuario autenticado con rol desconocido: {rol}")
        sys.exit(0)

    # Inyecta flujos
    try:
        install_flows("10.0.0.1", target)
    except requests.RequestException as rex:
        print("❌ No se pudo conectar al controlador Floodlight.")
        print(f"<pre>{rex}</pre>")
        sys.exit(0)

    # Mensaje de bienvenida
    msgs = {
      "Alumno":     "✅ Bienvenido, Alumno. Acceso a web y SSH habilitado.",
      "Profesor":   "✅ Bienvenido, Profesor. Acceso a servicios habilitado.",
      "SuperAdmin": "✅ Bienvenido, SuperAdmin. Acceso total habilitado."
    }
    print(msgs.get(rol, f"✅ Autenticado con rol: {rol}"))

except subprocess.CalledProcessError:
    print("❌ Error al conectar con la base de datos.")  
