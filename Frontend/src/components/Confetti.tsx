
import {
  useState,
  useImperativeHandle,
  forwardRef,
  useRef,
  useEffect,
} from "react";

export type ConfettiRef = {
  aparecer: () => void;
};

const Confetti = forwardRef<ConfettiRef>((_, ref) => {
  const [activo, setActivo] = useState(false);
  const [key, setKey] = useState(0);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);

  useImperativeHandle(ref, () => ({
    aparecer() {
      setActivo(true);
      setKey((k) => k + 1);

      if (temporizador.current) {
        clearTimeout(temporizador.current);
      }

      temporizador.current = setTimeout(() => {
        setActivo(false);
        temporizador.current = null;
      }, 5500);
    },
  }));

  useEffect(() => {
    return () => {
      if (temporizador.current) {
        clearTimeout(temporizador.current);
      }
    };
  }, []);

  if (!activo) return null;

  const colores = [
    "#22c55e", "#3b82f6", "#facc15",
    "#ec4899", "#a855f7",
  ];

  return (
    <div className="confetti-cielo" key={key}>
      {Array.from({ length: 100 }, (_, i) => (
        <span
          key={`${key}-${i}`}
          className="confetti-particula"
          style={{
            left: `${Math.random() * 100}vw`,
            width: `${0.4 + Math.random() * 0.6}vh`,
            height: `${0.5 + Math.random()}vh`,
            backgroundColor: colores[i % colores.length],
            animationDelay: `${Math.random() * 1.5}s`,
            animationDuration: `${2 + Math.random() * 3}s`,
          }}
        />
      ))}
    </div>
  );
});

export default Confetti;
