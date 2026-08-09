document.addEventListener('DOMContentLoaded', () => {
    // Typing effect for the terminal
    const cmdElement = document.getElementById('type-cmd');
    const originalText = "uv run schemap generate --format=ai";
    cmdElement.textContent = "";

    // Add cursor
    const cursor = document.createElement('span');
    cursor.className = 'cursor';
    cmdElement.parentNode.appendChild(cursor);

    let i = 0;
    const typeInterval = setInterval(() => {
        if (i < originalText.length) {
            cmdElement.textContent += originalText.charAt(i);
            i++;
        } else {
            clearInterval(typeInterval);
            // Wait 500ms then remove cursor and show output
            setTimeout(() => {
                cursor.remove();
                showOutput();
            }, 500);
        }
    }, 80);

    function showOutput() {
        // Show up to 10 output lines
        const delays = [300, 600, 800, 900, 1000, 1300, 1600, 1900, 2200, 2500];
        for (let j = 1; j <= 10; j++) {
            setTimeout(() => {
                const el = document.getElementById(`out-${j}`);
                if (el) {
                    el.classList.remove('hidden');
                }
            }, delays[j - 1] || 3000);
        }
    }

    // Copy Install Command functionality
    const copyBtn = document.getElementById('copy-install-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            navigator.clipboard.writeText('pip install schemap-tool').then(() => {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied to Clipboard!';
                copyBtn.style.color = 'var(--success)';
                copyBtn.style.borderColor = 'var(--success)';

                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.style.color = '';
                    copyBtn.style.borderColor = '';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        });
    }

    // Matrix-Style SQL Purification Background (Tweaked for sparsity and slower speed)
    const canvas = document.getElementById('matrix-bg');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        
        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = document.querySelector('.hero').offsetHeight;
        }
        
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        const rawSQL = "CREATE TABLE INSERT INTO SELECT FROM WHERE JOIN ON GROUP BY ORDER BY PRIMARY KEY FOREIGN KEY VARCHAR INT TIMESTAMP".split(" ");
        const pureContext = "[TABLE] [PK] [COL] [REL] -> PATH".split(" ");
        
        const fontSize = 14;
        // Increase the divisor to drastically reduce the number of columns (less text)
        let columns = Math.floor(canvas.width / (fontSize * 2.5));
        
        // Instead of a single y-coordinate, track the entire tail of characters
        let drops = [];
        const tailLength = 10; // Shorter tail to reduce text density
        
        for (let x = 0; x < columns; x++) {
            drops[x] = {
                y: Math.random() * -100, // Head position
                // Drastically slower speed: max 0.15, min 0.05
                speed: Math.random() * 0.1 + 0.05,
                chars: Array(tailLength).fill('') // Store the characters in the tail
            };
        }

        function draw() {
            // MUST use clearRect to preserve the beautiful CSS radial glow behind the canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = fontSize + 'px "JetBrains Mono", monospace';
            
            for (let i = 0; i < drops.length; i++) {
                let drop = drops[i];
                
                // Determine new character for the head
                const isPurified = drop.y * fontSize > canvas.height / 2;
                const newChar = isPurified 
                    ? pureContext[Math.floor(Math.random() * pureContext.length)]
                    : rawSQL[Math.floor(Math.random() * rawSQL.length)];
                
                // Shift array: remove last, add new at beginning
                if (Math.floor(drop.y) > Math.floor(drop.y - drop.speed)) {
                     drop.chars.unshift(newChar);
                     drop.chars.pop();
                }

                // Draw the tail
                for (let j = 0; j < drop.chars.length; j++) {
                    const charY = (drop.y - j) * fontSize;
                    if (charY < 0 || !drop.chars[j]) continue;
                    
                    const charIsPurified = charY > canvas.height / 2;
                    
                    // Alpha fades out the further back in the tail we are
                    const alpha = Math.max(0, 1 - (j / tailLength));
                    
                    // X-coordinate is spaced out by fontSize * 2.5
                    const xCoord = i * (fontSize * 2.5);
                    
                    if (charIsPurified) {
                        ctx.fillStyle = `rgba(52, 211, 153, ${alpha * 0.4})`; // Green
                    } else {
                        ctx.fillStyle = `rgba(255, 95, 86, ${alpha * 0.15})`; // Faint red
                    }
                    
                    ctx.fillText(drop.chars[j], xCoord, charY);
                }
                
                if (drop.y * fontSize > canvas.height + (tailLength * fontSize) && Math.random() > 0.985) {
                    drop.y = 0;
                    drop.chars = Array(tailLength).fill('');
                }
                
                drop.y += drop.speed;
            }
        }
        
        // Use requestAnimationFrame for smoother rendering instead of setInterval
        function animate() {
            draw();
            requestAnimationFrame(animate);
        }
        animate();
    }

    // Export Formats Showcase Tab Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and panes
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked button
            btn.classList.add('active');

            // Find matching pane and activate it
            const targetId = btn.getAttribute('data-target');
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });

    // Dynamic Subscription Interval Switcher
    const subData = {
        monthly: {
            title: "Pro Subscription",
            price: "$7.99",
            period: "/mo",
            desc: '2026 Founder Price <span style="text-decoration: line-through; color: var(--text-secondary);">$9.99/mo</span>',
            badge: "Flexible Monthly",
            discount: "20% OFF",
            saveTag: "Cancel anytime",
            link: "https://buy.stripe.com/dRm00jeG13kpfoA131dIA01"
        },
        quarterly: {
            title: "Pro Subscription",
            price: "$21.99",
            period: "/3mo",
            desc: '2026 Founder Price <span style="text-decoration: line-through; color: var(--text-secondary);">$27.99 / 3mo</span>',
            badge: "Save 21%",
            discount: "21% OFF",
            saveTag: "Billed every 3 months",
            link: "https://buy.stripe.com/9B6bJ1gO94otekw275dIA02"
        },
        semiannual: {
            title: "Pro Subscription",
            price: "$39.99",
            period: "/6mo",
            desc: '2026 Founder Price <span style="text-decoration: line-through; color: var(--text-secondary);">$49.99 / 6mo</span>',
            badge: "Save 20%",
            discount: "20% OFF",
            saveTag: "Billed every 6 months",
            link: "https://buy.stripe.com/9B6fZh0Pb6wB0tG5jhdIA03"
        },
        annual: {
            title: "Pro Subscription",
            price: "$79.99",
            period: "/yr",
            desc: '2026 Founder Price <span style="text-decoration: line-through; color: var(--text-secondary);">$99.99/yr</span>',
            badge: "Best Value (Save 20%)",
            discount: "20% OFF",
            saveTag: "<strong>2 months free</strong>&nbsp;equivalent",
            link: "https://buy.stripe.com/6oU8wP9lH3kpgsE275dIA04"
        }
    };

    window.switchSubInterval = function(interval, btnElement) {
        const subBtns = document.querySelectorAll('.sub-btn');
        const subTitle = document.getElementById('sub-title');
        const subPrice = document.getElementById('sub-price');
        const subDesc = document.getElementById('sub-desc');
        const subBadge = document.getElementById('sub-badge');
        const subDiscountTag = document.getElementById('sub-discount-tag');
        const subSaveTag = document.getElementById('sub-save-tag');
        const subCheckoutBtn = document.getElementById('sub-checkout-btn');

        subBtns.forEach(b => {
            b.classList.remove('active');
            b.style.backgroundColor = 'transparent';
            b.style.color = 'var(--text-secondary)';
        });

        if (btnElement) {
            btnElement.classList.add('active');
            btnElement.style.backgroundColor = 'var(--accent)';
            btnElement.style.color = '#ffffff';
        }

        const data = subData[interval];
        if (data) {
            if (subTitle) subTitle.textContent = data.title;
            if (subPrice) subPrice.innerHTML = `${data.price}<span class="period">${data.period}</span>`;
            if (subDesc) subDesc.innerHTML = data.desc;
            if (subBadge) subBadge.textContent = data.badge;
            if (subDiscountTag) subDiscountTag.textContent = data.discount;
            if (subSaveTag) subSaveTag.innerHTML = data.saveTag;
            if (subCheckoutBtn) subCheckoutBtn.href = data.link;
        }
    };
});
