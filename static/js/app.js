function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop().split(";").shift();
    }
    return "";
}

function formatDuration(seconds) {
    const safe = Math.max(seconds, 0);
    const hours = String(Math.floor(safe / 3600)).padStart(2, "0");
    const minutes = String(Math.floor((safe % 3600) / 60)).padStart(2, "0");
    const secs = String(safe % 60).padStart(2, "0");
    return `${hours}:${minutes}:${secs}`;
}

function bindTimerCards() {
    document.querySelectorAll("[data-start-time]").forEach((card) => {
        const display = card.querySelector("[data-timer-display]");
        if (!display) {
            return;
        }
        const start = new Date(card.dataset.startTime);
        const tick = () => {
            const seconds = Math.floor((Date.now() - start.getTime()) / 1000);
            display.textContent = formatDuration(seconds);
        };
        tick();
        window.setInterval(tick, 1000);
    });
}

function bindNavToggle() {
    const toggle = document.querySelector("[data-nav-toggle]");
    const backdrop = document.querySelector("[data-nav-backdrop]");
    const sidebar = document.querySelector(".sidebar");
    if (!toggle || !sidebar) {
        return;
    }

    const closeNav = () => {
        document.body.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
    };

    const openNav = () => {
        document.body.classList.add("nav-open");
        toggle.setAttribute("aria-expanded", "true");
    };

    toggle.addEventListener("click", () => {
        if (document.body.classList.contains("nav-open")) {
            closeNav();
            return;
        }
        openNav();
    });

    backdrop?.addEventListener("click", closeNav);
    document.querySelectorAll(".nav-link, .nav-button").forEach((element) => {
        element.addEventListener("click", closeNav);
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeNav();
        }
    });
}

async function handleTimerAction(button) {
    const action = button.dataset.action;
    const taskId = button.dataset.taskId;
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = action === "start" ? "Starting..." : "Stopping...";

    try {
        const response = await fetch(`/time/${action}/${taskId}/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest",
            },
        });
        const payload = await response.json();
        if (!response.ok) {
            window.alert(payload.detail || "Request failed.");
            return;
        }
        window.location.reload();
    } finally {
        button.disabled = false;
        button.textContent = originalLabel;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    bindNavToggle();
    bindTimerCards();
    document.querySelectorAll(".timer-action").forEach((button) => {
        button.addEventListener("click", () => {
            handleTimerAction(button);
        });
    });
});
