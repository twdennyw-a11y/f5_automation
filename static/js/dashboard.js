document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('f5_token');
    const role = localStorage.getItem('f5_role');

    if (!token) {
        window.location.href = '/static/index.html';
        return;
    }

    // Initialize UI
    fetchUserData();
    setupNavigation();
    
    if (role === 'admin') {
        document.querySelector('.admin-only').style.display = 'block';
    }

    // Initial load
    loadUserRequests();
    if(role === 'admin') loadAllRequests();

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.removeItem('f5_token');
        localStorage.removeItem('f5_role');
        window.location.href = '/static/index.html';
    });

    // Form Submission
    document.getElementById('newRequestForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const msgDiv = document.getElementById('submitMsg');
        msgDiv.textContent = '送出中...';
        msgDiv.style.color = '#3fb950';

        const payload = {
            request_type: document.getElementById('reqType').value,
            target_ip: document.getElementById('reqTargetIp').value,
            details: document.getElementById('reqDetails').value,
        };

        try {
            const resp = await fetch('/api/requests', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (resp.ok) {
                msgDiv.textContent = '申請單已成功送出！';
                document.getElementById('newRequestForm').reset();
                toggleDetailsTemplate(); // reset template
                loadUserRequests();
            } else {
                const err = await resp.json();
                msgDiv.textContent = `失敗: ${JSON.stringify(err.detail)}`;
                msgDiv.style.color = '#f85149';
            }
        } catch (err) {
            msgDiv.textContent = '網路連線錯誤。';
            msgDiv.style.color = '#f85149';
        }
    });
});

async function fetchUserData() {
    const token = localStorage.getItem('f5_token');
    try {
        const resp = await fetch('/api/users/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resp.ok) {
            const user = await resp.json();
            document.getElementById('userNameLabel').textContent = user.username;
            document.getElementById('userRoleLabel').textContent = user.role;
            document.getElementById('userAvatar').textContent = user.username.charAt(0).toUpperCase();
        } else {
            // Token expired or invalid
            localStorage.clear();
            window.location.href = '/static/index.html';
        }
    } catch (e) {
        console.error(e);
    }
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const panels = document.querySelectorAll('.panel');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            panels.forEach(panel => panel.classList.remove('active'));

            item.classList.add('active');
            const target = document.getElementById(item.getAttribute('data-target'));
            target.classList.add('active');
        });
    });
}

function toggleDetailsTemplate() {
    const type = document.getElementById('reqType').value;
    const detailsObj = document.getElementById('reqDetails');
    
    if (type === 'info_query') {
        detailsObj.value = '{\n  "query_type": "all"\n}';
    } else if (type === 'waf_rule') {
        detailsObj.value = '{\n  "rule_name": "Block_SQL_Injection",\n  "action": "enable"\n}';
    } else if (type === 'certificate') {
        detailsObj.value = '{\n  "cert_name": "example_com_cert",\n  "cert_content": "-----BEGIN CERTIFICATE-----\\n..."\n}';
    }
}

function getStatusBadge(status) {
    let cls = `status-${status.toLowerCase()}`;
    const statusMap = {
        'pending': '待處理',
        'approved': '已同意',
        'rejected': '已退回',
        'completed': '已完成',
        'failed': '失敗'
    };
    const displayStatus = statusMap[status.toLowerCase()] || status.toUpperCase();
    return `<span class="status-badge ${cls}">${displayStatus}</span>`;
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleString();
}

async function loadUserRequests() {
    const token = localStorage.getItem('f5_token');
    try {
        const resp = await fetch('/api/requests', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resp.ok) {
            const requests = await resp.json();
            const tbody = document.querySelector('#myRequestsTable tbody');
            tbody.innerHTML = '';
            
            requests.forEach(req => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>#${req.id}</td>
                    <td>${req.request_type}</td>
                    <td>${req.target_ip}</td>
                    <td>${getStatusBadge(req.status)}</td>
                    <td>${formatDate(req.created_at)}</td>
                    <td><button class="action-btn" onclick='showModal(${JSON.stringify(req.details)})'>查看</button></td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) { console.error(e); }
}

async function loadAllRequests() {
    const token = localStorage.getItem('f5_token');
    const role = localStorage.getItem('f5_role');
    if (role !== 'admin') return;

    try {
        const resp = await fetch('/api/requests', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resp.ok) {
            const requests = await resp.json();
            const tbody = document.querySelector('#adminRequestsTable tbody');
            tbody.innerHTML = '';
            
            requests.forEach(req => {
                // Actions only for pending
                let actionHtml = '';
                if (req.status === 'pending') {
                    actionHtml = `
                        <button class="action-btn btn-approve" onclick="updateRequestStatus(${req.id}, 'approved')">同意</button>
                        <button class="action-btn btn-reject" onclick="updateRequestStatus(${req.id}, 'rejected')">退回</button>
                    `;
                }

                let logsHtml = req.admin_log ? `<button class="action-btn" onclick='showModal(${JSON.stringify(req.admin_log)})'>紀錄</button>` : '-';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>#${req.id}</td>
                    <td>${req.user_id}</td>
                    <td>${req.request_type}</td>
                    <td>${req.target_ip}</td>
                    <td>${getStatusBadge(req.status)}</td>
                    <td>${actionHtml}</td>
                    <td>${logsHtml}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) { console.error(e); }
}

async function updateRequestStatus(id, newStatus) {
    const statusMap = {
        'approved': '同意',
        'rejected': '退回'
    };
    const twStatus = statusMap[newStatus.toLowerCase()] || newStatus;
    
    if (!confirm(`確定要將申請單 #${id} 標記為 [${twStatus}] 嗎？`)) return;

    const token = localStorage.getItem('f5_token');
    try {
        const payload = { status: newStatus };
        const resp = await fetch(`/api/requests/${id}/approve`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (resp.ok) {
            alert(`申請單 #${id} 已開始執行，請隨後查看紀錄了解詳情。`);
            loadAllRequests(); // refresh table
            loadUserRequests();
        } else {
            const err = await resp.json();
            alert(`發生錯誤: ${JSON.stringify(err.detail)}`);
        }
    } catch (e) { console.error(e); }
}

function showModal(content) {
    document.getElementById('modalContent').textContent = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
    document.getElementById('detailsModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('detailsModal').style.display = 'none';
}
