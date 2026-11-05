/**
 * PROCTORAI - FRONTEND INTERACTION CONTROLLER
 * Quản lý thời gian thực, Master Toggle Switch, Polling KPI & Gallery Bằng Chứng
 */

document.addEventListener('DOMContentLoaded', () => {
    // ==================== 1. KHỞI TẠO BIẾN & DOM REFS ====================
    let isSystemEnabled = true;
    let currentFilter = 'all';
    let allSnapshots = [];

    // Header & Clock
    const currentTimeEl = document.getElementById('currentTime');
    const systemStatusBadge = document.getElementById('systemStatusBadge');
    const systemStatusText = document.getElementById('systemStatusText');

    // KPI Elements
    const kpiTotalEl = document.getElementById('kpiTotal');
    const kpiPhoneEl = document.getElementById('kpiPhone');
    const kpiCalcEl = document.getElementById('kpiCalc');
    const kpiPoseEl = document.getElementById('kpiPose');
    const kpiFaceEl = document.getElementById('kpiFace');

    // Camera & Controls
    const btnMasterToggle = document.getElementById('btnMasterToggle');
    const textMasterToggle = document.getElementById('textMasterToggle');
    const iconMaster = document.getElementById('iconMaster');
    const standbyScreen = document.getElementById('standbyScreen');
    const btnQuickStart = document.getElementById('btnQuickStart');
    const btnClearSession = document.getElementById('btnClearSession');
    const aiEngineStatus = document.getElementById('aiEngineStatus');

    // Gallery & Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const snapshotsList = document.getElementById('snapshotsList');
    const evidenceCount = document.getElementById('evidenceCount');

    // Modal
    const imageModal = document.getElementById('imageModal');
    const btnModalClose = document.getElementById('btnModalClose');
    const modalImg = document.getElementById('modalImg');
    const modalTitle = document.getElementById('modalTitle');
    const modalTag = document.getElementById('modalTag');
    const modalTime = document.getElementById('modalTime');
    const modalDuration = document.getElementById('modalDuration');

    // ==================== 2. ĐỒNG HỒ THỜI GIAN THỰC ====================
    function updateClock() {
        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        if (currentTimeEl) {
            currentTimeEl.textContent = `${h}:${m}:${s}`;
        }
    }
    setInterval(updateClock, 1000);
    updateClock();

    // ==================== 3. XỬ LÝ MASTER POWER SWITCH ====================
    function renderMasterState(enabled) {
        isSystemEnabled = enabled;

        if (enabled) {
            // Trạng thái BẬT (Active)
            btnMasterToggle.className = 'btn-master active';
            textMasterToggle.textContent = 'TẮT HỆ THỐNG';
            iconMaster.innerHTML = '<path d="M6 6h12v12H6z"/>'; // Icon Stop vuông

            systemStatusBadge.className = 'system-status-pill active';
            systemStatusText.textContent = 'ĐANG GIÁM SÁT';

            standbyScreen.classList.remove('active');
            aiEngineStatus.textContent = 'AI ENGINE: ĐANG GIÁM SÁT';
            aiEngineStatus.style.color = '#34d399';
        } else {
            // Trạng thái TẮT (Standby)
            btnMasterToggle.className = 'btn-master standby';
            textMasterToggle.textContent = 'BẬT HỆ THỐNG';
            iconMaster.innerHTML = '<path d="M8 5v14l11-7z"/>'; // Icon Play tam giác

            systemStatusBadge.className = 'system-status-pill standby';
            systemStatusText.textContent = 'CHẾ ĐỘ CHỜ';

            standbyScreen.classList.add('active');
            aiEngineStatus.textContent = 'AI ENGINE: TẠM DỪNG';
            aiEngineStatus.style.color = '#fbbf24';
        }
    }

    async function handleToggleSystem() {
        try {
            const res = await fetch('/api/toggle_system', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                renderMasterState(data.system_enabled);
            }
        } catch (err) {
            console.error('Lỗi khi chuyển đổi Master Switch:', err);
        }
    }

    btnMasterToggle.addEventListener('click', handleToggleSystem);
    btnQuickStart.addEventListener('click', handleToggleSystem);

    // ==================== 4. XỬ LÝ ĐẶT LẠI PHIÊN THI (CLEAR) ====================
    btnClearSession.addEventListener('click', async () => {
        const ok = confirm('Bạn có chắc chắn muốn đặt lại số liệu và xóa toàn bộ bằng chứng phiên thi này?');
        if (!ok) return;

        try {
            const res = await fetch('/api/clear', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                pollStatus(); // Cập nhật lại ngay lập tức
            }
        } catch (err) {
            console.error('Lỗi khi đặt lại phiên thi:', err);
        }
    });

    // ==================== 5. BỘ LỌC TABS BẰNG CHỨNG ====================
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderSnapshots();
        });
    });

    // ==================== 6. RENDER DANH SÁCH BẰNG CHỨNG ====================
    function renderSnapshots() {
        if (!snapshotsList) return;

        let filtered = allSnapshots;
        if (currentFilter !== 'all') {
            filtered = allSnapshots.filter(s => s.category === currentFilter);
        }

        evidenceCount.textContent = `${allSnapshots.length} ảnh`;

        if (filtered.length === 0) {
            snapshotsList.innerHTML = `
                <div class="empty-gallery">
                    <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                    <p>${allSnapshots.length === 0 ? 'Chưa ghi nhận vi phạm nào' : 'Không có ảnh trong danh mục này'}</p>
                </div>
            `;
            return;
        }

        snapshotsList.innerHTML = filtered.map(snap => `
            <div class="snap-card" onclick="openModal('${snap.image_url}', '${snap.type}', '${snap.category}', '${snap.timestamp}', '${snap.duration}')">
                <div class="snap-thumb-wrap">
                    <img src="${snap.image_url}" alt="${snap.type}" loading="lazy">
                    <span class="snap-badge ${snap.category}">${snap.category.toUpperCase()}</span>
                </div>
                <div class="snap-info">
                    <div class="snap-title" title="${snap.type}">${snap.type}</div>
                    <div class="snap-meta">
                        <span>${formatTimestamp(snap.timestamp)}</span>
                        <span class="snap-duration">${snap.duration}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    function formatTimestamp(ts) {
        if (!ts) return '';
        // Định dạng lại YYYYMMDD_HHMMSS
        const parts = ts.split('_');
        if (parts.length >= 2) {
            const time = parts[1];
            if (time.length >= 6) {
                return `${time.substr(0,2)}:${time.substr(2,2)}:${time.substr(4,2)}`;
            }
        }
        return ts;
    }

    // ==================== 7. MODAL PHÓNG TO HÌNH ẢNH ====================
    window.openModal = function(url, title, cat, time, duration) {
        modalImg.src = url;
        modalTitle.textContent = title;
        modalTag.textContent = cat;
        modalTag.className = `modal-tag ${cat}`;
        modalTime.textContent = `Thời gian: ${formatTimestamp(time)}`;
        modalDuration.textContent = `Kéo dài: ${duration}`;
        imageModal.classList.add('open');
    };

    function closeModal() {
        imageModal.classList.remove('open');
    }

    btnModalClose.addEventListener('click', closeModal);
    imageModal.addEventListener('click', (e) => {
        if (e.target === imageModal) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && imageModal.classList.contains('open')) {
            closeModal();
        }
    });

    // ==================== 8. POLLING ĐỒNG BỘ TRẠNG THÁI (1s) ====================
    async function pollStatus() {
        try {
            const res = await fetch('/api/status');
            if (!res.ok) return;
            const data = await res.json();

            // Đồng bộ Master Switch nếu có sự thay đổi
            if (data.system_enabled !== isSystemEnabled) {
                renderMasterState(data.system_enabled);
            }

            // Cập nhật 5 thẻ KPI
            if (data.stats) {
                kpiTotalEl.textContent = data.stats.total_violations || 0;
                kpiPhoneEl.textContent = data.stats.phone || 0;
                kpiCalcEl.textContent = data.stats.calculator || 0;
                kpiPoseEl.textContent = data.stats.head_pose || 0;
                kpiFaceEl.textContent = data.stats.no_face || 0;
            }

            // Cập nhật danh sách bằng chứng nếu số lượng thay đổi
            const newSnapshots = data.snapshots || [];
            if (JSON.stringify(newSnapshots) !== JSON.stringify(allSnapshots)) {
                allSnapshots = newSnapshots;
                renderSnapshots();
            }
        } catch (err) {
            console.warn('Đang chờ kết nối API ProctorAI...', err);
        }
    }

    // Polling định kỳ mỗi 1 giây
    setInterval(pollStatus, 1000);
    pollStatus();
});
