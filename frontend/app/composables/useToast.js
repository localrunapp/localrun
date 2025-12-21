// app/composables/useToast.js
import { useToastStore } from '@/stores/toast'

export function useToast() {
    const toast = useToastStore()

    return {
        // Métodos originales
        success: toast.success,
        info: toast.info,
        error: toast.error,
        show: toast.show,
        remove: toast.remove,
        update: toast.update,
        updateProgress: toast.updateProgress,
        completeProcess: toast.completeProcess,

        // Métodos rápidos para diferentes tipos de toast
        alert: {
            success: (message, config = {}) => toast.success({
                type: 'alert',
                message,
                duration: 3000,
                position: 'top-right',
                ...config
            }),

            error: (message, config = {}) => toast.error({
                type: 'alert',
                message,
                duration: 5000,
                position: 'top-right',
                ...config
            }),

            warning: (message, config = {}) => toast.show({
                type: 'alert',
                severity: 'warning',
                icon: 'ti ti-alert-triangle',
                title: 'Warning',
                message,
                duration: 4000,
                position: 'top-right',
                ...config
            }),

            info: (message, config = {}) => toast.info({
                type: 'alert',
                message,
                duration: 3000,
                position: 'top-right',
                ...config
            })
        },

        notification: (title, message, config = {}) => toast.show({
            type: 'notification',
            title,
            message,
            duration: 0, // Las notificaciones no se auto-dismiss por defecto
            ...config
        }),

        process: (title, config = {}) => toast.show({
            type: 'process',
            title,
            progress: 0,
            progressLabel: 'Iniciando...',
            duration: 0, // Los procesos no se auto-dismiss
            ...config
        })
    }
}
