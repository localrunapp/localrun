// composables/useTimeAgo.ts
import { ref, onMounted, onBeforeUnmount } from 'vue'
import dayjs from 'dayjs'

export const useTimeAgo = (utcDatetime) => {
    const now = ref(new Date())
    let interval

    onMounted(() => {
        interval = setInterval(() => {
            now.value = new Date()
        }, 60000)
    })

    onBeforeUnmount(() => {
        clearInterval(interval)
    })

    const timeAgo = () => {
        // Convertir desde UTC a la hora local del navegador
        return dayjs.utc(utcDatetime).local().from(now.value)
    }

    return { timeAgo }
}
