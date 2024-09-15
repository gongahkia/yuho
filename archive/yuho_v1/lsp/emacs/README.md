# Emacs

Add this to your `init.el` file.

```el
(require 'lsp-mode)
(setq lsp-server-command '("node" "../base/index.js"))
(add-hook 'yuho-mode-hook #'lsp)
```
