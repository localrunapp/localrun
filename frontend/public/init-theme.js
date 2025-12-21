(function () {
    try {
        const theme = localStorage.getItem('hs_theme') || 'auto';

        if (theme === 'dark' ||
            (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    } catch (e) {
        console.warn('Error initializing theme:', e);
    }
})();