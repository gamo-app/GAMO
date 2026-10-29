# Backend GAMO

Backend de **GAMO**, desarrollado con **Python + FastAPI** y ejecutado como **Python Worker en Cloudflare Workers**.

El backend expone una API HTTP para gestionar los recursos de la aplicación y utiliza **Supabase** como base de datos.

FastAPI se utiliza para:

- Definir los endpoints de la API.
- Validar los datos recibidos.
- Generar automáticamente la documentación OpenAPI.
- Proporcionar la interfaz interactiva disponible en `/docs`.

---

## Arquitectura

```text
                    ┌─────────────────┐
                    │    Frontend     │
                    │ React Native    │
                    └────────┬────────┘
                             │ HTTP
                             ▼
                    ┌─────────────────┐
                    │  Cloudflare     │
                    │     Worker      │
                    │                 │
                    │ Python + FastAPI│
                    └────────┬────────┘
                             │
                             │ Supabase Python SDK
                             ▼
                    ┌─────────────────┐
                    │    Supabase     │
                    │                 │
                    │   PostgreSQL    │
                    └─────────────────┘
```

### Componentes principales

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12+ |
| Framework API | FastAPI |
| Runtime | Cloudflare Workers |
| Base de datos | PostgreSQL |
| Backend de datos | Supabase |
| Gestión de dependencias | uv |
| CLI de Cloudflare | Wrangler |
| Documentación API | OpenAPI / Swagger |

---

# Requisitos

Antes de comenzar, instalar:

- **Node.js y npm**, necesarios para ejecutar Wrangler.
- **Python 3.12 o superior**.
- **uv**, recomendado para gestionar el entorno y las dependencias Python.

### Instalar uv

Consultar la documentación oficial:

https://docs.astral.sh/uv/getting-started/installation/

---

# Instalación

Clonar el repositorio y acceder a la carpeta del backend:

```powershell
cd Backend
```

Instalar las dependencias:

```powershell
uv sync
```

Preparar las dependencias Python para Cloudflare Workers:

```powershell
uv run pywrangler sync
```

---

# Ejecutar en desarrollo

Para iniciar el Worker localmente:

```powershell
npx wrangler dev
```

También puede utilizarse:

```powershell
npm run dev
```

Una vez iniciado, Wrangler mostrará la dirección local donde está disponible el Worker.

> La ruta `/docs` permite acceder a la documentación interactiva de FastAPI si está expuesta por la aplicación.

---

# Dependencias principales

### FastAPI

Framework utilizado para construir la API HTTP.

Se encarga de:

- Definir rutas.
- Validar datos.
- Gestionar parámetros y cuerpos de las peticiones.
- Generar la documentación OpenAPI.
- Proporcionar Swagger UI mediante `/docs`.

### workers-py

Herramientas de Cloudflare para ejecutar aplicaciones Python como Workers.

El proyecto utiliza Pywrangler para preparar las dependencias Python necesarias para el runtime de Cloudflare Workers.

### Supabase

Supabase proporciona PostgreSQL, autenticación y otros servicios de datos. El
backend accede a estos servicios mediante el SDK oficial de Supabase para
Python. No se deben construir manualmente solicitudes HTTP para acceder a las
tablas.

FastAPI sigue exponiendo los endpoints HTTP de la aplicación; el acceso a los
datos se realiza desde el backend mediante el SDK.

---

# Gestión de dependencias

Las dependencias principales del proyecto se declaran en:

```text
pyproject.toml
```

Las versiones resueltas quedan registradas en:

```text
uv.lock
```

Cuando se agregue o modifique una dependencia Python, ejecutar nuevamente:

```powershell
uv sync
uv run pywrangler sync
npx wrangler dev
```

Qué hace cada comando:

- `uv sync` prepara el entorno virtual de desarrollo e instala las
  dependencias declaradas en `pyproject.toml`, usando `uv.lock` para resolver
  versiones reproducibles.
- `uv run pywrangler sync` prepara y empaqueta los paquetes Python que necesita
  el runtime de Cloudflare Workers. Vuelve a ejecutarlo cuando agregues o
  actualices dependencias.
- `npx wrangler dev` inicia el servidor local de Cloudflare Workers. También
  puedes ejecutar `npm run dev`.

### Dependencias Python

- **FastAPI**: define los endpoints, valida los datos recibidos y publica la
  documentación OpenAPI/Swagger en `/docs`.
- **Supabase Python SDK**: cliente oficial para acceder a Supabase desde
  Python. Utilízalo para consultar y modificar datos, invocar funciones y
  trabajar con Supabase Auth.
- **workers-py**: herramientas de desarrollo de Cloudflare para preparar y
  ejecutar Python Workers.

Las dependencias necesarias para el Worker se declaran en
`pyproject.toml`; `uv.lock` registra las versiones resueltas. `Pipfile` se
incluye como alternativa para preparar un entorno local con Pipenv, pero no
reemplaza `pyproject.toml` para empaquetar y ejecutar el Worker.

## Instalación alternativa con Pipenv

Si ya usas Pipenv, desde `Backend` ejecuta:

```powershell
python -m pip install pipenv
pipenv install --dev
```

y posteriormente:

```powershell
uv run pywrangler sync
```

para actualizar el entorno utilizado por Cloudflare Workers.

---

# Configuración de Supabase

El Worker necesita las siguientes variables:

```text
SUPABASE_URL
SUPABASE_KEY
```

Para desarrollo local, pueden configurarse mediante:

```text
.dev.vars
```

Por ejemplo:

```text
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=tu_clave
```

También puede utilizarse el archivo `.env` si está configurado para el entorno correspondiente.

## Archivo de ejemplo

Si el proyecto contiene:

```text
.dev.vars.example
```

copiarlo como:

```text
.dev.vars
```

y completar las credenciales correspondientes.

### Importante

Para el desarrollo del backend se debe utilizar una clave pública:

```text
publishable / anon
```

**Nunca publicar ni subir al repositorio una clave `service_role`.**

Los archivos que contengan credenciales deben estar incluidos en `.gitignore`.

---

# Despliegue en Cloudflare

Las variables de entorno necesarias deben configurarse como **secrets del Worker** en Cloudflare.

No se deben almacenar credenciales sensibles directamente en el código fuente ni subirlas al repositorio.

---

# API

Los endpoints se organizan mediante routers de FastAPI.

## Asistencia con QR estático por sede

El QR impreso contiene un payload estable por sede. Al escanearlo, el backend
usa la hora de Argentina (`UTC-03:00`) para encontrar la clase activa de esa
sede; el cliente no envía `uuid_clase` ni `fecha`.

1. Un usuario con rol `Admin` o `Profesor` obtiene el contenido que luego se
   codifica en la imagen QR:

   ```http
   GET /asistencia/qr/sede/{id_sede}
   ```

   La respuesta incluye `qr_payload`, por ejemplo
   `GAMO:ASISTENCIA:SEDE:2`. El QR físico puede ser estático.

2. Un usuario con rol `Socio` escanea el QR y envía el contenido:

   ```http
   POST /asistencia/qr/escaneo
   Content-Type: application/json
   ```

   ```json
   {
     "qr_payload": "GAMO:ASISTENCIA:SEDE:2"
   }
   ```

   Ambas rutas requieren la cookie de sesión. El backend valida al socio, la
   sede y que haya exactamente una clase activa según el día y hora actuales.
   Devuelve `404` si no hay clase activa y `409` si hay varias o la asistencia
   ya existe ese día.

La tabla `clase` modela horarios recurrentes. Para horarios locales conviene
que `hora_inicio` y `hora_fin` sean `time without time zone`; si actualmente
son `time with time zone`, se pueden migrar preservando la hora local:

```sql
ALTER TABLE public.clase
  ALTER COLUMN hora_inicio TYPE time without time zone
    USING hora_inicio::time,
  ALTER COLUMN hora_fin TYPE time without time zone
    USING hora_fin::time;
```

Para evitar duplicados ante peticiones simultáneas, comprobá primero que no
haya filas duplicadas y luego agregá esta restricción:

```sql
CREATE UNIQUE INDEX asistencia_unica_por_clase_socio_fecha
ON public.asistencia (uuid_clase, codigo_credencial, fecha);
```

Las políticas RLS deben permitir al socio autenticado leer las sedes y los
horarios de clase necesarios para validar el escaneo, consultar sus propias
asistencias y crear una fila únicamente con su propia credencial. El QR estático
identifica la sede, pero no demuestra por sí solo que el escaneo ocurra
físicamente allí.

Ejemplo:

```text
GET  /socio
POST /socio
```

### Obtener socios

```http
GET /socio
```

Devuelve la lista de socios disponibles.

### Crear un socio

```http
POST /socio
Content-Type: application/json
```

Requiere una sesión autenticada y recibe los datos de Auth y del perfil:

```json
{
  "id_plan": 1,
  "fecha_inicio": "2026-10-25",
  "fecha_fin": "2026-11-25",
  "usuario": {
    "email": "socio@example.com",
    "password": "una-clave-segura",
    "nombre": "Nombre",
    "apellido": "Apellido",
    "fecha_nacimiento": "2000-01-01",
    "DNI": 12345678
  }
}
```

El backend busca el rol llamado `Socio`, crea la identidad en Supabase Auth,
inserta el perfil en `public.usuario` con el `id_rol` encontrado y crea la fila
correspondiente en `public.socio`. También requiere `id_plan`, `fecha_inicio`
y `fecha_fin`; crea la membresía inicial en `public.membresia` con esos datos.
Los planes disponibles se consultan en `GET /socio/planes`.

La documentación interactiva permite probar estos endpoints desde:

```text
/docs
```

---

# Acceso a Supabase desde Python

Las operaciones de base de datos se realizan con el cliente del SDK de
Supabase. Inicialízalo con `get_supabase(env)` y las variables
`SUPABASE_URL` y `SUPABASE_KEY`, configuradas para el Worker como se explica en
[Configuración de Supabase](#configuración-de-supabase).

Con el cliente inicializado, se pueden realizar operaciones como:

```python
resultado = supabase.table("socio").select("*").execute()

resultado = (
    supabase.table("usuario")
    .select("email, nombre, apellido")
    .eq("activo", True)
    .execute()
)

resultado = supabase.table("notificacion").insert(datos).execute()

resultado = supabase.rpc("nombre_de_la_funcion", parametros).execute()
```

Para consultas complejas, utiliza una vista o una función SQL/RPC definida en
Supabase y consúmela con el SDK. Aplica las políticas RLS necesarias y valida
los permisos de la operación; el SDK no reemplaza esos controles.

---

# Estructura del proyecto

```text
Backend/
│
├── app/
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── ...
│
├── pyproject.toml
├── uv.lock
├── wrangler.jsonc
├── .dev.vars
├── .dev.vars.example
└── README.md
```

> La estructura exacta puede variar a medida que avance el proyecto.

---

# Comandos rápidos

### Instalar dependencias

```powershell
uv sync
```

### Preparar Python para Workers

```powershell
uv run pywrangler sync
```

### Ejecutar localmente

```powershell
npx wrangler dev
```

### Actualizar dependencias

```powershell
uv sync
uv run pywrangler sync
```

---

# Seguridad

- No subir `.dev.vars` ni `.env` al repositorio.
- No publicar claves de Supabase.
- No utilizar `service_role` en el frontend.
- Validar los permisos del usuario en el backend antes de realizar operaciones administrativas.
- No confiar únicamente en los permisos enviados por el cliente.
- Utilizar las políticas **RLS de Supabase** como capa adicional de seguridad.

---

# Estado del proyecto

El backend se encuentra actualmente en desarrollo.

La API se está construyendo progresivamente mediante routers de FastAPI y el
SDK de Supabase para las operaciones de datos.

Los endpoints y modelos se irán incorporando a este documento a medida que se complete cada módulo.
