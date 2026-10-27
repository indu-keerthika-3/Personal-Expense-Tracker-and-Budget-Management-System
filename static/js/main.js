/**
 * Personal Expense Tracker - Main Interactivity Engine
 * Handles theme switching, mobile sidebar navigation, dynamic category switching,
 * modal dialogs, and client-side form validation.
 */

document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    initMobileNav();
    initCategorySwitcher();
    initDeleteModals();
    initFlashAlerts();
});

// ==========================================
// 1. THEME SWITCHER (LIGHT / DARK)
// ==========================================
function initTheme() {
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const currentTheme = localStorage.getItem("expense_theme") || "light";
    document.documentElement.setAttribute("data-theme", currentTheme);
    updateThemeIcon(currentTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", function () {
            const activeTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = activeTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("expense_theme", newTheme);
            updateThemeIcon(newTheme);

            // Re-render any charts to match the new theme colors if charts.js is present
            if (window.refreshAllCharts) {
                window.refreshAllCharts();
            }
        });
    }
}

function updateThemeIcon(theme) {
    const sunIcon = document.getElementById("sunIcon");
    const moonIcon = document.getElementById("moonIcon");
    if (sunIcon && moonIcon) {
        if (theme === "dark") {
            sunIcon.style.display = "block";
            moonIcon.style.display = "none";
        } else {
            sunIcon.style.display = "none";
            moonIcon.style.display = "block";
        }
    }
}

// ==========================================
// 2. MOBILE SIDEBAR NAVIGATION
// ==========================================
function initMobileNav() {
    const mobileToggle = document.getElementById("mobileToggle");
    const sidebar = document.getElementById("appSidebar");
    const overlay = document.getElementById("sidebarBackdrop");

    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
            if (overlay) overlay.classList.toggle("active");
        });

        if (overlay) {
            overlay.addEventListener("click", function () {
                sidebar.classList.remove("open");
                overlay.classList.remove("active");
            });
        }
    }
}

// ==========================================
// 3. DYNAMIC CATEGORY SWITCHER (INCOME / EXPENSE)
// ==========================================
const EXPENSE_CATEGORIES = [
    "Food", "Transportation", "Shopping", "Education", "Rent",
    "Utilities", "Healthcare", "Entertainment", "Travel", "Personal Care", "Other"
];

const INCOME_CATEGORIES = [
    "Salary", "Freelancing", "Business", "Scholarship", "Investment Income", "Other"
];

function initCategorySwitcher() {
    const typeRadios = document.querySelectorAll('input[name="transaction_type"]');
    const categorySelect = document.getElementById("categorySelect");

    if (typeRadios.length > 0 && categorySelect) {
        const updateCategories = function () {
            const selectedType = document.querySelector('input[name="transaction_type"]:checked')?.value || "Expense";
            const currentSelected = categorySelect.getAttribute("data-selected") || categorySelect.value;
            const categories = (selectedType === "Income") ? INCOME_CATEGORIES : EXPENSE_CATEGORIES;

            categorySelect.innerHTML = "";
            categories.forEach(function (cat) {
                const opt = document.createElement("option");
                opt.value = cat;
                opt.textContent = cat;
                if (cat === currentSelected) {
                    opt.selected = true;
                }
                categorySelect.appendChild(opt);
            });
        };

        typeRadios.forEach(radio => radio.addEventListener("change", updateCategories));
        // Run once on load
        updateCategories();
    }
}

// ==========================================
// 4. DELETE CONFIRMATION MODAL
// ==========================================
let pendingDeleteForm = null;

function initDeleteModals() {
    const deleteModal = document.getElementById("deleteModal");
    const confirmBtn = document.getElementById("confirmDeleteBtn");
    const cancelBtn = document.getElementById("cancelDeleteBtn");
    const deleteDesc = document.getElementById("deleteModalDesc");

    document.querySelectorAll("[data-action='delete-trigger']").forEach(button => {
        button.addEventListener("click", function (e) {
            e.preventDefault();
            const formId = this.getAttribute("data-form-id");
            const itemDescription = this.getAttribute("data-item-name") || "this transaction";
            pendingDeleteForm = document.getElementById(formId);

            if (deleteDesc) {
                deleteDesc.textContent = `Are you sure you want to permanently delete "${itemDescription}"? This action cannot be undone.`;
            }

            if (deleteModal) {
                deleteModal.classList.add("active");
            }
        });
    });

    if (confirmBtn) {
        confirmBtn.addEventListener("click", function () {
            if (pendingDeleteForm) {
                pendingDeleteForm.submit();
            }
        });
    }

    if (cancelBtn && deleteModal) {
        cancelBtn.addEventListener("click", function () {
            deleteModal.classList.remove("active");
            pendingDeleteForm = null;
        });
    }

    // Close on outside click
    if (deleteModal) {
        deleteModal.addEventListener("click", function (e) {
            if (e.target === deleteModal) {
                deleteModal.classList.remove("active");
                pendingDeleteForm = null;
            }
        });
    }
}

// ==========================================
// 5. FLASH ALERTS AUTO-DISMISS
// ==========================================
function initFlashAlerts() {
    document.querySelectorAll(".alert").forEach(alert => {
        const closeBtn = alert.querySelector(".alert-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => alert.remove());
        }
        // Auto dismiss after 6 seconds for success/info alerts
        if (alert.classList.contains("alert-success") || alert.classList.contains("alert-info")) {
            setTimeout(() => {
                alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
                alert.style.opacity = "0";
                alert.style.transform = "translateY(-10px)";
                setTimeout(() => alert.remove(), 400);
            }, 6000);
        }
    });
}

