export const usePageLoader = () => {
    const isLoading = ref(false)

    const show = () => {
        isLoading.value = true
    }

    const hide = () => {
        isLoading.value = false
    }

    const toggle = () => {
        isLoading.value = !isLoading.value
    }

    // Cleanup al desmontar el componente
    onBeforeUnmount(() => {
        if (isLoading.value) {
            hide()
        }
    })

    return {
        isLoading: readonly(isLoading),
        show,
        hide,
        toggle
    }
}