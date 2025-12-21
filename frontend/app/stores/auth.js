import { defineStore } from 'pinia';

export const useAuthStore = defineStore('authStore', {
    state: () => ({
        token: null,
        user: null,
    }),

    actions: {
        saveCookie(name, value, maxAge) {
            const isDev = import.meta.env.DEV;
            const cookie = useCookie(name, {
                maxAge,
                sameSite: 'lax',
                secure: !isDev,
            });

            if (typeof value === 'object') {
                cookie.value = JSON.stringify(value);
            } else {
                cookie.value = value;
            }
        },

        getFromCookie(name) {
            const cookie = useCookie(name);
            if (!cookie.value) return null;
            return cookie.value;
        },

        deleteCookie(name) {
            const cookie = useCookie(name);
            cookie.value = null;
        },

        saveToken(token) {
            this.token = token;
            const payload = JSON.parse(atob(token.split('.')[1]));
            const expires = payload.exp * 1000;

            this.saveCookie('jwt', token, (expires - Date.now()) / 1000);
        },

        saveUser(user) {
            this.user = user;
            const userCookie = useCookie('user');
            userCookie.value = JSON.stringify(user);
        },

        getToken() {
            if (this.token) return this.token;
            return this.getFromCookie('jwt');
        },

        getUser() {
            if (this.user) return this.user;
            const userCookie = useCookie('user');
            return userCookie.value;
        },

        async login(password) {
            try {
                const config = useRuntimeConfig();
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ password }),
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Login failed');
                }

                const data = await response.json();

                if (data.access_token) {
                    this.saveToken(data.access_token);
                }

                if (data.user) {
                    this.saveUser(data.user);
                }

                return data;
            } catch (error) {
                console.error('Login error:', error);
                throw error;
            }
        },

        async fetchCurrentUser() {
            try {
                const token = this.getToken();
                if (!token) return null;

                const config = useRuntimeConfig();
                const response = await fetch('/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    this.logout();
                    return null;
                }

                const user = await response.json();
                this.saveUser(user);
                return user;
            } catch (error) {
                console.error('Error fetching current user:', error);
                this.logout();
                return null;
            }
        },

        logout() {
            this.user = null;
            this.token = null;

            this.deleteCookie('jwt');
            this.deleteCookie('user');
        },

        async linkAccount(provider, providerId, email, name, username) {
            try {
                const config = useRuntimeConfig();
                const token = this.getToken();
                const response = await fetch('/api/auth/link', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        provider,
                        provider_id: providerId,
                        email,
                        name,
                        username
                    }),
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Linking failed');
                }

                const user = await response.json();
                this.saveUser(user);
                return user;
            } catch (error) {
                console.error('Link error:', error);
                throw error;
            }
        },

        async unlinkAccount(provider) {
            try {
                const config = useRuntimeConfig();
                const token = this.getToken();
                const response = await fetch(`/api/auth/unlink/${provider}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Unlinking failed');
                }

                const user = await response.json();
                this.saveUser(user);
                return user;
            } catch (error) {
                console.error('Unlink error:', error);
                throw error;
            }
        },

        async loginWithProvider(provider, providerId, email) {
            try {
                const config = useRuntimeConfig();
                const response = await fetch('/api/auth/login/oauth', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        provider,
                        provider_id: providerId,
                        email
                    }),
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Login failed');
                }

                const data = await response.json();

                if (data.access_token) {
                    this.saveToken(data.access_token);
                }

                // Fetch user details after login
                await this.fetchCurrentUser();

                return data;
            } catch (error) {
                console.error('OAuth Login error:', error);
                throw error;
            }
        },

        isAuthenticated() {
            const token = this.getToken();
            if (!token) return false;

            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                const expiresAt = payload.exp * 1000;

                if (expiresAt && expiresAt < Date.now()) {
                    this.logout();
                    return false;
                }

                return true;
            } catch {
                return false;
            }
        },
    },

    persist: {
        paths: ['token', 'user']
    }
});
