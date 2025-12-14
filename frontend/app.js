// ===== Configuration =====
const API_URL = window.location.origin + '/api';

// ===== Translations =====
const translations = {
    fa: {
        daily: 'روزانه',
        weekly: 'هفتگی',
        monthly: 'ماهانه',
        search: 'جستجو',
        searchPlaceholder: '@username (مثال: @tirok547)',
        noResults: 'کاربری یافت نشد',
        field: 'رشته',
        grade: 'پایه',
        dailyTime: 'امروز',
        weeklyTime: 'هفتگی',
        monthlyTime: 'ماهانه',
        totalTime: 'کل زمان',
        rank: 'رتبه',
        noStats: 'هنوز آماری ثبت نشده است',
        error: 'خطا در دریافت اطلاعات'
    },
    en: {
        daily: 'Daily',
        weekly: 'Weekly',
        monthly: 'Monthly',
        search: 'Search',
        searchPlaceholder: '@username (e.g. @tirok547)',
        noResults: 'No user found',
        field: 'Field',
        grade: 'Grade',
        dailyTime: 'Today',
        weeklyTime: 'Weekly',
        monthlyTime: 'Monthly',
        totalTime: 'Total Time',
        rank: 'Rank',
        noStats: 'No statistics available yet',
        error: 'Error fetching data'
    }
};

// ===== State =====
let currentLang = 'fa';
let currentTheme = 'light';

// ===== Utility Functions =====
function formatTime(seconds, lang = 'fa') {
    if (seconds < 60) {
        return lang === 'fa' ? 'کمتر از یک دقیقه' : 'Less than a minute';
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    const toFarsi = (num) => {
        const farsiDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
        return num.toString().split('').map(d => farsiDigits[d] || d).join('');
    };

    const hourStr = lang === 'fa' ? toFarsi(hours) : hours;
    const minStr = lang === 'fa' ? toFarsi(minutes) : minutes;

    if (hours === 0) {
        return lang === 'fa' ? `${minStr} دقیقه` : `${minutes} min`;
    } else if (minutes === 0) {
        return lang === 'fa' ? `${hourStr} ساعت` : `${hours} hr`;
    } else {
        return lang === 'fa'
            ? `${hourStr} ساعت و ${minStr} دقیقه`
            : `${hours} hr ${minutes} min`;
    }
}

function getRankEmoji(rank) {
    const medals = ['🥇', '🥈', '🥉'];
    return rank <= 3 ? medals[rank - 1] : `${rank}`;
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

function t(key) {
    return translations[currentLang][key] || key;
}

// ===== API Functions =====
async function fetchStats(period) {
    try {
        showLoading();
        const response = await fetch(`${API_URL}/stats/${period}`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        const data = await response.json();
        return data.stats;
    } catch (error) {
        console.error('Error fetching stats:', error);
        return [];
    } finally {
        hideLoading();
    }
}

async function searchUser(username) {
    try {
        showLoading();
        const response = await fetch(`${API_URL}/user/${encodeURIComponent(username)}`);
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error('Failed to search user');
        }
        return await response.json();
    } catch (error) {
        console.error('Error searching user:', error);
        return null;
    } finally {
        hideLoading();
    }
}

// ===== Render Functions =====
function renderStats(stats, containerId) {
    const container = document.getElementById(containerId);

    if (!stats || stats.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-text">${t('noStats')}</div>
            </div>
        `;
        return;
    }

    container.innerHTML = stats.map((item, index) => {
        const rank = index + 1;
        const rankClass = rank <= 3 ? `rank-${rank}` : '';
        const user = item.user;
        const fieldDisplay = user.field_display?.[currentLang] || user.field || '';
        const gradeDisplay = user.grade_display?.[currentLang] || user.grade || '';

        return `
            <div class="stat-card ${rankClass}">
                <div class="stat-card-left">
                    <div class="rank-badge">${getRankEmoji(rank)}</div>
                    <div class="stat-card-info">
                        <h4>${user.name || 'Unknown'}</h4>
                        <div class="stat-card-meta">
                            ${fieldDisplay} ${gradeDisplay ? '• ' + gradeDisplay : ''}
                        </div>
                    </div>
                </div>
                <div class="stat-card-time">
                    ${formatTime(item.total_seconds, currentLang)}
                </div>
            </div>
        `;
    }).join('');
}

function renderUserCard(data) {
    const container = document.getElementById('searchResults');

    if (!data) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-text">${t('noResults')}</div>
            </div>
        `;
        return;
    }

    const user = data.user;
    const stats = data.stats;
    const fieldDisplay = user.field_display?.[currentLang] || user.field || '';
    const gradeDisplay = user.grade_display?.[currentLang] || user.grade || '';

    container.innerHTML = `
        <div class="user-card">
            <div class="user-header">
                <h3 class="user-name">${user.name || 'Unknown'}</h3>
            </div>
            <div class="user-info">
                <div class="info-item">
                    <span class="info-label">${t('field')}</span>
                    <span class="info-value">${fieldDisplay}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">${t('grade')}</span>
                    <span class="info-value">${gradeDisplay}</span>
                </div>
            </div>
            <div class="user-stats">
                <div class="stat-box">
                    <div class="stat-label">${t('dailyTime')}</div>
                    <div class="stat-value">${formatTime(stats.daily, currentLang)}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">${t('weeklyTime')}</div>
                    <div class="stat-value">${formatTime(stats.weekly, currentLang)}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">${t('monthlyTime')}</div>
                    <div class="stat-value">${formatTime(stats.monthly, currentLang)}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">${t('totalTime')}</div>
                    <div class="stat-value">${formatTime(stats.total, currentLang)}</div>
                </div>
            </div>
        </div>
    `;
}

// ===== Language & Theme Functions =====
function updateTexts() {
    document.querySelectorAll('[data-fa]').forEach(el => {
        const text = currentLang === 'fa' ? el.dataset.fa : el.dataset.en;
        if (text) el.textContent = text;
    });

    document.querySelectorAll('[data-fa-placeholder]').forEach(el => {
        const placeholder = currentLang === 'fa'
            ? el.dataset.faPlaceholder
            : el.dataset.enPlaceholder;
        if (placeholder) el.placeholder = placeholder;
    });
}

function toggleLanguage() {
    currentLang = currentLang === 'fa' ? 'en' : 'fa';
    document.body.setAttribute('data-lang', currentLang);
    document.documentElement.lang = currentLang;
    document.documentElement.dir = currentLang === 'fa' ? 'rtl' : 'ltr';

    updateTexts();

    // Refresh current tab
    const activeTab = document.querySelector('.tab-btn.active');
    if (activeTab) {
        loadStats(activeTab.dataset.tab);
    }

    // Re-render search results if any
    const searchResults = document.getElementById('searchResults');
    if (searchResults.innerHTML) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput.value) {
            handleSearch();
        }
    }

    // Save preference
    localStorage.setItem('lang', currentLang);
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.body.classList.toggle('dark-mode');

    const icon = document.querySelector('.theme-icon');
    icon.textContent = currentTheme === 'light' ? '🌙' : '☀️';

    // Save preference
    localStorage.setItem('theme', currentTheme);
}

// ===== Event Handlers =====
function handleTabClick(e) {
    const tabBtn = e.target.closest('.tab-btn');
    if (!tabBtn) return;

    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

    tabBtn.classList.add('active');
    document.getElementById(tabBtn.dataset.tab).classList.add('active');

    // Load stats
    loadStats(tabBtn.dataset.tab);
}

async function handleSearch() {
    const username = document.getElementById('searchInput').value.trim();
    if (!username) return;

    const data = await searchUser(username);
    renderUserCard(data);
}

async function loadStats(period) {
    const stats = await fetchStats(period);
    renderStats(stats, `${period}Stats`);
}

// ===== Initialize =====
async function init() {
    // Load saved preferences
    const savedLang = localStorage.getItem('lang') || 'fa';
    const savedTheme = localStorage.getItem('theme') || 'light';

    if (savedLang !== 'fa') {
        currentLang = 'fa';
        toggleLanguage();
    }

    if (savedTheme === 'dark') {
        toggleTheme();
    }

    // Event listeners
    document.querySelector('.tabs').addEventListener('click', handleTabClick);
    document.getElementById('searchBtn').addEventListener('click', handleSearch);
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('langToggle').addEventListener('click', toggleLanguage);

    // Refresh buttons
    document.querySelectorAll('.refresh-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            loadStats(btn.dataset.period);
        });
    });

    // Load initial stats (daily)
    loadStats('daily');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
