export default defineNuxtRouteMiddleware((to, from) => {
    // Only run on client side
    if (import.meta.server) return;

    const authStore = useAuthStore();

    // Public routes that don't require authentication
    const publicRoutes = ['/setup', '/login', '/offline', '/reset-password'];

    const isPublicRoute = publicRoutes.includes(to.path);
    const isAuthenticated = authStore.isAuthenticated();

    // If user is not authenticated and trying to access protected route
    if (!isAuthenticated && !isPublicRoute) {
        return navigateTo('/login');
    }

    // If user is authenticated and trying to access login page
    if (isAuthenticated && to.path === '/login') {
        return navigateTo('/');
    }
});
