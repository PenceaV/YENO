# Configurare Tailwind CSS pentru YENO

## Instalare și configurare

Tailwind CSS este deja configurat în proiect! Iată ce a fost făcut:

### 1. Aplicația `tema`
- Aplicația `tema` a fost creată pentru gestionarea Tailwind CSS
- Conține configurația Tailwind și fișierele CSS generate

### 2. Structura fișierelor
```
tema/
├── static_src/          # Fișierele sursă pentru Tailwind
│   ├── css/
│   │   └── styles.css   # Fișierul CSS principal cu directivele Tailwind
│   ├── package.json    # Dependențele Node.js
│   └── tailwind.config.js  # Configurația Tailwind
└── static/              # Fișierele CSS compilate
    └── css/
        └── styles.css   # CSS-ul generat de Tailwind
```

### 3. Comenzi utile

#### Pentru development (watch mode - recompilează automat la modificări):
```bash
cd tema/static_src
npm run dev
```

#### Pentru build (compilare o singură dată):
```bash
cd tema/static_src
npm run build
```

### 4. Actualizare CSS

După ce modifici clasele Tailwind în template-uri, trebuie să recompilezi CSS-ul:

1. Deschide un terminal în directorul `tema/static_src`
2. Rulează `npm run build` (sau `npm run dev` pentru watch mode)
3. CSS-ul va fi generat în `tema/static/css/styles.css`

### 5. Template-uri

Template-urile folosesc acum fișierul CSS generat în loc de CDN:
- `sondaje/templates/sondaje/base.html` - Template de bază cu Tailwind
- Toate template-urile extind `base.html` și folosesc clasele Tailwind

### 6. Configurare Django

În `settings.py`:
- `tailwind` și `tema` sunt adăugate în `INSTALLED_APPS`
- `TAILWIND_APP_NAME = 'tema'` este configurat
- `STATICFILES_DIRS` include directorul `tema/static`

## Notă importantă

Dacă adaugi noi clase Tailwind în template-uri, nu uita să rulezi `npm run build` în `tema/static_src` pentru a regenera CSS-ul!

