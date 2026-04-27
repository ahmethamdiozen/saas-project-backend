[🇬🇧 English](README.EN.md)

# SaaS Backend Framework

FastAPI, SQLAlchemy ve Redis Queue (RQ) ile geliştirilmiş, production'a hazır SaaS backend altyapısı. Arka plan iş işleme, güvenilirlik ve gözlemlenebilirlik odağıyla modüler mimari uygular.

## Özellikler

- **FastAPI** — otomatik Swagger belgeli async REST API
- **Arka Plan İşleri** — ilerleme takibi, iptal token'ları ve otomatik yeniden denemeli Redis Queue (RQ)
- **Dağıtık Kilitleme** — worker'lar arasında çift iş işlenmesini engeller
- **JWT Kimlik Doğrulama** — bcrypt şifreleme ile erişim + yenileme token kalıbı
- **Veritabanı Migrasyonları** — versiyonlu şema yönetimi için Alembic
- **Gözlemlenebilirlik** — yapısal loglama, global hata yakalayıcı, sağlık kontrolü uç noktası

## Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Framework | FastAPI |
| Veritabanı | PostgreSQL (SQLAlchemy ORM) |
| Görev Kuyruğu | Redis + RQ (Redis Queue) |
| Migrasyonlar | Alembic |
| Doğrulama | Pydantic v2 |

## Proje Yapısı

```
app/
├── core/           # Loglama, güvenlik, yapılandırma
├── db/             # Veritabanı oturumu ve temel modeller
├── modules/        # Alan güdümlü modüller (Auth, Users, Jobs, Subscriptions)
│   └── [module]/   # router, service, repository, models, schemas
├── worker/         # Arka plan worker, görevler, iptal
└── tests/          # Birim ve entegrasyon testleri
```

## Kurulum

```bash
git clone https://github.com/ahmethamdiozen/saas-project-backend.git
cd saas-project-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`.env` oluştur:
```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/saas_db
SECRET_KEY=gizli-anahtariniz
REDIS_URL=redis://localhost:6379/0
BACKEND_CORS_ORIGINS=http://localhost:3000
```

```bash
alembic upgrade head
uvicorn app.main:app --reload        # API :8000'de
python -m app.worker.worker          # Arka plan worker
```

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testler

```bash
pytest
```

## Lisans

MIT
