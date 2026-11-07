"""Importación de socios desde un archivo .csv o .xlsx (HU-11)."""
import csv
from datetime import date, datetime, timedelta
import io
import logging
import re
import secrets
import unicodedata
import zipfile

from fastapi import HTTPException
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from supabase import create_async_client
from supabase_config import get_supabase_config

from Base.base_alta_usuario import _rollback, formatear_telefono
from Base.base_exportacion import ahora_ar

logger = logging.getLogger(__name__)

MAX_BYTES_ARCHIVO = 2 * 1024 * 1024
# Un .xlsx es un zip: se limita lo que ocupa descomprimido para que un archivo armado a propósito
# no agote la memoria del Worker.
MAX_BYTES_XLSX_DESCOMPRIMIDO = 50 * 1024 * 1024
# Cada socio nuevo cuesta ~4 llamadas a Supabase y Cloudflare limita las llamadas por request.
MAX_FILAS_IMPORTACION = 100
# Tope de filas que se recorren al leer (Excel a veces guarda miles de filas vacías con formato).
MAX_FILAS_LEIDAS = 5000

DIAS_MEMBRESIA_POR_DEFECTO = 30
DOMINIO_EJEMPLO = "@example.com"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")

# (clave interna, título en la plantilla, obligatoria, nombres aceptados en el encabezado).
# Los nombres aceptados van sin tildes, en minúsculas y sin espacios ni símbolos.
COLUMNAS = [
    ("dni", "DNI *", True, {"dni", "documento", "nrodocumento", "numerodocumento", "nrodni"}),
    ("nombre", "Nombre *", True, {"nombre", "nombres"}),
    ("apellido", "Apellido *", True, {"apellido", "apellidos"}),
    ("email", "Email *", True, {"email", "mail", "correo", "correoelectronico"}),
    (
        "fecha_nacimiento",
        "Fecha de nacimiento *",
        True,
        {"fechadenacimiento", "fechanacimiento", "nacimiento"},
    ),
    ("telefono", "Teléfono", False, {"telefono", "celular", "tel"}),
    ("plan", "Plan (ID o nombre)", False, {"plan", "idplan", "planidonombre"}),
    (
        "fecha_inicio",
        "Inicio de membresía",
        False,
        {"iniciodemembresia", "iniciomembresia", "fechainicio", "inicio"},
    ),
    (
        "fecha_fin",
        "Vencimiento de cuota",
        False,
        {"vencimientodecuota", "vencimientocuota", "vencimiento", "fechafin", "fechadevencimiento"},
    ),
    ("password", "Contraseña", False, {"contrasena", "password", "clave"}),
]

EJEMPLOS = [
    (30123456, "María", "Pérez", "maria.perez@example.com", date(1995, 3, 15), "11 5555-1000", 1, None, None, None),
    (28456789, "Juan", "Gómez", "juan.gomez@example.com", date(1988, 11, 2), None, None, None, None, None),
]

INSTRUCCIONES = [
    "Cómo completar la plantilla",
    "Una fila por socio, en la hoja 'Socios'. Las columnas con * son obligatorias.",
    "Borrá las filas de ejemplo antes de subir el archivo (los emails @example.com se rechazan).",
    "DNI: solo números, con o sin puntos.",
    "Fecha de nacimiento: DD/MM/AAAA.",
    "Plan (opcional): ID o nombre exacto de un plan existente. Si lo completás se crea la membresía: "
    f"empieza hoy y vence a los {DIAS_MEMBRESIA_POR_DEFECTO} días, salvo que indiques las fechas.",
    "Contraseña (opcional): mínimo 6 caracteres. Si la dejás vacía se genera una aleatoria que no se informa.",
    f"Máximo {MAX_FILAS_IMPORTACION} socios por archivo. El DNI y el email no pueden repetirse "
    "ni estar ya registrados.",
    "Formatos aceptados: .xlsx y .csv (separado por ; o por coma).",
]


# ----------------------------------------------------------------------------- lectura del archivo
def _formato_por_nombre(nombre_archivo: str) -> str:
    nombre = (nombre_archivo or "").strip().lower()
    if nombre.endswith(".xlsx"):
        return "xlsx"
    if nombre.endswith(".csv"):
        return "csv"
    raise HTTPException(
        status_code=415,
        detail="Formato no soportado: subí un archivo .csv o .xlsx.",
    )


def _filas_csv(contenido: bytes) -> list[list]:
    if contenido.startswith(b"PK\x03\x04"):
        raise HTTPException(
            status_code=400,
            detail="El archivo es un Excel (.xlsx) con extensión .csv. Cambiale la extensión a .xlsx.",
        )
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Excel en español suele guardar los .csv en Windows-1252.
        texto = contenido.decode("cp1252", errors="replace")
    lineas = [linea for linea in texto.splitlines() if linea.strip()]
    if not lineas:
        return []
    delimitador = max((";", ",", "\t"), key=lineas[0].count)
    try:
        filas = []
        for fila in csv.reader(io.StringIO(texto), delimiter=delimitador):
            filas.append(fila)
            if len(filas) >= MAX_FILAS_LEIDAS:
                break
        return filas
    except csv.Error:
        raise HTTPException(status_code=400, detail="No se pudo leer el .csv: el archivo está dañado.")


def _filas_xlsx(contenido: bytes) -> list[list]:
    invalido = HTTPException(
        status_code=400,
        detail=(
            "No se pudo leer el .xlsx: puede estar dañado o ser un .xls viejo. "
            "Guardalo de nuevo como .xlsx."
        ),
    )
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as zip_xlsx:
            if sum(info.file_size for info in zip_xlsx.infolist()) > MAX_BYTES_XLSX_DESCOMPRIMIDO:
                raise HTTPException(status_code=413, detail="El archivo ocupa demasiado al descomprimirse.")
    except zipfile.BadZipFile:
        raise invalido

    try:
        libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except Exception:
        raise invalido
    try:
        hoja = libro.worksheets[0]
        if hasattr(hoja, "reset_dimensions"):
            hoja.reset_dimensions()
        filas = []
        for fila in hoja.iter_rows(values_only=True):
            filas.append(list(fila))
            if len(filas) >= MAX_FILAS_LEIDAS:
                break
        return filas
    except Exception:
        logger.exception("Error al leer el .xlsx de la importación")
        raise invalido
    finally:
        libro.close()


def _clave_encabezado(valor) -> str:
    sin_tildes = unicodedata.normalize("NFKD", str(valor or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sin_tildes.lower())


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return " ".join(_CONTROL.sub(" ", str(valor)).split())


def _vacio(valor) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


def _mapear_encabezado(fila: list) -> dict[str, int]:
    posicion: dict[str, int] = {}
    for idx, celda in enumerate(fila):
        clave_celda = _clave_encabezado(celda)
        for clave, _, _, nombres in COLUMNAS:
            if clave_celda in nombres and clave not in posicion:
                posicion[clave] = idx
    faltan = [
        titulo.replace(" *", "")
        for clave, titulo, obligatoria, _ in COLUMNAS
        if obligatoria and clave not in posicion
    ]
    if faltan:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Faltan columnas obligatorias: {', '.join(faltan)}. "
                "Descargá la plantilla para ver el formato."
            ),
        )
    return posicion


def _extraer_registros(filas: list[list]) -> list[tuple[int, dict]]:
    """[(número de fila en el archivo, {columna: valor})] sin las filas vacías ni el encabezado."""
    posicion = None
    registros: list[tuple[int, dict]] = []
    for numero, fila in enumerate(filas, start=1):
        if all(_vacio(celda) for celda in fila):
            continue
        if posicion is None:
            posicion = _mapear_encabezado(fila)
            continue
        if len(registros) >= MAX_FILAS_IMPORTACION:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"El archivo tiene más de {MAX_FILAS_IMPORTACION} socios. "
                    "Dividilo en archivos más chicos."
                ),
            )
        registros.append(
            (numero, {clave: (fila[idx] if idx < len(fila) else None) for clave, idx in posicion.items()})
        )
    if posicion is None or not registros:
        raise HTTPException(
            status_code=400,
            detail="El archivo no tiene filas de datos debajo del encabezado.",
        )
    return registros


# ----------------------------------------------------------------------------- validación de cada fila
def _parsear_dni(valor) -> int:
    if isinstance(valor, float):
        if not valor.is_integer():
            raise ValueError("DNI inválido (solo números)")
        valor = int(valor)
    if isinstance(valor, int):
        texto = str(valor)
    else:
        texto = _texto(valor).replace(" ", "")
        if re.fullmatch(r"[0-9]+[.,]0+", texto):
            # "30123456.0": así queda el DNI cuando otra herramienta lo guardó como decimal
            texto = re.split(r"[.,]", texto)[0]
        elif re.fullmatch(r"[0-9]{1,3}(\.[0-9]{3})+", texto):
            texto = texto.replace(".", "")  # "30.123.456"
    if not (texto.isascii() and texto.isdigit()) or len(texto) > 9 or int(texto) <= 0:
        raise ValueError("DNI inválido (solo números, hasta 9 dígitos)")
    return int(texto)


def _parsear_fecha(valor, etiqueta: str) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = re.split(r"[ T]", _texto(valor), maxsplit=1)[0]
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError(f"{etiqueta} inválida (usá DD/MM/AAAA)")


def _validar_fila(valores: dict, planes_por_id: set, planes_por_nombre: dict, hoy: date):
    """Devuelve (datos limpios, [motivos de error]). Junta todos los problemas de la fila."""
    errores: list[str] = []
    datos: dict = {}

    if _vacio(valores.get("dni")):
        errores.append("Falta el DNI")
    else:
        try:
            datos["dni"] = _parsear_dni(valores["dni"])
        except ValueError as error:
            errores.append(str(error))

    for campo in ("nombre", "apellido"):
        texto = _texto(valores.get(campo))
        if not texto:
            errores.append(f"Falta el {campo}")
        elif len(texto) > 100:
            errores.append(f"El {campo} supera los 100 caracteres")
        else:
            datos[campo] = texto

    email = _texto(valores.get("email")).lower()
    if not email:
        errores.append("Falta el email")
    elif len(email) > 254 or not EMAIL_RE.match(email):
        errores.append("El email no tiene un formato válido")
    elif email.endswith(DOMINIO_EJEMPLO):
        errores.append("Es una fila de ejemplo de la plantilla (email @example.com): borrala o reemplazala")
    else:
        datos["email"] = email

    if _vacio(valores.get("fecha_nacimiento")):
        errores.append("Falta la fecha de nacimiento")
    else:
        try:
            nacimiento = _parsear_fecha(valores["fecha_nacimiento"], "Fecha de nacimiento")
            if nacimiento > hoy or nacimiento < date(1900, 1, 1):
                errores.append("La fecha de nacimiento no es válida (futura o anterior a 1900)")
            else:
                datos["fecha_nacimiento"] = nacimiento
        except ValueError as error:
            errores.append(str(error))

    datos["telefono"] = None
    telefono = _texto(valores.get("telefono"))
    if telefono:
        try:
            datos["telefono"] = formatear_telefono(telefono)
        except HTTPException as error:
            errores.append(str(error.detail))

    datos["id_plan"] = None
    plan = _texto(valores.get("plan"))
    if plan:
        if plan.isascii() and plan.isdigit():
            id_plan = int(plan)
        else:
            id_plan = planes_por_nombre.get(_clave_encabezado(plan))
        if id_plan in planes_por_id:
            datos["id_plan"] = id_plan
        else:
            errores.append(f"El plan '{plan[:40]}' no existe")

    datos["fecha_inicio"] = datos["fecha_fin"] = None
    inicio_crudo, fin_crudo = valores.get("fecha_inicio"), valores.get("fecha_fin")
    if _vacio(inicio_crudo) and _vacio(fin_crudo):
        if datos["id_plan"] is not None:
            datos["fecha_inicio"] = hoy
            datos["fecha_fin"] = hoy + timedelta(days=DIAS_MEMBRESIA_POR_DEFECTO)
    elif not plan:
        errores.append("Para cargar fechas de membresía indicá también el plan")
    elif datos["id_plan"] is not None:
        try:
            inicio = hoy if _vacio(inicio_crudo) else _parsear_fecha(inicio_crudo, "Inicio de membresía")
            fin = (
                inicio + timedelta(days=DIAS_MEMBRESIA_POR_DEFECTO)
                if _vacio(fin_crudo)
                else _parsear_fecha(fin_crudo, "Vencimiento de cuota")
            )
            if fin < inicio:
                errores.append("El vencimiento no puede ser anterior al inicio de la membresía")
            else:
                datos["fecha_inicio"], datos["fecha_fin"] = inicio, fin
        except ValueError as error:
            errores.append(str(error))

    password = valores.get("password")
    if _vacio(password):
        # Aleatoria y con minúscula, mayúscula, número y símbolo: cumple cualquier política de Supabase.
        datos["password"] = secrets.token_urlsafe(16) + "aA1!"
    else:
        if isinstance(password, float) and password.is_integer():
            password = int(password)
        password = str(password).strip()
        if not 6 <= len(password) <= 128:
            errores.append("La contraseña debe tener entre 6 y 128 caracteres")
        else:
            datos["password"] = password

    return datos, errores


# ----------------------------------------------------------------------------- alta en Supabase
def _motivo_error(error: Exception) -> str:
    texto = str(error).lower()
    codigo = str(getattr(error, "code", "") or "").lower()
    info = f"{texto} {str(getattr(error, 'details', '') or '').lower()}"
    if codigo == "23505" or "23505" in texto or "duplicate key" in texto:  # clave duplicada en la base
        if "id_membresia" in info:
            return "La secuencia de id_membresia está desincronizada en Supabase (hay que sincronizarla)"
        if "dni" in info:
            return "Ya existe un usuario con ese DNI"
        return "Ya existe un registro duplicado"
    if (
        codigo in ("email_exists", "user_already_exists")
        or "email_exists" in texto
        or "already been registered" in texto
        or "already registered" in texto
        or ("email" in texto and "already" in texto)
    ):
        return "El email ya está registrado"
    if codigo == "weak_password" or (
        "password" in texto and ("weak" in texto or "least" in texto or "characters" in texto)
    ):
        return "La contraseña no cumple la política de seguridad"
    if "too many subrequests" in texto:
        return "El servidor alcanzó su límite de llamadas por pedido (Cloudflare): subí menos socios por archivo"
    logger.exception("Error al importar un socio")
    return "No se pudo crear el socio (error inesperado)"


async def _crear_socio(supabase, id_rol_socio: int, datos: dict) -> dict:
    uuid_usuario = codigo_credencial = id_membresia = None
    try:
        respuesta_auth = await supabase.auth.admin.create_user({
            "email": datos["email"],
            "password": datos["password"],
            "email_confirm": True,
            "user_metadata": {
                "nombre": datos["nombre"],
                "apellido": datos["apellido"],
                "dni": datos["dni"],
                "telefono": datos["telefono"],
                "rol": "socio",
            },
        })
        if respuesta_auth.user is None:
            raise RuntimeError("Supabase Auth no devolvió el usuario creado")
        uuid_usuario = respuesta_auth.user.id

        await (
            supabase.table("usuario")
            .insert({
                "uuid_usuario": uuid_usuario,
                "DNI": datos["dni"],
                "nombre": datos["nombre"],
                "apellido": datos["apellido"],
                "fecha_nacimiento": datos["fecha_nacimiento"].isoformat(),
                "id_rol": id_rol_socio,
            })
            .execute()
        )

        socio = await supabase.table("socio").insert({"uuid_usuario": uuid_usuario}).execute()
        codigo_credencial = socio.data[0]["codigo_credencial"]

        if datos["id_plan"] is not None:
            membresia = await (
                supabase.table("membresia")
                .insert({
                    "codigo_credencial": codigo_credencial,
                    "id_plan": datos["id_plan"],
                    "fecha_inicio": datos["fecha_inicio"].isoformat(),
                    "fecha_fin": datos["fecha_fin"].isoformat(),
                    "porcentaje_descuento": 0,
                })
                .execute()
            )
            id_membresia = membresia.data[0].get("id_membresia")
        return {"uuid_usuario": uuid_usuario, "codigo_credencial": codigo_credencial}
    except Exception:
        await _rollback(supabase, uuid_usuario, codigo_credencial, id_membresia)
        raise


async def _consultar(consulta):
    """Ejecuta una consulta previa a las altas; si falla, devuelve un error claro en JSON."""
    try:
        return await consulta.execute()
    except Exception:
        logger.exception("Error al consultar Supabase durante la importación")
        raise HTTPException(
            status_code=502,
            detail="No se pudo consultar la base de datos. Reintentá en unos minutos.",
        )


async def _cerrar_cliente(supabase) -> None:
    """Cierra las conexiones. Si una falla no se corta nada: lo importante es devolver el reporte."""
    for cerrar in (
        lambda: supabase.postgrest.aclose(),
        lambda: supabase.auth.close(),
        lambda: supabase.realtime.close(),
    ):
        try:
            await cerrar()
        except Exception:
            logger.warning("No se pudo cerrar una conexión de Supabase", exc_info=True)


async def importar_socios_desde_archivo(env, nombre_archivo: str, contenido: bytes) -> dict:
    """Crea los socios del archivo. Las filas válidas se cargan y las inválidas se informan."""
    formato = _formato_por_nombre(nombre_archivo)
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    filas = _filas_xlsx(contenido) if formato == "xlsx" else _filas_csv(contenido)
    registros = _extraer_registros(filas)

    url, key = get_supabase_config(env)
    supabase = await create_async_client(url, key)
    hoy = ahora_ar().date()  # el servidor corre en UTC: "hoy" tiene que ser el de Argentina
    detalle_errores: list[dict] = []
    creados: list[dict] = []

    def registrar_error(fila: int, valores: dict, datos: dict, motivos: list[str]) -> None:
        detalle_errores.append({
            "fila": fila,
            "dni": datos.get("dni") or _texto(valores.get("dni")) or None,
            "email": datos.get("email") or _texto(valores.get("email")) or None,
            "motivo": "; ".join(motivos),
        })

    try:
        roles = await _consultar(supabase.table("rol").select("id_rol,nombre"))
        roles_socio = [r for r in roles.data if str(r["nombre"]).strip().casefold() == "socio"]
        if len(roles_socio) != 1:
            raise HTTPException(
                status_code=500,
                detail="No se puede importar: el rol 'Socio' no existe o está repetido en la tabla rol.",
            )
        id_rol_socio = roles_socio[0]["id_rol"]

        planes = await _consultar(supabase.table("plan").select("id_plan,nombre"))
        planes_por_id = {plan["id_plan"] for plan in planes.data}
        planes_por_nombre = {_clave_encabezado(plan["nombre"]): plan["id_plan"] for plan in planes.data}

        candidatas: list[tuple[int, dict, dict]] = []
        filas_por_dni: dict[int, int] = {}
        filas_por_email: dict[str, int] = {}
        for numero, valores in registros:
            datos, motivos = _validar_fila(valores, planes_por_id, planes_por_nombre, hoy)
            for campo, vistos, etiqueta in (("dni", filas_por_dni, "DNI"), ("email", filas_por_email, "Email")):
                if campo in datos:
                    if datos[campo] in vistos:
                        motivos.append(
                            f"{etiqueta} repetido en el archivo (ya figura en la fila {vistos[datos[campo]]})"
                        )
                    else:
                        vistos[datos[campo]] = numero
            if motivos:
                registrar_error(numero, valores, datos, motivos)
            else:
                candidatas.append((numero, valores, datos))

        if candidatas:
            existentes = await _consultar(
                supabase.table("usuario").select("DNI").in_("DNI", [datos["dni"] for _, _, datos in candidatas])
            )
            dnis_existentes = {int(fila["DNI"]) for fila in existentes.data}
            for numero, valores, datos in candidatas:
                if datos["dni"] in dnis_existentes:
                    registrar_error(numero, valores, datos, ["Ya existe un usuario con ese DNI"])
            candidatas = [c for c in candidatas if c[2]["dni"] not in dnis_existentes]

        for numero, valores, datos in candidatas:
            try:
                alta = await _crear_socio(supabase, id_rol_socio, datos)
            except Exception as error:
                registrar_error(numero, valores, datos, [_motivo_error(error)])
                continue
            creados.append({
                "fila": numero,
                "dni": datos["dni"],
                "nombre": datos["nombre"],
                "apellido": datos["apellido"],
                "email": datos["email"],
                "uuid_usuario": alta["uuid_usuario"],
                "codigo_credencial": alta["codigo_credencial"],
            })
    finally:
        await _cerrar_cliente(supabase)

    detalle_errores.sort(key=lambda e: e["fila"])
    exitos, errores = len(creados), len(detalle_errores)
    return {
        "mensaje": (
            f"Importación finalizada: {exitos} {'socio creado' if exitos == 1 else 'socios creados'} "
            f"y {errores} {'fila con error' if errores == 1 else 'filas con errores'}."
        ),
        "total_filas": len(registros),
        "exitos": exitos,
        "errores": errores,
        "creados": creados,
        "detalle_errores": detalle_errores,
    }


# ----------------------------------------------------------------------------- plantillas
def generar_plantilla_xlsx() -> io.BytesIO:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Socios"
    relleno_obligatoria = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    relleno_opcional = PatternFill(start_color="7F8FA6", end_color="7F8FA6", fill_type="solid")

    for col, (_, titulo, obligatoria, _) in enumerate(COLUMNAS, start=1):
        celda = hoja.cell(row=1, column=col, value=titulo)
        celda.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        celda.fill = relleno_obligatoria if obligatoria else relleno_opcional
        celda.alignment = Alignment(horizontal="center", vertical="center")
        hoja.column_dimensions[get_column_letter(col)].width = max(len(titulo) + 4, 16)
    hoja.row_dimensions[1].height = 22

    for fila, ejemplo in enumerate(EJEMPLOS, start=2):
        for col, valor in enumerate(ejemplo, start=1):
            celda = hoja.cell(row=fila, column=col, value=valor)
            if isinstance(valor, date):
                celda.number_format = "DD/MM/YYYY"
            if isinstance(valor, str):
                celda.data_type = "s"
    hoja.freeze_panes = "A2"

    instrucciones = libro.create_sheet("Instrucciones")
    instrucciones.column_dimensions["A"].width = 110
    for fila, texto in enumerate(INSTRUCCIONES, start=1):
        celda = instrucciones.cell(row=fila, column=1, value=texto)
        celda.alignment = Alignment(wrap_text=True, vertical="top")
        if fila == 1:
            celda.font = Font(name="Calibri", size=13, bold=True, color="1F497D")

    salida = io.BytesIO()
    libro.save(salida)
    salida.seek(0)
    return salida


def generar_plantilla_csv() -> bytes:
    """CSV separado por ';' y con BOM, que es como Excel en español lo abre bien (con tildes)."""
    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=";", lineterminator="\r\n")
    escritor.writerow([titulo for _, titulo, _, _ in COLUMNAS])
    for ejemplo in EJEMPLOS:
        escritor.writerow([
            "" if valor is None else valor.strftime("%d/%m/%Y") if isinstance(valor, date) else valor
            for valor in ejemplo
        ])
    return salida.getvalue().encode("utf-8-sig")