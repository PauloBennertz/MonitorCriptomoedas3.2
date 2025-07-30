import os
import subprocess
import sys
import shutil

def build_complete():
    """Script completo para build, preparação e teste do executável"""
    
    print("🚀 === BUILD COMPLETO DO MONITOR DE CRIPTOMOEDAS ===")
    print()
    
    # Passo 1: Build do executável
    print("📦 Passo 1: Gerando executável...")
    try:
        cmd = [
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--name=MonitorCriptomoedas',
            '--add-data=icons;icons',
            '--add-data=sons;sons',
            '--add-data=config.json;.',
            '--hidden-import=ttkbootstrap',
            '--hidden-import=PIL',
            '--hidden-import=PIL._tkinter_finder',
            '--hidden-import=pandas',
            '--hidden-import=numpy',
            '--hidden-import=requests',
            '--hidden-import=pycoingecko',
            '--hidden-import=tkinter',
            '--hidden-import=tkinter.ttk',
            '--hidden-import=tkinter.messagebox',
            '--hidden-import=threading',
            '--hidden-import=queue',
            '--hidden-import=json',
            '--hidden-import=os',
            '--hidden-import=sys',
            '--hidden-import=time',
            '--hidden-import=logging',
            '--hidden-import=datetime',
            '--hidden-import=collections',
            '--hidden-import=hashlib',
            '--hidden-import=dataclasses',
            '--hidden-import=typing',
            '--hidden-import=io',
            '--hidden-import=asyncio',
            '--clean',
            'main_app.py'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executável gerado com sucesso!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro durante o build: {e}")
        print(f"📋 Saída de erro: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    
    # Passo 2: Preparar pasta dist
    print("\n📁 Passo 2: Preparando pasta de distribuição...")
    try:
        # Copiar arquivos necessários
        files_to_copy = [
            ('config.json', 'dist/'),
            ('icons', 'dist/'),
            ('sons', 'dist/'),
        ]
        
        for src, dst in files_to_copy:
            if os.path.isdir(src):
                if os.path.exists(dst + os.path.basename(src)):
                    shutil.rmtree(dst + os.path.basename(src))
                shutil.copytree(src, dst + os.path.basename(src))
            else:
                shutil.copy2(src, dst)
        
        print("✅ Arquivos copiados para pasta dist")
        
    except Exception as e:
        print(f"❌ Erro ao preparar pasta dist: {e}")
        return False
    
    # Passo 3: Criar arquivo de instruções
    print("\n📝 Passo 3: Criando documentação...")
    instructions = """# 🚀 Monitor de Criptomoedas

## Como Executar

1. **Execute o arquivo**: `MonitorCriptomoedas.exe`
2. **Primeira execução**: O programa criará as configurações automaticamente
3. **Configurar alertas**: Use o menu "Configurações" para personalizar

## Arquivos Incluídos

- `MonitorCriptomoedas.exe` - Programa principal
- `config.json` - Configurações
- `icons/` - Ícones da interface
- `sons/` - Arquivos de som para alertas

## Requisitos

- Windows 10 ou superior
- Conexão com internet
- 4GB RAM mínimo

## Suporte

Se houver problemas:
1. Execute como administrador
2. Verifique o antivírus
3. Verifique a conexão com internet

🎉 **Pronto para usar!**
"""
    
    with open('dist/LEIA-ME.txt', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("✅ Documentação criada")
    
    # Passo 4: Verificar arquivos
    print("\n🔍 Passo 4: Verificando arquivos...")
    exe_path = "dist/MonitorCriptomoedas.exe"
    if os.path.exists(exe_path):
        size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
        print(f"✅ Executável criado: {size:.1f} MB")
    else:
        print("❌ Executável não encontrado")
        return False
    
    # Listar arquivos finais
    print("\n📁 Arquivos na pasta dist:")
    for item in os.listdir('dist'):
        path = os.path.join('dist', item)
        if os.path.isfile(path):
            size = os.path.getsize(path) / (1024 * 1024)  # MB
            print(f"   📄 {item} ({size:.1f} MB)")
        else:
            print(f"   📁 {item}/")
    
    print("\n🎉 === BUILD CONCLUÍDO COM SUCESSO! ===")
    print("\n📋 Próximos passos:")
    print("1. Navegue até a pasta 'dist'")
    print("2. Execute 'MonitorCriptomoedas.exe'")
    print("3. Configure seus alertas")
    print("4. Aproveite o monitoramento!")
    
    return True

if __name__ == "__main__":
    build_complete() 