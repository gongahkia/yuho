;; --- SAMPLE CONFIG ---
;; !!! be sure you know what each part does before you copy this wholesale !!!

(require 'package)
(add-to-list 'package-archives '("melpa" . "https://melpa.org/packages/") t)
(package-initialize)

(unless (package-installed-p 'use-package)
  (package-refresh-contents)
  (package-install 'use-package))

(require 'use-package)

;; --- install and configure lsp-mode ---

(use-package lsp-mode
  :ensure t
  :commands lsp
  :hook (yuho-mode . lsp)
  :config
  ;; Path to your LSP server
  (setq lsp-server-command '("node" "../base/index.js")))

;; --- install and configure lsp-ui ---

(use-package lsp-ui
  :ensure t
  :after lsp-mode
  :config
  (setq lsp-ui-doc-enable t
        lsp-ui-sideline-enable t
        lsp-ui-imenu-enable t
        lsp-ui-flycheck-enable t))

;; --- install and configure company-mode ---

(use-package company
  :ensure t
  :hook (lsp-mode . company-mode)
  :config
  (setq company-idle-delay 0.2)
  (setq company-minimum-prefix-length 1))

;; --- define yuho-mode ---

(defun yuho-mode ()
  "Major mode for editing Yuho files."
  (interactive)
  (kill-all-local-variables)
  (setq major-mode 'yuho-mode)
  (setq mode-name "Yuho")
  (run-mode-hooks 'yuho-mode-hook))

;; --- file association ---

(add-to-list 'auto-mode-alist '("\\.yh\\'" . yuho-mode))
