export {};

declare global {
  interface Window {
    AndroidApp?: {
      guardarIdUsuario(idUsuario: string): void;
    };
  }
}