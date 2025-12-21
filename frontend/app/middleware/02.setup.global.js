/**
 * Setup Status Middleware (Runs AFTER health check)
 * Checks if backend setup is complete
 * Assumes backend is already responding (verified by 01.health.global.js)
 */
export default defineNuxtRouteMiddleware(async (to, from) => {
    // Skip for setup, offline, and reset-password pages
    if (to.path === '/setup' || to.path === '/offline' || to.path === '/reset-password') return;

    // Only run on SSR for instant redirects
    if (import.meta.client) return;

    const config = useRuntimeConfig();

    try {
        // Check setup status endpoint
        const response = await fetch(`${config.backendInternalUrl}/setup/status`, {
            signal: AbortSignal.timeout(1000), // 1s timeout - local should be instant
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            // Setup endpoint failed - redirect to setup
            console.error(`Setup status check failed: ${response.status}`);
            return navigateTo('/setup');
        }

        const data = await response.json();
        console.log(`SSR setup check:`, data);

        const { setup_completed } = data;

        // Redirect to setup if not configured
        if (!setup_completed) {
            return navigateTo('/setup');
        }

        // Setup complete - allow navigation
    } catch (error) {
        // If we get here, backend is up but setup check failed
        // Redirect to setup to be safe
        console.error('Error checking setup status:', error);
        return navigateTo('/setup');
    }
});
