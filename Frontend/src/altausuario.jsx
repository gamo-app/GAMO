import { useState } from "react";

const API_URL = "http://localhost:8000";

const FORM_INICIAL = {
  nombre: "",
  apellido: "",
  dni: "",
  telefono: "",
  fecha_nacimiento: "",
  email: "",
  password: "",
  rol: "profesor",
  id_deporte: "1"
};

export default function AltaUsuario() {
  const [formData, setFormData] = useState(FORM_INICIAL);
  const [mensaje, setMensaje] = useState(null);
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

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
      // Ajustado a /api/representantes que es donde está montado el endpoint en FastAPI
      const response = await fetch(`${API_URL}/api/representantes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          // Si está vacío se envía null para que Pydantic lo acepte como opcional
          fecha_nacimiento: formData.fecha_nacimiento ? formData.fecha_nacimiento : null,
          // El deporte solo aplica si el rol es representante
          id_deporte: formData.rol === "representante" ? parseInt(formData.id_deporte, 10) : null,
          id_sede: 1
        })
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        // FastAPI devuelve un arreglo en 'detail' cuando falla la validación (código 422)
        const detalle = Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg).join(", ")
          : data.detail;
        throw new Error(detalle || "Error al registrar el usuario");
      }

      setMensaje("¡Usuario registrado con éxito!");
      setFormData(FORM_INICIAL);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div style={{ maxWidth: "450px", margin: "20px auto", padding: "20px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h2>Alta de Usuario / ABM</h2>
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
            <option value="profesor">Profesor</option>
            <option value="socio">Socio</option>
            <option value="representante">Representante</option>
          </select>
        </div>

        {formData.rol === "representante" && (
          <div>
            <label>Actividad / Deporte Asignado:</label>
            <select 
              name="id_deporte" 
              value={formData.id_deporte} 
              onChange={handleChange} 
              style={{ width: "100%", marginBottom: "10px" }}
            >
              <option value="1">Fútbol</option>
              <option value="2">Básquet</option>
              <option value="3">Natación</option>
            </select>
          </div>
        )}

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