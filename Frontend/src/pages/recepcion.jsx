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
  rol: "socio",
  id_sede: "",
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

function Recepcion() {
  const [formData, setFormData] = useState(FORM_INICIAL);
  const [sedes, setSedes] = useState([]);
  const [cargandoSedes, setCargandoSedes] = useState(true);
  const [mensaje, setMensaje] = useState(null);
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    fetch(`${BASE_URL}/sede`)
      .then((res) => {
        if (!res.ok) throw new Error("No se pudieron obtener las sedes del servidor.");
        return res.json();
      })
      .then((data) => {
        const sedesActivas = Array.isArray(data)
          ? data.filter((s) => s.activo !== false)
          : [];
        setSedes(sedesActivas);
        if (sedesActivas.length > 0) {
          setFormData((prev) => ({
            ...prev,
            id_sede: String(sedesActivas[0].id_sede),
          }));
        }
      })
      .catch((err) => {
        console.error("Error al cargar sedes:", err);
        setError("Error al cargar las sedes. Verificá que el backend esté corriendo en " + BASE_URL);
      })
      .finally(() => setCargandoSedes(false));
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

    setEnviando(true);

    try {
      const response = await fetch(`${BASE_URL}/usuario/recepcion`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: formData.nombre.trim(),
          apellido: formData.apellido.trim(),
          dni: formData.dni.trim(),
          telefono: formData.telefono ? formData.telefono.trim() : null,
          fecha_nacimiento: formData.fecha_nacimiento || null,
          email: formData.email.trim(),
          password: formData.password,
          rol: formData.rol,
          id_sede: parseInt(formData.id_sede, 10),
        }),
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
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  const botonDeshabilitado = enviando || cargandoSedes || sedes.length === 0;

  return (
    <Main>
      <Header />
      <section>
        <div className="listabloques">
          <h3>Agregar socio / Recepción</h3>

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
                placeholder="Ej: María"
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
                placeholder="Ej: Gómez"
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
                placeholder="socio@correo.com"
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
                <option value="socio">Socio</option>
                <option value="profesor">Profesor</option>
              </select>
            </div>

            <div className="input">
              <label>Sede (Obligatoria)</label>
              <select
                name="id_sede"
                value={formData.id_sede}
                onChange={handleChange}
                required
                className="blanco"
              >
                {cargandoSedes && <option value="">Cargando sedes...</option>}
                {!cargandoSedes && sedes.length === 0 && (
                  <option value="">No hay sedes cargadas</option>
                )}
                {sedes.map((sede) => (
                  <option key={sede.id_sede} value={sede.id_sede}>
                    {sede.nombre} {sede.direccion ? `(${sede.direccion})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <button type="submit" className="azul" disabled={botonDeshabilitado}>
              {enviando ? "Registrando..." : "Registrar Usuario"}
            </button>
          </form>
        </div>
      </section>
      <NavBar />
    </Main>
  );
}

export default Recepcion;