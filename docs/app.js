document.addEventListener("DOMContentLoaded", () => {
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

    // ============================================================
    // HERO INTERACTIVE TERMINAL
    // ============================================================
    const heroTabCommands = {
        context: "schemap context",
        doctor: "schemap doctor",
        join: "schemap join users payments",
        agents: "schemap agents --targets codex,claude,cursor"
    };

    const commandElement = document.getElementById("type-cmd");
    let typeTimer = null;

    function typeCommandText(cmdText, callback) {
        if (typeTimer) clearTimeout(typeTimer);
        if (!commandElement) return;

        if (reduced) {
            commandElement.textContent = cmdText;
            if (callback) callback();
            return;
        }

        let idx = 0;
        commandElement.textContent = "";
        const step = () => {
            commandElement.textContent = cmdText.slice(0, idx++);
            if (idx <= cmdText.length) {
                typeTimer = setTimeout(step, 35);
            } else if (callback) {
                typeTimer = setTimeout(callback, 200);
            }
        };
        step();
    }

    // Initial typing
    typeCommandText(heroTabCommands.context);

    // Hero Command Tabs Click Handler
    document.querySelectorAll("[data-hero-cmd]").forEach((tab) => {
        tab.addEventListener("click", () => {
            const targetCmdKey = tab.dataset.heroCmd;
            const fullCmd = heroTabCommands[targetCmdKey] || `schemap ${targetCmdKey}`;

            // Update Tab UI
            document.querySelectorAll("[data-hero-cmd]").forEach((btn) => {
                const isSelected = btn === tab;
                btn.classList.toggle("is-active", isSelected);
                btn.style.background = isSelected ? "var(--surface2)" : "transparent";
                btn.style.color = isSelected ? "var(--text)" : "var(--muted)";
            });

            // Hide all panels initially
            document.querySelectorAll(".hero-output-panel").forEach((panel) => {
                panel.hidden = true;
            });

            // Type text and show corresponding output panel
            typeCommandText(fullCmd, () => {
                const targetPanel = document.getElementById(`hero-output-${targetCmdKey}`);
                if (targetPanel) {
                    targetPanel.hidden = false;
                }
            });
        });
    });

    // ============================================================
    // PROBLEM & PROOF TABS
    // ============================================================
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

    // ============================================================
    // BENCHMARK VISUALIZATION SUITE
    // ============================================================
    const benchmarkSchemas = {
        chinook: {
            name: "Chinook (Media Store)",
            tables: "11 tables · 64 cols",
            rawTokens: 995,
            schemapTokens: 536,
            reduction: "46.1%",
            latency: "0.92 ms",
            savedPerPrompt: "459 tokens",
            fableTeamSavings: "$242.35/yr",
            opusTeamSavings: "$121.18/yr",
            geminiTeamSavings: "$84.82/yr",
            sonnetTeamSavings: "$48.47/yr",
            deepseekTeamSavings: "$31.99/yr",
            flashTeamSavings: "$18.18/yr"
        },
        northwind: {
            name: "Northwind (ERP/Inventory)",
            tables: "13 tables · 86 cols",
            rawTokens: 1045,
            schemapTokens: 590,
            reduction: "43.5%",
            latency: "1.05 ms",
            savedPerPrompt: "455 tokens",
            fableTeamSavings: "$240.24/yr",
            opusTeamSavings: "$120.12/yr",
            geminiTeamSavings: "$84.08/yr",
            sonnetTeamSavings: "$48.05/yr",
            deepseekTeamSavings: "$31.71/yr",
            flashTeamSavings: "$18.02/yr"
        },
        pagila: {
            name: "Pagila (Complex DVD Rental)",
            tables: "15 tables · 82 cols",
            rawTokens: 1222,
            schemapTokens: 673,
            reduction: "44.9%",
            latency: "1.20 ms",
            savedPerPrompt: "549 tokens",
            fableTeamSavings: "$289.87/yr",
            opusTeamSavings: "$144.94/yr",
            geminiTeamSavings: "$101.46/yr",
            sonnetTeamSavings: "$57.97/yr",
            deepseekTeamSavings: "$38.26/yr",
            flashTeamSavings: "$21.74/yr"
        },
        saas: {
            name: "SaaS E-Commerce Platform",
            tables: "30 tables · 360 cols",
            rawTokens: 2572,
            schemapTokens: 532,
            reduction: "79.3%",
            latency: "1.77 ms",
            savedPerPrompt: "2,040 tokens",
            fableTeamSavings: "$1,077.12/yr",
            opusTeamSavings: "$538.56/yr",
            geminiTeamSavings: "$376.99/yr",
            sonnetTeamSavings: "$215.42/yr",
            deepseekTeamSavings: "$142.18/yr",
            flashTeamSavings: "$80.78/yr"
        },
        enterprise: {
            name: "Enterprise Production Scale",
            tables: "100 tables · 1,237 cols",
            rawTokens: 9027,
            schemapTokens: 1103,
            reduction: "87.8%",
            latency: "5.27 ms",
            savedPerPrompt: "7,924 tokens",
            fableTeamSavings: "$4,183.87/yr",
            opusTeamSavings: "$2,091.94/yr",
            geminiTeamSavings: "$1,464.36/yr",
            sonnetTeamSavings: "$836.77/yr",
            deepseekTeamSavings: "$552.27/yr",
            flashTeamSavings: "$313.79/yr"
        }
    };

    // Benchmark Main Tier Tabs
    document.querySelectorAll("[data-bench-tab]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const targetTier = btn.dataset.benchTab;

            document.querySelectorAll("[data-bench-tab]").forEach((b) => {
                b.classList.toggle("is-active", b === btn);
            });

            document.querySelectorAll(".bench-tier-panel").forEach((p) => {
                p.hidden = p.id !== `bench-panel-${targetTier}`;
            });
        });
    });

    // Tier 1 Schema Pills Selector
    document.querySelectorAll("[data-bench-schema]").forEach((pill) => {
        pill.addEventListener("click", () => {
            const schemaKey = pill.dataset.benchSchema;
            const data = benchmarkSchemas[schemaKey];
            if (!data) return;

            document.querySelectorAll("[data-bench-schema]").forEach((p) => {
                p.classList.toggle("is-active", p === pill);
            });

            // Update Text & Bars
            const rawValEl = document.getElementById("bench-raw-tokens");
            const schemapValEl = document.getElementById("bench-schemap-tokens");
            const reductionBadge = document.getElementById("bench-reduction-badge");
            const latencyBadge = document.getElementById("bench-latency-badge");
            const savedBadge = document.getElementById("bench-saved-badge");
            const schemapBar = document.getElementById("bench-schemap-bar");

            if (rawValEl) rawValEl.textContent = `${data.rawTokens.toLocaleString()} tokens (100%)`;
            if (schemapValEl) schemapValEl.textContent = `${data.schemapTokens.toLocaleString()} tokens (${(100 - parseFloat(data.reduction)).toFixed(1)}%)`;
            if (reductionBadge) reductionBadge.textContent = `${data.reduction} Token Reduction`;
            if (latencyBadge) latencyBadge.textContent = data.latency;
            if (savedBadge) savedBadge.textContent = data.savedPerPrompt;

            if (schemapBar) {
                const schemapPct = Math.max(8, (data.schemapTokens / data.rawTokens) * 100);
                schemapBar.style.width = `${schemapPct}%`;
                schemapBar.textContent = `${data.schemapTokens.toLocaleString()} tokens`;
            }

            // Update 2026 Next-Gen Frontier Model ROI Grid
            const fableEl = document.getElementById("bench-roi-fable");
            const opusEl = document.getElementById("bench-roi-opus");
            const geminiEl = document.getElementById("bench-roi-gemini");
            const sonnetEl = document.getElementById("bench-roi-sonnet");
            const deepseekEl = document.getElementById("bench-roi-deepseek");
            const flashEl = document.getElementById("bench-roi-flash");

            if (fableEl) fableEl.textContent = data.fableTeamSavings;
            if (opusEl) opusEl.textContent = data.opusTeamSavings;
            if (geminiEl) geminiEl.textContent = data.geminiTeamSavings;
            if (sonnetEl) sonnetEl.textContent = data.sonnetTeamSavings;
            if (deepseekEl) deepseekEl.textContent = data.deepseekTeamSavings;
            if (flashEl) flashEl.textContent = data.flashTeamSavings;
        });
    });

    // ============================================================
    // PACKAGE MANAGER SWITCHER
    // ============================================================
    const pmCommands = {
        pipx: {
            install: "pipx install schemap-tool",
            upgrade: "pipx upgrade schemap-tool",
            copyText: "Copy pipx install"
        },
        uv: {
            install: "uv tool install schemap-tool",
            upgrade: "uv tool upgrade schemap-tool",
            copyText: "Copy uv install"
        },
        pip: {
            install: "pip install schemap-tool",
            upgrade: "pip install --upgrade schemap-tool",
            copyText: "Copy pip install"
        }
    };
    let currentPm = "pipx";

    document.querySelectorAll("[data-pm]").forEach((btn) => {
        btn.addEventListener("click", () => {
            currentPm = btn.dataset.pm;
            const pmData = pmCommands[currentPm];
            if (!pmData) return;

            document.querySelectorAll("[data-pm]").forEach((b) => {
                const active = b === btn;
                b.classList.toggle("is-active", active);
                b.style.background = active ? "var(--blue)" : "transparent";
                b.style.color = active ? "var(--bg)" : "var(--muted)";
            });

            const installCode = document.getElementById("install-cmd-code");
            const upgradeCode = document.getElementById("upgrade-cmd-code");
            const copyBtn = document.getElementById("copy-install-btn");

            if (installCode) installCode.textContent = pmData.install;
            if (upgradeCode) upgradeCode.textContent = pmData.upgrade;
            if (copyBtn) copyBtn.textContent = pmData.copyText;
        });
    });

    const copy = document.getElementById("copy-install-btn");
    if (copy) {
        copy.addEventListener("click", async () => {
            try {
                const textToCopy = pmCommands[currentPm]?.install || "pipx install schemap-tool";
                await navigator.clipboard.writeText(textToCopy);
                const original = copy.textContent;
                copy.textContent = "Copied to clipboard!";
                setTimeout(() => copy.textContent = original, 1800);
            } catch {
                copy.textContent = "Copy unavailable";
            }
        });
    }

    // ============================================================
    // PRICING SUBSCRIPTION TOGGLE
    // ============================================================
    const plans = {
        monthly: ["$1.99", "/mo", "$8.99/mo", "78% launch discount", "Launch Special: Flexible monthly billing (Includes 7-Day Free Trial).", "https://buy.stripe.com/dRm00jeG13kpfoA131dIA01"],
        quarterly: ["$4.99", "/3mo", "$24.99 / 3mo", "80% launch discount", "Launch Special: Billed every three months (~$1.66/mo).", "https://buy.stripe.com/9B6bJ1gO94otekw275dIA02"],
        semiannual: ["$8.99", "/6mo", "$45.99 / 6mo", "80% launch discount", "Launch Special: Billed every six months (~$1.50/mo).", "https://buy.stripe.com/9B6fZh0Pb6wB0tG5jhdIA03"],
        annual: ["$15.99", "/yr", "$79.99/yr", "80% launch discount", "Best Value Launch Deal: Only ~$1.33/mo.", "https://buy.stripe.com/6oU8wP9lH3kpgsE275dIA04"]
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

    // ============================================================
    // MATRIX RAIN ANIMATION
    // ============================================================
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

    // Dynamic Founder Seats Counter (200 Cap)
    const claimedEl = document.getElementById("founder-claimed-count");
    const remainingEl = document.getElementById("founder-remaining-count");
    const progressBarEl = document.getElementById("founder-progress-bar");

    if (claimedEl && remainingEl && progressBarEl) {
        const TOTAL_CAP = 200;
        
        async function fetchFounderSeats() {
            try {
                const res = await fetch("https://schemap-license-api.alansyahmi2004.workers.dev/v1/stats/founders");
                if (res.ok) {
                    const data = await res.json();
                    const claimed = Math.min(TOTAL_CAP, Math.max(0, data.claimed || 0));
                    updateFounderUI(claimed);
                    return;
                }
            } catch (e) {
                // Fallback to initial seats count
            }
            updateFounderUI(0);
        }

        function updateFounderUI(claimedCount) {
            const remaining = Math.max(0, TOTAL_CAP - claimedCount);
            const percentage = Math.min(100, Math.max(5, (claimedCount / TOTAL_CAP) * 100));
            
            claimedEl.textContent = claimedCount;
            remainingEl.textContent = remaining;
            progressBarEl.style.width = `${percentage}%`;
        }

        fetchFounderSeats();
    }
});
