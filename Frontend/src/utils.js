export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const HOY = new Date().toISOString().split("T")[0];

// Formatea automáticamente a XX-XXXX-XXXX mientras el usuario escribe
export function formatearTelefonoInput(valor) {
  let digitos = valor.replace(/\D/g, "");
  if (digitos.startsWith("549")) digitos = digitos.slice(3);
  else if (digitos.startsWith("54")) digitos = digitos.slice(2);
  else if (digitos.startsWith("0")) digitos = digitos.slice(1);

  digitos = digitos.slice(0, 10);

  if (digitos.length <= 2) return digitos;
  if (digitos.length <= 6) return `${digitos.slice(0, 2)}-${digitos.slice(2)}`;
  return `${digitos.slice(0, 2)}-${digitos.slice(2, 6)}-${digitos.slice(6, 10)}`;
}