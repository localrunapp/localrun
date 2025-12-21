declare global {
    interface Window {
        HSStaticMethods?: {
            autoInit?: () => void
        }
        HSThemeAppearance?: {
            init?: () => void
        }
    }
}

export default defineNuxtPlugin(async (nuxtApp) => {
    if (!process.client) return

    try {
        await import('preline')

        // Función para inicializar Preline
        const initPreline = () => {
            if (window.HSStaticMethods?.autoInit) {
                window.HSStaticMethods.autoInit()
            }
            if (window.HSThemeAppearance?.init) {
                window.HSThemeAppearance.init()
            }
        }

        // Función para realizar múltiples intentos de inicialización
        const performMultipleInits = () => {
            initPreline()
            // Intentos adicionales para asegurar que funcione
            setTimeout(initPreline, 50)
            setTimeout(initPreline, 200)
            setTimeout(initPreline, 500)
        }

        // Inicialización inicial cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', performMultipleInits)
        } else {
            nextTick(performMultipleInits)
        }

        // Re-inicializar después de la navegación
        const router = useRouter()

        router.beforeEach(() => {
            // Limpiar estado antes de la navegación si es necesario
        })

        router.afterEach(() => {
            // Múltiples estrategias para asegurar la reinicialización
            requestAnimationFrame(() => {
                performMultipleInits()
            })
        })

        // Observer para detectar cambios en el DOM
        let layoutObserver: MutationObserver | null = null

        const startLayoutObserver = () => {
            if (layoutObserver) {
                layoutObserver.disconnect()
            }

            layoutObserver = new MutationObserver((mutations) => {
                let shouldReinit = false

                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        // Verificar si se añadieron elementos con atributos de Preline
                        const addedNodes = Array.from(mutation.addedNodes)
                        const hasPrelineElements = addedNodes.some(node => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                const element = node as Element
                                return element.querySelector?.('[data-hs-overlay], [data-hs-dropdown], [data-hs-theme-click-value], [class*="hs-"]') ||
                                    element.hasAttribute?.('data-hs-overlay') ||
                                    element.hasAttribute?.('data-hs-dropdown') ||
                                    element.hasAttribute?.('data-hs-theme-click-value') ||
                                    (typeof element.className === 'string' && element.className.includes('hs-')) ||
                                    (element.className && element.className.toString().includes('hs-'))
                            }
                            return false
                        })

                        if (hasPrelineElements) {
                            shouldReinit = true
                        }
                    }
                })

                if (shouldReinit) {
                    setTimeout(initPreline, 10)
                    setTimeout(initPreline, 100)
                }
            })

            layoutObserver.observe(document.body, {
                childList: true,
                subtree: true
            })
        }

        // Iniciar el observer cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', startLayoutObserver)
        } else {
            nextTick(startLayoutObserver)
        }

        // Observer adicional para detectar cambios específicos de layout
        nuxtApp.hooks.hookOnce('app:mounted', () => {
            performMultipleInits()
        })

        // Reinicializar cuando el componente raíz cambie
        nuxtApp.hooks.hook('page:finish', () => {
            setTimeout(performMultipleInits, 50)
        })

        // Cleanup al desmontar la app
        nuxtApp.hook('app:beforeUnmount', () => {
            if (layoutObserver) {
                layoutObserver.disconnect()
                layoutObserver = null
            }
        })

    } catch (error) {
        console.warn('Error al cargar Preline:', error)
    }
})
