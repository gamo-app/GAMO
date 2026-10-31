
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { storage } from "../storage/Storage";
import type { UsuarioSesion } from "../api/Socios";
import {
  iniciarSesion,
  obtenerSesion,
  cerrarSesion,
} from "../api/Api";

function sincronizarUsuarioAndroid(usuario: UsuarioSesion | null) {
  const androidApp = window.AndroidApp;
  if (!androidApp) return;

  if (usuario) {
    androidApp.guardarUsuarioSesion(JSON.stringify({
      uuid_usuario: usuario.uuid_usuario,
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      email: usuario.email,
      rol: usuario.rol?.nombre ?? "",
    }));
  } else {
    androidApp.limpiarUsuarioSesion();
  }
}

type AuthContextType = {
  usuario: UsuarioSesion | null;
  cargando: boolean;
  login: (
    email: string,
    password: string
  ) => Promise<UsuarioSesion>;
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
  const [usuario, setUsuario] = useState<UsuarioSesion | null>(
  () => storage.get<UsuarioSesion>("usuarioSesion")
);
  const [cargando, setCargando] = useState(true);

  // Recuperar la sesión automáticamente al abrir la aplicación.
  useEffect(() => {
    let activo = true;

    async function verificarSesion() {
      try {
        const sesion = await obtenerSesion();

        if (activo) {
          setUsuario(sesion.usuario);
          sincronizarUsuarioAndroid(sesion.usuario);
        }
      } catch {
        if (activo) {
          setUsuario(null);
          sincronizarUsuarioAndroid(null);
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

  // Iniciar sesión y recuperar los datos actualizados del usuario.
  async function login(
  email: string,
  password: string
): Promise<UsuarioSesion> {
  await iniciarSesion(email, password);

  const sesion = await obtenerSesion();
  storage.set("usuarioSesion", sesion.usuario);
  sincronizarUsuarioAndroid(sesion.usuario);
  setUsuario(sesion.usuario);

  return sesion.usuario;
}

  // Cerrar sesión.
  async function logout() {
  try {
    await cerrarSesion();
  } finally {
    storage.remove("usuarioSesion");
    sincronizarUsuarioAndroid(null);
    setUsuario(null);
  }
}

  return (
    <AuthContext.Provider
      value={{ usuario, cargando, login, logout }}
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
