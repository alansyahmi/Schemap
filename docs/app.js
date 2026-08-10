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
        monthly: ["$7.99", "/mo", "$9.99/mo", "20% off", "Flexible monthly billing.", "https://buy.stripe.com/dRm00jeG13kpfoA131dIA01"],
        quarterly: ["$21.99", "/3mo", "$27.99 / 3mo", "21% off", "Billed every three months.", "https://buy.stripe.com/9B6bJ1gO94otekw275dIA02"],
        semiannual: ["$39.99", "/6mo", "$49.99 / 6mo", "20% off", "Billed every six months.", "https://buy.stripe.com/9B6fZh0Pb6wB0tG5jhdIA03"],
        annual: ["$69.99", "/yr", "$99.99/yr", "30% off", "Best value: save $30 annually.", "https://buy.stripe.com/6oU8wP9lH3kpgsE275dIA04"]
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
            document.getElementById("sub-original").textContent = plan[2];
            document.getElementById("sub-discount").textContent = plan[3];
            document.getElementById("sub-desc").textContent = plan[4];
            document.getElementById("sub-checkout-btn").href = plan[5];
        });
    });

    const canvas = document.getElementById("matrix-bg");
    if (canvas && !reduced) {
        const ctx = canvas.getContext("2d");
        const hero = document.querySelector(".hero");

        function resizeCanvas() {
            canvas.width = hero ? hero.clientWidth : window.innerWidth;
            canvas.height = hero ? hero.clientHeight : window.innerHeight;
            canvas.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none";
        }

        window.addEventListener("resize", resizeCanvas);
        resizeCanvas();

        const rawSQL = "CREATE TABLE INSERT INTO SELECT FROM WHERE JOIN ON GROUP BY ORDER BY PRIMARY KEY FOREIGN KEY VARCHAR INT TIMESTAMP".split(" ");
        const pureContext = "[TABLE] [PK] [COL] [REL] -> PATH".split(" ");

        const fontSize = 14;
        let columns = Math.floor(canvas.width / (fontSize * 2.5));
        let drops = [];
        const tailLength = 10;

        for (let x = 0; x < columns; x++) {
            drops[x] = {
                y: Math.random() * -100,
                speed: Math.random() * 0.1 + 0.05,
                chars: Array(tailLength).fill('')
            };
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = fontSize + 'px "JetBrains Mono", monospace';

            for (let i = 0; i < drops.length; i++) {
                let drop = drops[i];

                const isPurified = drop.y * fontSize > canvas.height / 2;
                const newChar = isPurified
                    ? pureContext[Math.floor(Math.random() * pureContext.length)]
                    : rawSQL[Math.floor(Math.random() * rawSQL.length)];

                if (Math.floor(drop.y) > Math.floor(drop.y - drop.speed)) {
                    drop.chars.unshift(newChar);
                    drop.chars.pop();
                }

                for (let j = 0; j < drop.chars.length; j++) {
                    const charY = (drop.y - j) * fontSize;
                    if (charY < 0 || !drop.chars[j]) continue;

                    const charIsPurified = charY > canvas.height / 2;
                    const alpha = Math.max(0, 1 - (j / tailLength));
                    const xCoord = i * (fontSize * 2.5);

                    if (charIsPurified) {
                        ctx.fillStyle = `rgba(52, 211, 153, ${alpha * 0.4})`;
                    } else {
                        ctx.fillStyle = `rgba(255, 95, 86, ${alpha * 0.15})`;
                    }

                    ctx.fillText(drop.chars[j], xCoord, charY);
                }

                if (drop.y * fontSize > canvas.height + (tailLength * fontSize) && Math.random() > 0.985) {
                    drop.y = 0;
                    drop.chars = Array(tailLength).fill('');
                }

                drop.y += drop.speed;
            }
            requestAnimationFrame(draw);
        }

        draw();
    }
});
