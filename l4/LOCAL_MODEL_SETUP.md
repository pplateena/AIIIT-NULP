# Local LLM Setup Guide - Ollama

## Встановлення Ollama на Fedora

### 1. Встановлення Ollama

```bash
# Завантажити та встановити
curl -fsSL https://ollama.com/install.sh | sh

# Або вручну
sudo dnf install -y ollama
```

### 2. Запустити Ollama сервіс

```bash
# Запустити сервер (в окремому терміналі)
ollama serve

# Або як systemd сервіс
sudo systemctl enable ollama
sudo systemctl start ollama
```

### 3. Завантажити моделі

```bash
# Рекомендовані моделі для RAG (від найшвидших до найкращих):

# Легка модель (швидка, 3.8GB)
ollama pull phi3

# Середня модель (баланс, 4.7GB)
ollama pull llama3.2

# Потужна модель (якісна, 7.4GB)
ollama pull mistral

# Найкраща якість (повільно, 13GB)
ollama pull llama3.1:8b
```

### 4. Перевірити встановлення

```bash
# Переглянути встановлені моделі
ollama list

# Тестовий запит
ollama run phi3 "What is a RAG system?"
```

---

## Вимоги до системи

### Мінімальні:
- **RAM:** 8GB (для phi3)
- **Диск:** 5GB вільного місця
- **CPU:** Будь-який сучасний (краще 4+ ядра)

### Рекомендовані:
- **RAM:** 16GB+ (для llama3/mistral)
- **GPU:** NVIDIA з 6GB+ VRAM (прискорення в 10-20 разів)
- **Диск:** 20GB+ (для декількох моделей)

---

## Інтеграція з RAG системою

Додано підтримку в `llm_interface.py` - див. клас `OllamaLLM`

### Використання:

```bash
# В .env файлі
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_MODEL=phi3  # або llama3.2, mistral, etc.
OLLAMA_BASE_URL=http://localhost:11434
```

### Запуск тестів:

```bash
# З локальною моделлю
python test_rag_resumable.py --llm-provider ollama

# Або
python main_simple.py ask --llm-provider ollama
```

---

## Порівняння моделей

| Модель | Розмір | RAM | Швидкість | Якість | Рекомендація |
|--------|--------|-----|-----------|--------|--------------|
| **phi3** | 3.8GB | 8GB | ⚡⚡⚡ | ⭐⭐⭐ | Розробка/дебаг |
| **llama3.2** | 4.7GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | **Рекомендовано** |
| **mistral** | 7.4GB | 16GB | ⚡⚡ | ⭐⭐⭐⭐ | Якість |
| **llama3.1:8b** | 13GB | 16GB | ⚡ | ⭐⭐⭐⭐⭐ | Найкраща якість |

---

## Переваги локальних моделей

✅ **Необмежені запити** - тестуй скільки хочеш
✅ **Приватність** - дані не виходять з комп'ютера
✅ **Офлайн робота** - не потрібен інтернет
✅ **Безкоштовно** - немає квот і лімітів
✅ **Швидкість** - немає мережевих затримок

## Недоліки

❌ **Нижча якість** - ніж GPT-4/Claude/Gemini
❌ **Потребує ресурсів** - RAM/диск/CPU
❌ **Повільніше** - без GPU
❌ **Довші відповіді** - може генерувати більше тексту

---

## Troubleshooting

### Ollama не запускається:
```bash
# Перевірити статус
systemctl status ollama

# Переглянути логи
journalctl -u ollama -f
```

### Модель повільна:
- Використовуй меншу модель (phi3)
- Закрий інші програми
- Зменш `max_tokens` в конфігурації

### Мало RAM:
```bash
# Використовуй найменшу модель
ollama pull phi3:mini

# Або налаштуй swap
sudo dd if=/dev/zero of=/swapfile bs=1G count=8
sudo mkswap /swapfile
sudo swapon /swapfile
```
