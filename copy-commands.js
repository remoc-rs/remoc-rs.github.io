(() => {
    if (!window.isSecureContext || !navigator.clipboard) {
        return;
    }

    for (const code of document.querySelectorAll("pre.cmd:not([data-no-copy]) > code")) {
        const pre = code.parentElement;
        const wrapper = document.createElement("div");
        wrapper.className = "command-block";
        pre.before(wrapper);
        wrapper.append(pre);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "copy-button";
        button.dataset.copy = code.textContent.trim();
        button.setAttribute("aria-label", "Copy command");
        button.innerHTML = '<span class="icon copy" aria-hidden="true"></span>'
            + '<span class="icon check" aria-hidden="true"></span>';
        wrapper.append(button);
    }

    const status = document.createElement("p");
    status.className = "copy-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-atomic", "true");
    document.body.append(status);

    for (const button of document.querySelectorAll("button[data-copy]")) {
        const label = button.getAttribute("aria-label");
        button.title = label;
        let resetTimeout;
        button.addEventListener("click", async () => {
            clearTimeout(resetTimeout);
            try {
                await navigator.clipboard.writeText(button.dataset.copy);
                button.classList.add("copied");
                button.setAttribute("aria-label", "Command copied");
                status.textContent = "";
                resetTimeout = setTimeout(() => {
                    button.classList.remove("copied");
                    button.setAttribute("aria-label", label);
                }, 1500);
            } catch (error) {
                button.classList.remove("copied");
                button.setAttribute("aria-label", label);
                status.textContent = "Could not copy. Select the command and copy it manually.";
                console.error("Could not copy command.", error);
            }
        });
    }
    document.documentElement.classList.add("js");
})();
