# ORAEX Documentation Site

Esta pasta contém o **site público** do projeto ORAEX, hospedado via GitHub Pages.

## 🌐 Acesso

Após configurar o GitHub Pages no repositório:

- **URL:** `https://jonathanfferreira.github.io/oraex-nprod/`

## 📁 Estrutura

```
docs/
├── index.html      # Página principal
├── style.css       # Estilos (Glassmorphism)
├── script.js       # Animações e terminal
└── assets/         # Logos e imagens
```

## 🔧 Como atualizar

1. Edite os arquivos em `presentation_site/`
2. Copie para `docs/`:

   ```powershell
   Copy-Item -Recurse -Force "presentation_site\*" "docs\"
   ```

3. Commit e push:

   ```bash
   git add docs/
   git commit -m "docs: update site"
   git push
   ```

## ⚙️ Configuração GitHub Pages

1. Vá em **Settings > Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` (ou `master`)
4. Folder: `/docs`
5. Save

O site estará live em ~1 minuto.
