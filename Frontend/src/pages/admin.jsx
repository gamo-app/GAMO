import { useState, useEffect } from "react";
import NavBar from "../components/Navbar";
import Header from "../components/Header";
import Main from "../components/Main";
import { storage } from "../database/Storage";
import { API_URL } from "../database/Api";

const BASE_URL = import.meta.env.VITE_API_URL || API_URL || "http://127.0.0.1:8787";
const HOY = new Date().toISOString().split("T")[0];

const FORM_INICIAL = {
  nombre: "",
  apellido: "",
  dni: "",
  telefono: "",
  fecha_nacimiento: "",
  email: "",
  password: "",
  rol: "representante",
  id_sede: "",
  id_deporte: "",
};

function formatearTelefonoInput(valor) {
  let digitos = valor.replace(/\D/g, "");
  if (digitos.startsWith("549")) digitos = digitos.slice(3);
  else if (digitos.startsWith("54")) digitos = digitos.slice(2);
  else if (digitos.startsWith("0")) digitos = digitos.slice(1);

  digitos = digitos.slice(0, 10);

  if (digitos.length <= 2) return digitos;
  if (digitos.length <= 6) return `${digitos.slice(0, 2)}-${digitos.slice(2)}`;
  return `${digitos.slice(0, 2)}-${digitos.slice(2, 6)}-${digitos.slice(6, 10)}`;
}

function Admin() {
  const [formData, setFormData] = useState(FORM_INICIAL);
  const [sedes, setSedes] = useState([]);
  const [deportes, setDeportes] = useState([]);
  const [cargandoCatalogos, setCargandoCatalogos] = useState(true);
  const [mensaje, setMensaje] = useState(null);
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    const cargarCatalogos = async () => {
      try {
        const [resSedes, resDeportes] = await Promise.all([
          fetch(`${BASE_URL}/sede`),
          fetch(`${BASE_URL}/deporte`),
        ]);

        if (!resSedes.ok || !resDeportes.ok) {
          throw new Error("Error al consultar los catálogos de sedes o deportes.");
        }

        const [dataSedes, dataDeportes] = await Promise.all([
          resSedes.json(),
          resDeportes.json(),
        ]);

        // Filtra solo sedes y deportes activos si tienen el campo 'activo'
        const sedesActivas = Array.isArray(dataSedes)
          ? dataSedes.filter((s) => s.activo !== false)
          : [];
        const deportesActivos = Array.isArray(dataDeportes)
          ? dataDeportes.filter((d) => d.activo !== false)
          : [];

        setSedes(sedesActivas);
        setDeportes(deportesActivos);

        setFormData((prev) => ({
          ...prev,
          id_sede: sedesActivas.length > 0 ? String(sedesActivas[0].id_sede) : "",
          id_deporte: deportesActivos.length > 0 ? String(deportesActivos[0].id_deporte) : "",
        }));
      } catch (err) {
        console.error("Error al cargar sedes o deportes:", err);
        setError("No se pudieron cargar las sedes o los deportes. Verificá que el backend esté corriendo en " + BASE_URL);
      } finally {
        setCargandoCatalogos(false);
      }
    };

    cargarCatalogos();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "telefono" ? formatearTelefonoInput(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMensaje(null);
    setError(null);

    if (!formData.id_sede) {
      setError("Debés seleccionar una sede obligatoriamente.");
      return;
    }

    if (formData.rol === "representante" && !formData.id_deporte) {
      setError("Debés seleccionar un deporte para el representante.");
      return;
    }

    setEnviando(true);

    try {
      const payload = {
        nombre: formData.nombre.trim(),
        apellido: formData.apellido.trim(),
        dni: formData.dni.trim(),
        telefono: formData.telefono ? formData.telefono.trim() : null,
        fecha_nacimiento: formData.fecha_nacimiento || null,
        email: formData.email.trim(),
        password: formData.password,
        rol: formData.rol,
        id_sede: parseInt(formData.id_sede, 10),
        id_deporte:
          formData.rol === "representante" && formData.id_deporte
            ? parseInt(formData.id_deporte, 10)
            : null,
      };

      const response = await fetch(`${BASE_URL}/usuario/admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detalle = Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg).join(", ")
          : data.detail;
        throw new Error(detalle || "Error al registrar el usuario");
      }

      storage.invalidar("listaSocios");
      setMensaje(data.mensaje || "¡Usuario registrado con éxito!");
      setFormData({
        ...FORM_INICIAL,
        id_sede: sedes.length > 0 ? String(sedes[0].id_sede) : "",
        id_deporte: deportes.length > 0 ? String(deportes[0].id_deporte) : "",
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  const botonDeshabilitado =
    enviando ||
    cargandoCatalogos ||
    sedes.length === 0 ||
    (formData.rol === "representante" && deportes.length === 0);

  return (
    <Main>
      <Header />
      <section>
        <div className="listabloques">
          <h3>Alta de Usuarios (Administración)</h3>

          {mensaje && (
            <div style={{ color: "green", fontWeight: "bold", margin: "10px 0" }}>
              {mensaje}
            </div>
          )}
          {error && (
            <div style={{ color: "red", fontWeight: "bold", margin: "10px 0" }}>
              {error}
            </div>
          )}

          <form className="bloque" onSubmit={handleSubmit}>
            <div className="input">
              <label>Nombre</label>
              <input
                type="text"
                name="nombre"
                placeholder="Ej: Juan"
                value={formData.nombre}
                onChange={handleChange}
                required
                className="blanco"
              />
            </div>

            <div className="input">
              <label>Apellido</label>
              <input
                type="text"
                name="apellido"
                placeholder="Ej: Pérez"
                value={formData.apellido}
                onChange={handleChange}
                required
                className="blanco"
              />
            </div>

            <div className="input">
              <label>DNI</label>
              <input
                type="text"
                name="dni"
                placeholder="Sin puntos ni espacios"
                value={formData.dni}
                onChange={handleChange}
                required
                pattern="\d{7,9}"
                title="Ingresá entre 7 y 9 números, sin puntos ni espacios"
                className="blanco"
              />
            </div>

            <div className="input">
              <label>Teléfono</label>
              <input
                type="tel"
                name="telefono"
                value={formData.telefono}
                onChange={handleChange}
                placeholder="11-5555-1000"
                pattern="\d{2}-\d{4}-\d{4}"
                title="Ingresá los 10 dígitos del teléfono (ej: 11-5555-1000)"
                className="blanco"
              />
            </div>

            <div className="input">
              <label>Fecha de Nacimiento</label>
              <input
                type="date"
                name="fecha_nacimiento"
                value={formData.fecha_nacimiento}
                onChange={handleChange}
                max={HOY}
                className="blanco"
              />
            </div>

            <div className="input">
              <label>Email</label>
              <input
                type="email"
                name="email"
                placeholder="usuario@correo.com"
                value={formData.email}
                onChange={handleChange}
                required
                className="blanco"
              />
            </div>

            <div className="input">
              <label>Contraseña</label>
              <input
                type="password"
                name="password"
                placeholder="Mínimo 6 caracteres"
                value={formData.password}
                onChange={handleChange}
                required
                minLength={6}
                className="blanco"
              />
            </div>

            <div className="input">
              <label>Rol</label>
              <select
                name="rol"
                value={formData.rol}
                onChange={handleChange}
                className="blanco"
              >
                <option value="representante">Representante</option>
                <option value="profesor">Profesor</option>
                <option value="socio">Socio</option>
              </select>
            </div>

            {formData.rol === "representante" && (
              <div className="input">
                <label>Deporte asignado</label>
                <select
                  name="id_deporte"
                  value={formData.id_deporte}
                  onChange={handleChange}
                  required
                  className="blanco"
                >
                  {cargandoCatalogos && <option value="">Cargando deportes...</option>}
                  {!cargandoCatalogos && deportes.length === 0 && (
                    <option value="">No hay deportes disponibles</option>
                  )}
                  {deportes.map((dep) => (
                    <option key={dep.id_deporte} value={dep.id_deporte}>
                      {dep.nombre}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="input">
              <label>Sede (Obligatoria)</label>
              <select
                name="id_sede"
                value={formData.id_sede}
                onChange={handleChange}
                required
                className="blanco"
              >
                {cargandoCatalogos && <option value="">Cargando sedes...</option>}
                {!cargandoCatalogos && sedes.length === 0 && (
                  <option value="">No hay sedes disponibles</option>
                )}
                {sedes.map((sede) => (
                  <option key={sede.id_sede} value={sede.id_sede}>
                    {sede.nombre} {sede.direccion ? `(${sede.direccion})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <button type="submit" className="azul" disabled={botonDeshabilitado}>
              {enviando ? "Registrando..." : "Registrar Usuario (Admin)"}
            </button>
          </form>
        </div>
      </section>
      <NavBar />
    </Main>
  );
}

export default Admin;