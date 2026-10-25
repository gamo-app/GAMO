
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  iniciarSesion,
  obtenerSesion,
  cerrarSesion,
  type UsuarioSesion,
} from "../database/Api";

type AuthContextType = {
  usuario: UsuarioSesion | null;
  cargando: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [usuario, setUsuario] = useState<UsuarioSesion | null>(null);
  const [cargando, setCargando] = useState(true);

  // Recuperar la sesión al abrir o recargar la aplicación.
  useEffect(() => {
    let activo = true;

    async function verificarSesion() {
      try {
        const sesion = await obtenerSesion();

        if (activo) {
          setUsuario(sesion.usuario);
        }
      } catch {
        if (activo) {
          setUsuario(null);
        }
      } finally {
        if (activo) {
          setCargando(false);
        }
      }
    }

    void verificarSesion();

    return () => {
      activo = false;
    };
  }, []);

  // El login crea las cookies; /auth/me devuelve el perfil completo.
  async function login(email: string, password: string) {
    await iniciarSesion(email, password);
    const sesion = await obtenerSesion();
    setUsuario(sesion.usuario);
  }

  // Invalidar la sesión en el backend y limpiar el estado.
  async function logout() {
    try {
      await cerrarSesion();
    } finally {
      setUsuario(null);
    }
  }

  return (
    <AuthContext.Provider
      value={{
        usuario,
        cargando,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const contexto = useContext(AuthContext);

  if (!contexto) {
    throw new Error(
      "useAuth debe utilizarse dentro de AuthProvider"
    );
  }

  return contexto;
}
