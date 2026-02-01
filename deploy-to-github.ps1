# Reddit Life Simulator — публикация на GitHub
# Запуск: .\deploy-to-github.ps1
# Требуется: Git установлен и в PATH; gh (GitHub CLI) опционально для создания репо

$ErrorActionPreference = "Stop"
$repoName = "reddit-life-simulator"

# 1. Проверка Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Ошибка: Git не найден. Установите Git: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

Set-Location $PSScriptRoot

# 2. Инициализация (если ещё не)
if (-not (Test-Path ".git")) {
    git init
    Write-Host "Git инициализирован." -ForegroundColor Green
}

# 3. Проверка что чувствительные файлы НЕ в индексе
$badFiles = @(".env", "config\account1.json", "state\summary.json")
foreach ($f in $badFiles) {
    if (Test-Path $f) {
        git rm --cached $f 2>$null  # убрать из индекса если был добавлен
    }
}

# 4. Добавить всё (по .gitignore)
git add .
$status = git status --short

# Проверка: .env не должен быть в статусе
if ($status -match "\.env\s") {
    Write-Host "ВНИМАНИЕ: .env попал в индекс! Проверьте .gitignore" -ForegroundColor Red
    exit 1
}
if ($status -match "config\\account1\.json\s") {
    Write-Host "ВНИМАНИЕ: config/account1.json попал в индекс! Проверьте .gitignore" -ForegroundColor Red
    exit 1
}

# 5. Коммит
if (git status --porcelain | Select-String "^[ MADRCU]") {
    git add -A
    git commit -m "Initial commit: Reddit Life Simulator v1.0.4"
    Write-Host "Коммит создан." -ForegroundColor Green
} else {
    Write-Host "Нет изменений для коммита (возможно, уже закоммичено)." -ForegroundColor Yellow
}

# 6. Создание репо на GitHub и push
if (Get-Command gh -ErrorAction SilentlyContinue) {
    # GitHub CLI установлен — создаём репо и пушим
    $existing = gh repo view $repoName 2>$null
    if (-not $existing) {
        gh repo create $repoName --public --source=. --remote=origin --push
        Write-Host "Репозиторий создан и залит: https://github.com/$(gh api user -q .login)/$repoName" -ForegroundColor Green
    } else {
        git remote add origin "https://github.com/$(gh api user -q .login)/$repoName.git" 2>$null
        git branch -M main 2>$null
        git push -u origin main
        Write-Host "Push выполнен." -ForegroundColor Green
    }
} else {
    Write-Host @"

GitHub CLI (gh) не установлен. Сделайте вручную:

1. Создайте пустой публичный репо на https://github.com/new
   Название: $repoName

2. Выполните в терминале:

   git remote add origin https://github.com/ВАШ_USERNAME/$repoName.git
   git branch -M main
   git push -u origin main

Или установите gh: winget install GitHub.cli — тогда скрипт создаст репо сам.

"@ -ForegroundColor Yellow
}
