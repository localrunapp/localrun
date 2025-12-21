/**
 * Backend Health Middleware (Runs FIRST - SSR ONLY)
 * Checks if backend is responding during server-side rendering
 * If SSR passes, client can trust backend is up
 */
export default defineNuxtRouteMiddleware(async (to, from) => {
    // Only check health during SSR - client-side navigation trusts SSR result
    if (import.meta.client) return;

    // Skip for offline page to avoid infinite loop
    if (to.path === '/offline') return;

    const config = useRuntimeConfig();

    try {
        // Quick health check - lightweight endpoint
        // Increased timeout to 3s to handle backend restarts
        const response = await fetch(`${config.backendInternalUrl}/health`, {
            signal: AbortSignal.timeout(3000), // 3s timeout - allows for backend restart
            headers: { 'Accept': 'application/json' }
        });

        console.log(`[Health] Backend check: ${response.status}`);

        // If backend doesn't respond or returns error, it's offline
        if (!response.ok) {
            console.error(`[Health] Backend returned error: ${response.status}`);
            return navigateTo('/offline');
        }
    } catch (error) {
        // Any error (network, timeout, etc) = backend is offline
        console.error(`[Health] Backend unreachable:`, error.message);
        return navigateTo('/offline');
    }
});
