document.addEventListener('DOMContentLoaded', () => {
    // Typing effect for the terminal
    const cmdElement = document.getElementById('type-cmd');
    const originalText = "uv run schemap generate";
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
    }, 100);

    function showOutput() {
        const delays = [400, 800, 1000, 1100, 1300];
        for (let j = 1; j <= 5; j++) {
            setTimeout(() => {
                const el = document.getElementById(`out-${j}`);
                if (el) {
                    el.classList.remove('hidden');
                }
            }, delays[j-1]);
        }
    }
});
