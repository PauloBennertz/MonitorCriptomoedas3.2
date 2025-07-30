#!/usr/bin/env python3
"""
Script para configurar e enviar o projeto para GitHub privado
"""

import os
import subprocess
import sys
import json

def run_command(command, description):
    """Executa um comando e trata erros"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} concluído!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro em {description}: {e}")
        print(f"📋 Saída de erro: {e.stderr}")
        return False

def check_git_installed():
    """Verifica se o Git está instalado"""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_github_repository():
    """Configura o repositório GitHub"""
    
    print("🚀 === CONFIGURAÇÃO DO GITHUB PRIVADO ===")
    print()
    
    # Verificar se Git está instalado
    if not check_git_installed():
        print("❌ Git não está instalado!")
        print("📥 Baixe em: https://git-scm.com/")
        return False
    
    # Verificar se já é um repositório Git
    if os.path.exists('.git'):
        print("⚠️  Repositório Git já existe!")
        response = input("Deseja continuar mesmo assim? (s/n): ").lower()
        if response != 's':
            return False
    
    # Inicializar Git (se necessário)
    if not os.path.exists('.git'):
        if not run_command('git init', 'Inicializando repositório Git'):
            return False
    
    # Adicionar arquivos
    if not run_command('git add .', 'Adicionando arquivos ao Git'):
        return False
    
    # Commit inicial
    if not run_command('git commit -m "Versão inicial do Monitor de Criptomoedas v3.1"', 'Fazendo commit inicial'):
        return False
    
    print("\n📋 === PRÓXIMOS PASSOS ===")
    print()
    print("1. Acesse: https://github.com/new")
    print("2. Configure o repositório:")
    print("   - Nome: MonitorCriptomoedas3.1")
    print("   - Descrição: Monitor de criptomoedas com alertas automáticos")
    print("   - ✅ Marque como PRIVADO")
    print("   - ❌ NÃO inicialize com README (já temos)")
    print()
    print("3. Após criar o repositório, execute:")
    print("   git remote add origin https://github.com/SEU_USUARIO/MonitorCriptomoedas3.1.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print()
    print("4. Configure o Cursor:")
    print("   - Settings → Accounts → GitHub")
    print("   - Faça login e autorize acesso a repositórios privados")
    print()
    print("🎉 Pronto! Seu projeto estará seguro no GitHub privado!")
    
    return True

def create_github_workflow():
    """Cria workflow do GitHub Actions para build automático"""
    
    workflow_dir = '.github/workflows'
    os.makedirs(workflow_dir, exist_ok=True)
    
    workflow_content = '''name: Build Executável

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Build executable
      run: |
        python build_exe.py
    
    - name: Upload executable
      uses: actions/upload-artifact@v3
      with:
        name: MonitorCriptomoedas
        path: dist/MonitorCriptomoedas.exe
'''
    
    workflow_file = os.path.join(workflow_dir, 'build.yml')
    with open(workflow_file, 'w', encoding='utf-8') as f:
        f.write(workflow_content)
    
    print("✅ Workflow do GitHub Actions criado!")
    print("📁 Arquivo: .github/workflows/build.yml")

if __name__ == "__main__":
    print("🚀 Configurando projeto para GitHub privado...")
    print()
    
    # Verificar arquivos essenciais
    required_files = ['main_app.py', 'requirements.txt', 'README.md', '.gitignore']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Arquivos faltando: {', '.join(missing_files)}")
        print("Certifique-se de que todos os arquivos estão presentes!")
        sys.exit(1)
    
    # Configurar repositório
    if setup_github_repository():
        # Criar workflow (opcional)
        response = input("\nDeseja criar workflow do GitHub Actions para build automático? (s/n): ").lower()
        if response == 's':
            create_github_workflow()
        
        print("\n🎉 Configuração concluída!")
        print("📋 Siga os passos indicados acima para finalizar.")
    else:
        print("\n❌ Configuração falhou!")
        sys.exit(1) 