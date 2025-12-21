// stores/toast.js
import { defineStore } from 'pinia'
import { v4 as uuid } from 'uuid'

const toastConfig = {
    severity: 'info',
    title: null,
    message: null,
    duration: 5000,
    progress: true,
    position: 'top-right',
    icon: null,
}

export const useToastStore = defineStore('toast', {
    state: () => ({
        toasts: {
            'top-left': [],
            'top-center': [],
            'top-right': [],
            'bottom-left': [],
            'bottom-center': [],
            'bottom-right': [],
        },
        timeouts: new Map(), // Para trackear los timeouts activos
    }),
    actions: {
        success(config) {
            const payload = typeof config === 'string' ? { message: config } : config
            const toast = {
                ...toastConfig,
                id: uuid(),
                severity: 'success',
                icon: 'ti ti-circle-check text-green-500',
                position: 'top-center',
                ...payload,
            }
            this.toasts[toast.position].push(toast)
            this._scheduleRemoval(toast)
        },
        info(config) {
            const payload = typeof config === 'string' ? { message: config } : config
            const toast = {
                ...toastConfig,
                id: uuid(),
                severity: 'info',
                icon: 'ti ti-info-circle',
                title: 'Info',
                position: 'top-right',
                ...payload,
            }
            this.toasts[toast.position].push(toast)
            this._scheduleRemoval(toast)
        },
        error(config) {
            const payload = typeof config === 'string' ? { message: config } : config
            const toast = {
                ...toastConfig,
                id: uuid(),
                severity: 'danger',
                icon: 'ti ti-exclamation-circle',
                title: 'Oh no!',
                position: 'top-right',
                ...payload,
            }
            this.toasts[toast.position].push(toast)
            this._scheduleRemoval(toast)
        },
        show(config) {
            const toast = {
                id: uuid(),
                severity: 'info',
                position: 'top-right',
                ...toastConfig,
                ...config,
            }
            this.toasts[toast.position].push(toast)
            this._scheduleRemoval(toast)
        },
        update(id, data) {
            for (const key in this.toasts) {
                const idx = this.toasts[key].findIndex(t => t.id === id)
                if (idx !== -1) {
                    this.toasts[key][idx] = { ...this.toasts[key][idx], ...data }
                    break
                }
            }
        },
        remove(id) {
            // Limpiar timeout si existe
            if (this.timeouts.has(id)) {
                clearTimeout(this.timeouts.get(id))
                this.timeouts.delete(id)
            }

            for (const key in this.toasts) {
                this.toasts[key] = this.toasts[key].filter(t => t.id !== id)
            }
        },
        _scheduleRemoval(toast) {
            // Solo programar auto-remove si duration > 0
            if (toast.duration && toast.duration > 0) {
                const timeoutId = setTimeout(() => {
                    this.remove(toast.id)
                }, toast.duration)

                this.timeouts.set(toast.id, timeoutId)
            }
        },

        // Método específico para actualizar progreso de un toast tipo process
        updateProgress(id, progress, progressLabel = null) {
            const updateData = { progress }
            if (progressLabel) {
                updateData.progressLabel = progressLabel
            }
            this.update(id, updateData)
        },

        // Método para completar un proceso
        completeProcess(id, message = 'Completado') {
            this.update(id, {
                progress: 100,
                progressLabel: message,
                duration: 3000, // Auto-remove después de completar
            })
            // Programar removal para el proceso completado
            this._scheduleRemoval({ id, duration: 3000 })
        },
    },
})
