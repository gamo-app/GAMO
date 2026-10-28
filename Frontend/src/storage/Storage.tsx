
type CacheEntry<T> = {
  datos: T;
  fecha: number;
};

const CINCO_MINUTOS = 5 * 60 * 1000;
const tiempos: Record<string, number> = {};

export const storage = {
  set(key: string, value: unknown): void {
    localStorage.setItem(key, JSON.stringify(value));
  },

  get<T>(key: string): T | null {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) as T : null;
  },

  remove(key: string): void {
    localStorage.removeItem(key);
  },

  clear(): void {
    localStorage.clear();
  },

  exist(key: string): boolean {
    return localStorage.getItem(key) !== null;
  },

  // Cambiar el tiempo de caché de una lista
  configurarTiempo(key: string, milisegundos: number): void {
    tiempos[key] = milisegundos;
  },

  // Obtener datos guardados o solicitarlos nuevamente
  async obtenerDatos<T>(
    key: string,
    solicitar: () => Promise<T>
  ): Promise<T> {
    const cache = this.get<CacheEntry<T>>(key);
    const tiempo = tiempos[key] ?? CINCO_MINUTOS;

    if (
      cache !== null &&
      Date.now() - cache.fecha < tiempo
    ) {
      return cache.datos;
    }

    const datos = await solicitar();

    this.set(key, {
      datos,
      fecha: Date.now()
    });

    return datos;
  },

  // Forzar una nueva consulta en la próxima llamada
  invalidar(key: string): void {
    this.remove(key);
  }
};