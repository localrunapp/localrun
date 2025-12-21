import { ref, onMounted, onUnmounted } from "vue";

// Store global para el tiempo actual (compartido entre todas las instancias)
const globalTimeStore = (() => {
  const currentTime = ref(Date.now());
  let intervalId = null;
  let subscriberCount = 0;

  const startGlobalTimer = () => {
    if (!intervalId) {
      intervalId = setInterval(() => {
        currentTime.value = Date.now();
      }, 5000); // Actualiza cada 5 segundos
    }
  };

  const stopGlobalTimer = () => {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };

  const subscribe = () => {
    subscriberCount++;
    if (subscriberCount === 1) {
      startGlobalTimer();
    }
  };

  const unsubscribe = () => {
    subscriberCount--;
    if (subscriberCount === 0) {
      stopGlobalTimer();
    }
  };

  return {
    currentTime,
    subscribe,
    unsubscribe,
  };
})();

/**
 * Composable para manejo de fechas y tiempos relativos
 */
export const useDate = () => {
  // Suscribirse al timer global cuando se monta el componente
  onMounted(() => {
    globalTimeStore.subscribe();
  });

  onUnmounted(() => {
    globalTimeStore.unsubscribe();
  });

  /**
   * Devuelve "hace X minutos/horas/días" en español.
   * @param {Date|string} input - Fecha a formatear
   * @param {boolean} watch - Si debe actualizarse automáticamente cada 5 segundos
   */
  const relativeTime = (input, watch = false) => {
    // Si watch es true, usar el tiempo global reactivo
    if (watch) {
      globalTimeStore.currentTime.value; // Esto hace que se recalcule automáticamente
    }
    
    if (!input) return "";
    
    const then = new Date(input);
    const now = new Date();
    const diffMs = now - then;
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return "hace unos segundos";
    if (diffMin < 60) return `hace ${diffMin} ${diffMin === 1 ? "minuto" : "minutos"}`;

    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `hace ${diffHrs} ${diffHrs === 1 ? "hora" : "horas"}`;

    const diffDays = Math.floor(diffHrs / 24);
    if (diffDays < 30) return `hace ${diffDays} ${diffDays === 1 ? "día" : "días"}`;

    // meses/años aproximados
    const diffMonths = Math.floor(diffDays / 30);
    if (diffMonths < 12) return `hace ${diffMonths} ${diffMonths === 1 ? "mes" : "meses"}`;

    const diffYears = Math.floor(diffMonths / 12);
    return `hace ${diffYears} ${diffYears === 1 ? "año" : "años"}`;
  };

  /**
   * Formatea la fecha para mostrar (puedes ajustar locales/opciones).
   */
  const formatDate = (input, options = {}) => {
    if (!input) return "";
    
    const defaultOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    };
    
    const d = new Date(input);
    return d.toLocaleString('es-ES', { ...defaultOptions, ...options });
  };

  /**
   * Formatea solo la fecha (sin hora)
   */
  const formatDateOnly = (input, options = {}) => {
    if (!input) return "";
    
    const defaultOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    };
    
    const d = new Date(input);
    return d.toLocaleDateString('es-ES', { ...defaultOptions, ...options });
  };

  /**
   * Formatea solo la hora (sin fecha)
   */
  const formatTimeOnly = (input, options = {}) => {
    if (!input) return "";
    
    const defaultOptions = {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    };
    
    const d = new Date(input);
    return d.toLocaleTimeString('es-ES', { ...defaultOptions, ...options });
  };

  /**
   * Devuelve si una fecha es hoy
   */
  const isToday = (input) => {
    if (!input) return false;
    
    const today = new Date();
    const date = new Date(input);
    
    return today.toDateString() === date.toDateString();
  };

  /**
   * Devuelve si una fecha es ayer
   */
  const isYesterday = (input) => {
    if (!input) return false;
    
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const date = new Date(input);
    
    return yesterday.toDateString() === date.toDateString();
  };

  /**
   * Formatea fecha de manera inteligente:
   * - "Hoy a las 14:30" si es hoy
   * - "Ayer a las 14:30" si es ayer
   * - "11/10/2025 14:30" para otras fechas
   */
  const formatSmart = (input) => {
    if (!input) return "";
    
    if (isToday(input)) {
      return `Hoy a las ${formatTimeOnly(input)}`;
    }
    
    if (isYesterday(input)) {
      return `Ayer a las ${formatTimeOnly(input)}`;
    }
    
    return formatDate(input);
  };

  /**
   * Devuelve el día de la semana en español
   */
  const getDayName = (input) => {
    if (!input) return "";
    
    const date = new Date(input);
    return date.toLocaleDateString('es-ES', { weekday: 'long' });
  };

  /**
   * Devuelve el mes en español
   */
  const getMonthName = (input) => {
    if (!input) return "";
    
    const date = new Date(input);
    return date.toLocaleDateString('es-ES', { month: 'long' });
  };

  /**
   * Calcula la diferencia en días entre dos fechas
   */
  const daysDiff = (date1, date2 = new Date()) => {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    const diffTime = Math.abs(d2 - d1);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  /**
   * Devuelve si una fecha está en el futuro
   */
  const isFuture = (input) => {
    if (!input) return false;
    return new Date(input) > new Date();
  };

  /**
   * Devuelve si una fecha está en el pasado
   */
  const isPast = (input) => {
    if (!input) return false;
    return new Date(input) < new Date();
  };

  return {
    relativeTime,
    formatDate,
    formatDateOnly,
    formatTimeOnly,
    formatSmart,
    isToday,
    isYesterday,
    getDayName,
    getMonthName,
    daysDiff,
    isFuture,
    isPast,
  };
};