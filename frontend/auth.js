import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import {
    getAuth,
    signInWithPopup,
    GoogleAuthProvider,
    signInWithEmailAndPassword,
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// Initialize Firebase
// Note: firebaseConfig is defined in firebase_config.js and attached to window
const app = initializeApp(window.firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// DOM Elements
const googleBtn = document.getElementById('googleBtn');
const loginForm = document.getElementById('loginForm');
const errorMsg = document.getElementById('errorMsg');

// Login Page Logic
if (googleBtn) {
    googleBtn.addEventListener('click', async () => {
        try {
            await signInWithPopup(auth, provider);
            // Redirect handled by onAuthStateChanged
        } catch (error) {
            showError(error.message);
        }
    });
}

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            await signInWithEmailAndPassword(auth, email, password);
            // Redirect handled by onAuthStateChanged
        } catch (error) {
            showError("Ungültige Email oder Passwort.");
            console.error(error);
        }
    });
}

function showError(msg) {
    if (errorMsg) {
        errorMsg.textContent = msg;
        errorMsg.style.display = 'block';
    } else {
        alert(msg);
    }
}

// Global Auth State Monitor
onAuthStateChanged(auth, (user) => {
    const isLoginPage = window.location.pathname.endsWith('login.html');

    if (user) {
        console.log("Logged in as:", user.email);
        localStorage.setItem('user_token', user.accessToken); // For optional backend usage

        if (isLoginPage) {
            // User is logged in but on login page -> Go to Dashboard
            window.location.href = 'index.html';
        }
    } else {
        console.log("No user.");
        localStorage.removeItem('user_token');

        if (!isLoginPage) {
            // User is NOT logged in and NOT on login page -> Go to Login
            window.location.href = 'login.html';
        }
    }
});

// Export Logout Function globally
window.logout = async () => {
    try {
        await signOut(auth);
        window.location.href = 'login.html';
    } catch (error) {
        console.error("Logout failed:", error);
    }
};
