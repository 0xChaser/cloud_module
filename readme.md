# Cloud module - Pulumi AWS Infrastructure

## 1. Create virtual env
python -m venv venv
.\venv\Scripts\Activate.ps1

## 2. Install dependencies
uv sync

## 3. Init stack
pulumi stack init dev

## 4. Deploy
pulumi up