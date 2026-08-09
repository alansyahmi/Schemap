document.addEventListener("DOMContentLoaded", () => {
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const command = "schemap context";
    const commandElement = document.getElementById("type-cmd");
    const terminalOutput = document.getElementById("terminal-output");

    if (commandElement && terminalOutput) {
        if (reduced) {
            commandElement.textContent = command;
            terminalOutput.hidden = false;
        } else {
            let index = 0;
            const type = () => {
                commandElement.textContent = command.slice(0, index++);
                if (index <= command.length) setTimeout(type, 55);
                else setTimeout(() => terminalOutput.hidden = false, 350);
            };
            type();
        }
    }

    document.querySelectorAll("[data-proof-tab]").forEach((tab) => {
        tab.addEventListener("click", () => {
            const target = tab.dataset.proofTab;
            document.querySelectorAll("[data-proof-tab]").forEach((item) => {
                const active = item === tab;
                item.classList.toggle("is-active", active);
                item.setAttribute("aria-selected", String(active));
            });
            document.querySelectorAll("[data-proof-panel]").forEach((panel) => {
                const active = panel.dataset.proofPanel === target;
                panel.hidden = !active;
                panel.classList.toggle("is-active", active);
            });
        });
    });

    const copy = document.getElementById("copy-install-btn");
    if (copy) {
        copy.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText("pip install schemap-tool");
                const original = copy.textContent;
                copy.textContent = "Copied to clipboard";
                setTimeout(() => copy.textContent = original, 1800);
            } catch {
                copy.textContent = "Copy unavailable";
            }
        });
    }

    const plans = {
        monthly: ["$7.99", "/mo", "Flexible monthly billing.", "https://buy.stripe.com/dRm00jeG13kpfoA131dIA01"],
        quarterly: ["$21.99", "/3mo", "Billed every three months.", "https://buy.stripe.com/9B6bJ1gO94otekw275dIA02"],
        semiannual: ["$39.99", "/6mo", "Billed every six months.", "https://buy.stripe.com/9B6fZh0Pb6wB0tG5jhdIA03"],
        annual: ["$79.99", "/yr", "Best value: two months free equivalent.", "https://buy.stripe.com/6oU8wP9lH3kpgsE275dIA04"]
    };
    document.querySelectorAll("[data-sub-interval]").forEach((button) => {
        button.addEventListener("click", () => {
            const plan = plans[button.dataset.subInterval];
            if (!plan) return;
            document.querySelectorAll("[data-sub-interval]").forEach((item) => {
                item.classList.toggle("is-active", item === button);
            });
            document.getElementById("sub-price").firstChild.textContent = plan[0];
            document.getElementById("sub-period").textContent = plan[1];
            document.getElementById("sub-desc").textContent = plan[2];
            document.getElementById("sub-checkout-btn").href = plan[3];
        });
    });

    const canvas = document.getElementById("matrix-bg");
    if (canvas && !reduced) {
        const context = canvas.getContext("2d");
        const hero = document.querySelector(".hero");
        const raw = ["CREATE", "TABLE", "SELECT", "FROM", "JOIN", "WHERE", "PRIMARY", "FOREIGN", "KEY"];
        const compiled = ["TABLE", "PK", "COL", "REL", "PATH"];
        let width = 0;
        let height = 0;
        let drops = [];

        const resize = () => {
            width = canvas.width = hero.clientWidth;
            height = canvas.height = hero.clientHeight;
            canvas.style.cssText = "position:absolute;inset:0;width:100%;height:100%;opacity:.7;pointer-events:none";
            drops = Array.from({ length: Math.ceil(width / 30) }, () => ({
                y: Math.random() * -height / 16,
                speed: 0.18 + Math.random() * 0.28
            }));
        };
        const draw = () => {
            context.clearRect(0, 0, width, height);
            context.font = '11px "JetBrains Mono"';
            drops.forEach((drop, column) => {
                const y = drop.y * 16;
                const purified = y > height * 0.52;
                const words = purified ? compiled : raw;
                context.fillStyle = purified ? "rgba(80,211,154,.2)" : "rgba(141,184,255,.12)";
                context.fillText(words[Math.floor(Math.random() * words.length)], column * 30, y);
                drop.y += drop.speed;
                if (y > height + 30) drop.y = 0;
            });
            requestAnimationFrame(draw);
        };
        resize();
        addEventListener("resize", resize);
        draw();
    }
});
