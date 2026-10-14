import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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

export default function Admin() {
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
          fetch(`${API_URL}/api/usuarios/sedes`),
          fetch(`${API_URL}/api/usuarios/deportes`),
        ]);

        if (resSedes.ok) {
          const dataSedes = await resSedes.json();
          setSedes(dataSedes);
          if (dataSedes.length > 0) {
            setFormData((prev) => ({ ...prev, id_sede: String(dataSedes[0].id_sede) }));
          }
        }

        if (resDeportes.ok) {
          const dataDeportes = await resDeportes.json();
          setDeportes(dataDeportes);
          if (dataDeportes.length > 0) {
            setFormData((prev) => ({ ...prev, id_deporte: String(dataDeportes[0].id_deporte) }));
          }
        }
      } catch (err) {
        console.error("Error al cargar sedes o deportes:", err);
      } finally {
        setCargandoCatalogos(false);
      }
    };

    cargarCatalogos();
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
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
      const payload = {
        nombre: formData.nombre.trim(),
        apellido: formData.apellido.trim(),
        dni: formData.dni.trim(),
        telefono: formData.telefono ? formData.telefono.trim() : null,
        fecha_nacimiento: formData.fecha_nacimiento ? formData.fecha_nacimiento : null,
        email: formData.email.trim(),
        password: formData.password,
        rol: formData.rol,
        id_sede: parseInt(formData.id_sede, 10),
        id_deporte: formData.rol === "representante" && formData.id_deporte 
          ? parseInt(formData.id_deporte, 10) 
          : null,
      };

      const response = await fetch(`${API_URL}/api/usuarios/admin`, {
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

  return (
    <div style={{ maxWidth: "480px", margin: "20px auto", padding: "20px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h2>Alta de Usuarios (Administración)</h2>
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
            <option value="representante">Representante</option>
            <option value="profesor">Profesor</option>
            <option value="socio">Socio</option>
          </select>
        </div>

        {/* Desplegable de Deportes (Solo para Representante) */}
        {formData.rol === "representante" && (
          <div>
            <label>Deporte asignado:</label>
            <select 
              name="id_deporte" 
              value={formData.id_deporte} 
              onChange={handleChange} 
              required
              style={{ width: "100%", marginBottom: "10px" }}
            >
              {cargandoCatalogos && <option value="">Cargando deportes...</option>}
              {!cargandoCatalogos && deportes.length === 0 && <option value="">No hay deportes disponibles</option>}
              {deportes.map((dep) => (
                <option key={dep.id_deporte} value={dep.id_deporte}>
                  {dep.nombre}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Desplegable de Sedes (Siempre obligatorio en Admin) */}
        <div>
          <label>Sede (Obligatoria):</label>
          <select 
            name="id_sede" 
            value={formData.id_sede} 
            onChange={handleChange} 
            required
            style={{ width: "100%", marginBottom: "10px" }}
          >
            {cargandoCatalogos && <option value="">Cargando sedes...</option>}
            {!cargandoCatalogos && sedes.length === 0 && <option value="">No hay sedes disponibles</option>}
            {sedes.map((sede) => (
              <option key={sede.id_sede} value={sede.id_sede}>
                {sede.nombre} {sede.direccion ? `(${sede.direccion})` : ""}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={enviando || sedes.length === 0}
          style={{ 
            width: "100%", 
            padding: "10px", 
            background: enviando ? "#7aa7d9" : "#28a745", 
            color: "white", 
            border: "none", 
            borderRadius: "4px", 
            cursor: enviando ? "not-allowed" : "pointer" 
          }}
        >
          {enviando ? "Registrando..." : "Registrar Usuario (Admin)"}
        </button>
      </form>
    </div>
  );
}