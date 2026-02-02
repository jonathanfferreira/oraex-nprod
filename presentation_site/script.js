document.addEventListener('DOMContentLoaded', () => {
    // --- Typing Effect for Terminal ---
    const terminalOutput = document.getElementById('terminal-output');
    const commands = [
        { text: "> python oracle_healthcheck.py --json", delay: 800 },
        { text: "Checking connectivity... [OK]", delay: 1500, color: "text-muted" },
        { text: "Validating Tablespaces... [WARNING]", delay: 2200, color: "warning" },
        { text: "  -> TS_DATA usage at 92%", delay: 2400, color: "warning" },
        { text: "Checking ASM Disk Groups... [OK]", delay: 3000, color: "success" },
        { text: "Generation Report: logs/healthcheck_2026.json", delay: 3500 },
        { text: "Done in 0.45s.", delay: 3700, color: "success" }
    ];

    let cmdIndex = 0;

    function typeCommand() {
        if (cmdIndex < commands.length) {
            const cmd = commands[cmdIndex];
            const p = document.createElement('div');

            p.textContent = cmd.text;
            if (cmd.color) p.classList.add(cmd.color);

            if (cmd.text.startsWith(">")) {
                p.style.color = "#fff";
                p.style.fontWeight = "bold";
            } else if (cmd.color === 'warning') {
                p.style.color = 'var(--warning)';
            } else if (cmd.color === 'success') {
                p.style.color = 'var(--success)';
            } else {
                p.style.color = 'var(--text-muted)';
            }

            terminalOutput.appendChild(p);
            cmdIndex++;
            setTimeout(typeCommand, 300 + Math.random() * 500); // Random typing speed variance
        }
    }

    // Start typing when terminal is in view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && cmdIndex === 0) {
                typeCommand();
            }
        });
    });

    observer.observe(document.getElementById('terminal-section'));

    // --- Smooth Scroll ---
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // --- Entrance Animations ---
    const sections = document.querySelectorAll('.animate-entrance');
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    sections.forEach(s => {
        s.style.opacity = '0';
        s.style.transform = 'translateY(20px)';
        s.style.transition = 'all 0.8s ease-out';
        sectionObserver.observe(s);
    });
});
