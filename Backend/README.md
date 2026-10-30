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

Supabase proporciona la base de datos PostgreSQL y sus APIs.

Las consultas de datos utilizan el cliente asíncrono del SDK de Supabase y el token del usuario para respetar RLS. `workers.fetch` se utiliza para las operaciones de autenticación de Supabase.

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
  Python. Se utiliza para consultar y modificar datos respetando las políticas
  RLS del usuario autenticado.
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

# Consultas a Supabase REST

El backend utiliza la API REST de Supabase para realizar consultas sobre PostgreSQL.

La estructura general es:

```text
https://<PROYECTO>.supabase.co/rest/v1/<TABLA>
```

Por ejemplo:

```text
/rest/v1/grupo_usuario
```

Para seleccionar todas las columnas:

```text
/rest/v1/grupo_usuario?select=*
```

Esto equivale conceptualmente a:

```sql
SELECT *
FROM grupo_usuario;
```

---

## Operadores de Supabase REST

Supabase REST utiliza operadores específicos para representar condiciones SQL.

| SQL | Supabase REST |
|---|---|
| `=` | `eq.` |
| `!=` | `neq.` |
| `>` | `gt.` |
| `>=` | `gte.` |
| `<` | `lt.` |
| `<=` | `lte.` |
| `IS NULL` | `is.null` |
| `IS NOT NULL` | `not.is.null` |
| `LIKE` | `like.` |
| `ILIKE` | `ilike.` |
| `IN (...)` | `in.(...)` |

### Ejemplos

Buscar un grupo específico:

```text
/rest/v1/grupo_usuario?id_grupo=eq.1
```

Equivalente a:

```sql
SELECT *
FROM grupo_usuario
WHERE id_grupo = 1;
```

Buscar grupos con nivel mayor o igual a 80:

```text
/rest/v1/grupo_usuario?nivel=gte.80
```

Equivalente a:

```sql
SELECT *
FROM grupo_usuario
WHERE nivel >= 80;
```

Buscar personas cuyo nombre contenga `"juan"` sin distinguir mayúsculas/minúsculas:

```text
/rest/v1/persona?nombre=ilike.*juan*
```

Equivalente conceptualmente a:

```sql
SELECT *
FROM persona
WHERE nombre ILIKE '%juan%';
```

---

## Seleccionar columnas

En lugar de:

```text
/rest/v1/persona?select=*
```

se pueden solicitar columnas específicas:

```text
/rest/v1/persona?select=id_persona,nombre,apellido
```

Equivalente a:

```sql
SELECT id_persona, nombre, apellido
FROM persona;
```

---

## Ordenar resultados

Ascendente:

```text
/rest/v1/persona?select=*&order=apellido.asc
```

Descendente:

```text
/rest/v1/persona?select=*&order=apellido.desc
```

Equivalente a:

```sql
SELECT *
FROM persona
ORDER BY apellido DESC;
```

---

## Limitar resultados

```text
/rest/v1/persona?select=*&limit=10
```

Equivalente a:

```sql
SELECT *
FROM persona
LIMIT 10;
```

---

## Combinar filtros

Los parámetros pueden combinarse para representar condiciones `AND`.

```text
/rest/v1/usuario?id_grupo=eq.2&id_sede=eq.5
```

Equivalente a:

```sql
SELECT *
FROM usuario
WHERE id_grupo = 2
  AND id_sede = 5;
```

---

# Relaciones entre tablas

Supabase REST puede utilizar las relaciones definidas mediante claves foráneas para obtener información relacionada.

Por ejemplo, `usuario` tiene una relación con `persona` mediante:

```text
usuario.id_persona
        ↓
persona.id_persona
```

Se puede solicitar:

```text
/rest/v1/usuario?select=*,persona(*)
```

También se pueden seleccionar solamente determinadas columnas:

```text
/rest/v1/usuario?select=email,persona(nombre,apellido,dni)
```

Esto permite obtener información relacionada sin tener que escribir manualmente un `JOIN` SQL para consultas sencillas.

---

# ¿Cuándo utilizar SQL?

Las consultas REST son apropiadas para operaciones simples como:

- Obtener registros.
- Filtrar registros.
- Ordenar resultados.
- Limitar resultados.
- Insertar registros.
- Actualizar registros.
- Eliminar registros.
- Obtener relaciones sencillas.

Para consultas complejas, se recomienda utilizar **SQL, Views o funciones RPC** en Supabase.

Por ejemplo:

```sql
SELECT
    s.id_socio,
    p.nombre,
    p.apellido,
    COUNT(a.id_asistencia) AS asistencias
FROM socio s
JOIN persona p
    ON s.id_persona = p.id_persona
LEFT JOIN asistencia a
    ON s.id_socio = a.id_socio
GROUP BY
    s.id_socio,
    p.nombre,
    p.apellido;
```

Este tipo de consultas puede implementarse mediante una `VIEW` o una función SQL/RPC y luego ser consumida desde el backend.

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

La API se está construyendo progresivamente mediante routers de FastAPI y el SDK de Supabase.

## Asistencia y QR por sede

- `GET /asistencia/mis-asistencias` devuelve las asistencias del socio autenticado.
- `POST /asistencia` permite a `Admin`, `Profesor` y `Representante` registrar una asistencia manual. Recibe `uuid_clase`, `fecha` y `codigo_credencial`.
- `GET /asistencia/qr/sede/{id_sede}` permite a `Admin` y `Profesor` obtener el payload `GAMO:ASISTENCIA:SEDE:{id_sede}` que se codifica como QR.
- `POST /asistencia/qr/escaneo` permite a un `Socio` registrar su asistencia enviando ese payload. El backend determina la clase activa usando la hora de Argentina.

El QR identifica una sede, no prueba por sí solo que el escaneo ocurra físicamente allí. Las políticas RLS deben permitir consultar las sedes y clases necesarias y limitar la lectura y creación de asistencias a los registros autorizados.

Los endpoints y modelos se irán incorporando a este documento a medida que se complete cada módulo.
