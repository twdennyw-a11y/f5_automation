document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        // If we are on login page, check if already logged in
        if (localStorage.getItem('f5_token')) {
            window.location.href = '/static/dashboard.html';
        }

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorMsg = document.getElementById('errorMsg');
            const submitBtnText = document.querySelector('#loginBtn span');
            const loader = document.getElementById('loginLoader');

            errorMsg.style.display = 'none';
            submitBtnText.style.opacity = '0';
            loader.style.display = 'block';

            try {
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);

                const response = await fetch('/api/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('f5_token', data.access_token);
                    
                    // Fetch user info to store role
                    const userResponse = await fetch('/api/users/me', {
                        headers: { 'Authorization': `Bearer ${data.access_token}` }
                    });
                    const userData = await userResponse.json();
                    localStorage.setItem('f5_role', userData.role);
                    
                    window.location.href = '/static/dashboard.html';
                } else {
                    const err = await response.json();
                    errorMsg.textContent = err.detail || '登入失敗';
                    errorMsg.style.display = 'block';
                }
            } catch (err) {
                errorMsg.textContent = '連線錯誤，請稍後再試。';
                errorMsg.style.display = 'block';
            } finally {
                submitBtnText.style.opacity = '1';
                loader.style.display = 'none';
            }
        });
    }
});
