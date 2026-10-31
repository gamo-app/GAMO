export {};

declare global {
  interface Window {
    AndroidApp?: {
      guardarIdUsuario(idUsuario: string): void;
      guardarUsuarioSesion(datos: string): void;
      limpiarUsuarioSesion(): void;
    };
  }
}
