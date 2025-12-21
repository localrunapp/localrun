// plugins/dark-state.client.ts
export default defineNuxtPlugin((nuxtApp) => {
    if (!process.client) return

    const isDark = useState<boolean>('isDark', () => false)

    const updateTheme = () => {
        if (typeof document !== 'undefined') {
            isDark.value = document.documentElement.classList.contains('dark')
        }
    }

    let observer: MutationObserver | null = null

    const initializeTheme = () => {
        updateTheme()

        // Configurar observer para cambios en la clase del documento
        if (observer) {
            observer.disconnect()
        }

        observer = new MutationObserver(() => {
            updateTheme()
        })

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class'],
        })
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeTheme)
    } else {
        nextTick(initializeTheme)
    }

    // Cleanup al desmontar la app
    nuxtApp.hook('app:beforeUnmount', () => {
        if (observer) {
            observer.disconnect()
            observer = null
        }
    })
})
