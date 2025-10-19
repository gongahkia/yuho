/* Extra JavaScript for Yuho documentation */

// Initialize mermaid diagrams
document.addEventListener('DOMContentLoaded', function() {
    // Mermaid configuration
    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
        });
    }

    // Add copy button to code blocks
    document.querySelectorAll('pre code').forEach(function(codeBlock) {
        // Create copy button
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.textContent = 'Copy';
        button.style.cssText = 'position:absolute;top:5px;right:5px;padding:4px 8px;background:#3f51b5;color:white;border:none;border-radius:4px;cursor:pointer;font-size:12px;';
        
        // Make pre position relative
        const pre = codeBlock.parentNode;
        pre.style.position = 'relative';
        pre.appendChild(button);
        
        // Copy to clipboard on click
        button.addEventListener('click', function() {
            const text = codeBlock.textContent;
            navigator.clipboard.writeText(text).then(function() {
                button.textContent = 'Copied!';
                setTimeout(function() {
                    button.textContent = 'Copy';
                }, 2000);
            });
        });
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

