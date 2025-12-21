import { nextTick } from 'vue'

export function useTheme() {
    const reloadOverlay = async () => {
        await nextTick()
        if (window?.HSOverlay) {
            window.HSOverlay.autoInit()
        }
    }

    const reloadAccordion = async () => {
        await nextTick()
        if (window?.HSAccordion) {
            window.HSAccordion.autoInit()
        }
    }

    const reloadSelect = async () => {
        await nextTick()
        if (window?.HSSelect) {
            window.HSSelect.autoInit()
        }
    }

    const reloadDropdown = async () => {
        await nextTick()
        if (window?.HSDropdown) {
            window.HSDropdown.autoInit()
        }
    }

    const refresh = async () => {
        await nextTick()
        if (window?.HSOverlay) window.HSOverlay.autoInit()
        if (window?.HSSelect) window.HSSelect.autoInit()
        if (window?.HSAccordion) window.HSAccordion.autoInit()
        if (window?.HSDropdown) window.HSDropdown.autoInit()
    }

    return { reloadOverlay, reloadSelect, reloadAccordion, reloadDropdown, refresh }
}
