import { useRoute } from 'vue-router';

export function useRouteHelper() {
    const route = useRoute();

    const matchPattern = (pattern) => matchUrlPatternAdvanced(pattern, route.path);

    return {
        matchPattern,
    };
}

function matchUrlPatternAdvanced(pattern, currentPath) {
    // wildcard tipo Laravel: /users/* → ^/users($|/.*)
    if (pattern.endsWith('/*')) {
        const base = pattern.slice(0, -2);
        const regex = new RegExp('^' + base + '($|/.*)');
        return regex.test(currentPath);
    }

    // Coincidencia exacta
    if (pattern === currentPath) {
        return true;
    }

    // patrón con :param → /users/:id → ^/users/[^/]+$
    const paramPattern = new RegExp('^' + pattern
        .replace(/:[^/]+/g, '[^/]+')  // :id → [^/]+
        .replace(/\//g, '/') + '$');

    return paramPattern.test(currentPath);
}
