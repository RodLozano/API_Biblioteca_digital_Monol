# test_api.py
import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:8000"
ADMIN_PASSWORD = "admin123"  # debe coincidir con tu app/.env

def j(resp):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}

# ----------------------------
# 1) Crear TIPO DE RECURSO
# ----------------------------
tipo_data = {
    "nombre": "LIBRO",
    "descripcion": "Material impreso"
}
r = requests.post(f"{BASE_URL}/tipos", json=tipo_data)
print("POST /tipos:", r.status_code, j(r))
if r.status_code in (200, 201):
    tipo_id = j(r).get("id")
elif r.status_code == 409:
    # ya existe -> lo buscamos por nombre
    r2 = requests.get(f"{BASE_URL}/tipos", params={"search": tipo_data["nombre"]})
    assert r2.status_code == 200 and j(r2), "No se pudo recuperar el tipo existente"
    tipo_id = j(r2)[0]["id"]
else:
    raise AssertionError("No se pudo crear/recuperar el tipo de recurso")

# Listar tipos
r = requests.get(f"{BASE_URL}/tipos")
print("GET /tipos:", r.status_code, j(r))
assert r.status_code == 200

# Obtener tipo concreto
r = requests.get(f"{BASE_URL}/tipos/{tipo_id}")
print(f"GET /tipos/{tipo_id}:", r.status_code, j(r))
assert r.status_code == 200

# Actualizar tipo
r = requests.put(f"{BASE_URL}/tipos/{tipo_id}", json={"descripcion": "Material impreso y ebooks"})
print(f"PUT /tipos/{tipo_id}:", r.status_code, j(r))
assert r.status_code == 200

# ----------------------------
# 2) Crear RECURSO (usa 'tipo' como str validado dinámicamente)
# ----------------------------
recurso_data = {
    "titulo": "Cálculo I",
    "autor": "Larson",
    "descripcion": "Libro de cálculo",    
    "isban": 9431798498175,
    "copias_totales": 2,
    "copias_disponibles": 2,    # opcional; si no viene = totales
    "is_promoted": False,
    "tipo_id": tipo_id            # si tu modelo usa FK numérica
}
r = requests.post(f"{BASE_URL}/recursos", json=recurso_data)
print("POST /recursos:", r.status_code, j(r))
assert r.status_code in (200, 201), "No se pudo crear el recurso"
recurso_id = j(r).get("id")

# Listar recursos
r = requests.get(f"{BASE_URL}/recursos")
print("GET /recursos:", r.status_code, len(j(r)))
assert r.status_code == 200

# Obtener recurso concreto
r = requests.get(f"{BASE_URL}/recursos/{recurso_id}")
print(f"GET /recursos/{recurso_id}:", r.status_code, j(r))
assert r.status_code == 200

# Actualizar recurso (p.ej., marcar como promovido)
r = requests.put(f"{BASE_URL}/recursos/{recurso_id}", json={"is_promoted": True})
print(f"PUT /recursos/{recurso_id}:", r.status_code, j(r))
assert r.status_code == 200

# ----------------------------
# 3) Crear PRÉSTAMO
# ----------------------------
venc = (datetime.now(timezone.utc) + timedelta(days=21)).isoformat()
prestamo_data = {
    "recurso_id": recurso_id,
    "usuario": "ana@example.com",
    "fecha_vencimiento": venc
}
r = requests.post(f"{BASE_URL}/prestamos", json=prestamo_data)
print("POST /prestamos:", r.status_code, j(r))
assert r.status_code in (200, 201), "No se pudo crear el préstamo"
prestamo_id = j(r).get("id")

# Listar préstamos activos
r = requests.get(f"{BASE_URL}/prestamos", params={"solo_activos": True})
print("GET /prestamos?solo_activos=true:", r.status_code, len(j(r)))
assert r.status_code == 200

# Obtener préstamo concreto
r = requests.get(f"{BASE_URL}/prestamos/{prestamo_id}")
print(f"GET /prestamos/{prestamo_id}:", r.status_code, j(r))
assert r.status_code == 200

# Devolver préstamo
r = requests.put(f"{BASE_URL}/prestamos/{prestamo_id}/devolucion")
print(f"PUT /prestamos/{prestamo_id}/devolucion:", r.status_code, j(r))
assert r.status_code == 200

# ----------------------------
# 4) Eliminar RECURSO (ya sin préstamos activos)
# ----------------------------
r = requests.delete(f"{BASE_URL}/recursos/{recurso_id}")
print(f"DELETE /recursos/{recurso_id}:", r.status_code, j(r))
print(r.status_code)
assert r.status_code in (200, 409)

# ----------------------------
# 5) Intentar borrar TIPO con contraseña incorrecta (debe fallar 403/409)
# ----------------------------
r = requests.delete(f"{BASE_URL}/tipos/{tipo_id}", json={"password": "mala"})
print(f"DELETE /tipos/{tipo_id} (bad pass):", r.status_code, j(r))
assert r.status_code in (403, 409)

# Borrar TIPO con contraseña correcta
r = requests.delete(f"{BASE_URL}/tipos/{tipo_id}", json={"password": ADMIN_PASSWORD})
print(f"DELETE /tipos/{tipo_id} (ok):", r.status_code, j(r))
assert r.status_code == 200

print("\n Todas las pruebas pasaron correctamente")
