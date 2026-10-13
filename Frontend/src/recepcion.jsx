import { useState, useEffect } from "react"; 
const API_URL = "http://localhost:8000";

const FORM_INICIAL = {
  nombre: "",
  apellido: "",
  dni: "",
  telefono: "",
  fecha_nacimiento: "",
  email: "",
  password: "",
  rol: "socio",
  id_sede: ""
};

export default function Recepcion() {
  const [formData, setFormData] = useState(FORM_INICIAL);
  const [sedes, setSedes] = useState([]); 
  const [cargandoSedes, setCargandoSedes] = useState(true);
  const [mensaje, setMensaje] = useState(null);
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  // 3. Consultar las sedes al cargar la pantalla
  useEffect(() => {
    fetch(`${API_URL}/api/usuarios/sedes`)
      .then((res) => {
        if (!res.ok) throw new Error("Error al obtener las sedes");
        return res.json();
      })
      .then((data) => {
        setSedes(data);
        // Si hay sedes en la base, preseleccionamos la primera por defecto
        if (data.length > 0) {
          setFormData((prev) => ({ ...prev, id_sede: String(data[0].id_sede) }));
        }
      })
      .catch((err) => console.error("Error al cargar sedes:", err))
      .finally(() => setCargandoSedes(false));
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMensaje(null);
    setError(null);
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
          fecha_nacimiento: formData.fecha_nacimiento ? formData.fecha_nacimiento : null,
          email: formData.email.trim(),
          password: formData.password,
          rol: formData.rol,
          id_sede: formData.id_sede ? parseInt(formData.id_sede, 10) : null
        })
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
        id_sede: sedes.length > 0 ? String(sedes[0].id_sede) : ""
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div style={{ maxWidth: "450px", margin: "20px auto", padding: "20px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h2>Alta de Usuario (Recepción)</h2>
      {mensaje && <p style={{ color: "green" }}>{mensaje}</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

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

        {/* 4. Selector dinámico de sedes mapeado desde la base de datos */}
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
          disabled={enviando}
          style={{ 
            width: "100%", 
            padding: "10px", 
            background: enviando ? "#7aa7d9" : "#007bff", 
            color: "white", 
            border: "none", 
            borderRadius: "4px", 
            cursor: enviando ? "not-allowed" : "pointer" 
          }}
        >
          {enviando ? "Registrando..." : "Registrar Usuario"}
        </button>
      </form>
    </div>
  );
}