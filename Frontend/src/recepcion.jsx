import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
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

export default function Recepcion() {
  const [formData, setFormData] = useState(FORM_INICIAL);
  const [sedes, setSedes] = useState([]);
  const [cargandoSedes, setCargandoSedes] = useState(true);
  const [mensaje, setMensaje] = useState(null);
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/usuarios/sedes`)
      .then((res) => {
        if (!res.ok) throw new Error("No se pudieron obtener las sedes del servidor.");
        return res.json();
      })
      .then((data) => {
        setSedes(data);
        if (data.length > 0) {
          setFormData((prev) => ({ ...prev, id_sede: String(data[0].id_sede) }));
        }
      })
      .catch((err) => {
        console.error("Error al cargar sedes:", err);
        setError("Error al cargar las sedes. Verificá la conexión con el servidor.");
      })
      .finally(() => setCargandoSedes(false));
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const actualizado = { ...prev, [name]: value };
      // Si cambia el rol a "socio" y tenía "Sin sede asignada", preseleccionamos la primera sede
      if (name === "rol" && value === "socio" && !prev.id_sede && sedes.length > 0) {
        actualizado.id_sede = String(sedes[0].id_sede);
      }
      return actualizado;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMensaje(null);
    setError(null);

    if (formData.rol === "socio" && !formData.id_sede) {
      setError("El socio debe tener una sede asignada obligatoriamente.");
      return;
    }

    setEnviando(true);

    try {
      const response = await fetch(`${API_URL}/api/usuarios/recepcion`, {
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
          id_sede: formData.id_sede ? parseInt(formData.id_sede, 10) : null,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detalle = Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg).join(", ")
          : data.detail;
        throw new Error(detalle || "Error al registrar el usuario");
      }

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

  const botonDeshabilitado =
    enviando || cargandoSedes || (formData.rol === "socio" && sedes.length === 0);

  return (
    <div style={{ maxWidth: "450px", margin: "20px auto", padding: "20px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h2>Alta de Usuario (Recepción)</h2>
      {mensaje && <p style={{ color: "green", fontWeight: "bold" }}>{mensaje}</p>}
      {error && <p style={{ color: "red", fontWeight: "bold" }}>{error}</p>}

      <form onSubmit={handleSubmit}>
        <div>
          <label>Nombre:</label>
          <input
            type="text"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            required
            style={{ width: "100%", marginBottom: "10px" }}
          />
        </div>

        <div>
          <label>Apellido:</label>
          <input
            type="text"
            name="apellido"
            value={formData.apellido}
            onChange={handleChange}
            required
            style={{ width: "100%", marginBottom: "10px" }}
          />
        </div>

        <div>
          <label>DNI:</label>
          <input
            type="text"
            name="dni"
            value={formData.dni}
            onChange={handleChange}
            required
            pattern="\d{7,9}"
            title="Ingresá entre 7 y 9 números, sin puntos ni espacios"
            style={{ width: "100%", marginBottom: "10px" }}
          />
        </div>

        <div>
          <label>Teléfono:</label>
          <input
            type="text"
            name="telefono"
            value={formData.telefono}
            onChange={handleChange}
            style={{ width: "100%", marginBottom: "10px" }}
          />
        </div>

        <div>
          <label>Fecha de Nacimiento:</label>
          <input
            type="date"
            name="fecha_nacimiento"
            value={formData.fecha_nacimiento}
            onChange={handleChange}
            max={HOY}
            style={{ width: "100%", marginBottom: "10px" }}
          />
        </div>

        <div>
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            style={{ width: "100%", marginBottom: "10px" }}
          />
        </div>

        <div>
          <label>Contraseña:</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={6}
            style={{ width: "100%", marginBottom: "10px" }}
          />
        </div>

        <div>
          <label>Rol:</label>
          <select
            name="rol"
            value={formData.rol}
            onChange={handleChange}
            style={{ width: "100%", marginBottom: "10px" }}
          >
            <option value="socio">Socio</option>
            <option value="profesor">Profesor</option>
          </select>
        </div>

        <div>
          <label>Sede {formData.rol === "socio" ? "(Obligatoria):" : "(Opcional):"}</label>
          <select
            name="id_sede"
            value={formData.id_sede}
            onChange={handleChange}
            required={formData.rol === "socio"}
            style={{ width: "100%", marginBottom: "10px" }}
          >
            {cargandoSedes && <option value="">Cargando sedes...</option>}
            {!cargandoSedes && sedes.length === 0 && <option value="">No hay sedes cargadas</option>}
            {formData.rol === "profesor" && <option value="">Sin sede asignada</option>}
            {sedes.map((sede) => (
              <option key={sede.id_sede} value={sede.id_sede}>
                {sede.nombre} {sede.direccion ? `(${sede.direccion})` : ""}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={botonDeshabilitado}
          style={{
            width: "100%",
            padding: "10px",
            background: botonDeshabilitado ? "#7aa7d9" : "#007bff",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: botonDeshabilitado ? "not-allowed" : "pointer",
          }}
        >
          {enviando ? "Registrando..." : "Registrar Usuario"}
        </button>
      </form>
    </div>
  );
}