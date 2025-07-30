# 🚀 Guia: Configurar Projeto no GitHub Privado

## 📋 Pré-requisitos

1. **Conta GitHub**: https://github.com/
2. **Git instalado**: https://git-scm.com/
3. **Cursor configurado**: https://cursor.sh/

## 🎯 Passo a Passo

### 1. **Preparar o Projeto**

Execute o script de configuração:
```bash
python setup_github.py
```

### 2. **Criar Repositório no GitHub**

1. Acesse: https://github.com/new
2. Configure:
   - **Repository name**: `MonitorCriptomoedas3.1`
   - **Description**: `Monitor de criptomoedas com alertas automáticos`
   - **Visibility**: ✅ **Private**
   - **Options**: ❌ NÃO marque "Add a README file"
   - **Options**: ❌ NÃO marque "Add .gitignore"
   - **Options**: ❌ NÃO marque "Choose a license"

3. Clique em **"Create repository"**

### 3. **Conectar Projeto Local ao GitHub**

No terminal do seu projeto:
```bash
# Adicionar repositório remoto (substitua SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/MonitorCriptomoedas3.1.git

# Renomear branch para main
git branch -M main

# Enviar para GitHub
git push -u origin main
```

### 4. **Configurar Cursor**

1. Abra o Cursor
2. Vá em **Settings** (⚙️)
3. **Accounts** → **GitHub**
4. Faça login com sua conta GitHub
5. Autorize acesso a **repositórios privados**

### 5. **Verificar Configuração**

```bash
# Verificar status
git status

# Verificar repositório remoto
git remote -v

# Verificar branches
git branch -a
```

## 🔧 Configurações Avançadas

### **Workflow Automático (Opcional)**

Se você escolheu criar o workflow no script:
1. Vá para **Actions** no seu repositório GitHub
2. O workflow será executado automaticamente
3. Baixe o executável gerado em **Artifacts**

### **Configurações de Segurança**

1. **Settings** → **Security** → **Code security and analysis**
2. Ative:
   - ✅ **Dependency graph**
   - ✅ **Dependabot alerts**
   - ✅ **Code scanning**

### **Colaboradores (Opcional)**

1. **Settings** → **Collaborators and teams**
2. Adicione colaboradores por email
3. Defina permissões adequadas

## 📁 Estrutura Final

```
MonitorCriptomoedas3.1/
├── .github/
│   └── workflows/
│       └── build.yml          # Build automático
├── .gitignore                 # Arquivos ignorados
├── .cursorrules              # Configuração do agente
├── LICENSE                   # Licença MIT
├── README.md                 # Documentação
├── requirements.txt          # Dependências
├── setup_github.py          # Script de configuração
├── main_app.py              # Aplicação principal
├── build_exe.py             # Script de build
├── config.json              # Configurações
├── icons/                   # Ícones
├── sons/                    # Sons de alerta
└── [outros arquivos...]
```

## 🎉 Benefícios da Configuração

### **Segurança**
- ✅ Código protegido em repositório privado
- ✅ Controle total de acesso
- ✅ Backup automático no GitHub

### **Colaboração**
- ✅ Versionamento completo
- ✅ Histórico de mudanças
- ✅ Possibilidade de adicionar colaboradores

### **Integração com Cursor**
- ✅ Agente tem acesso total ao código
- ✅ Análise inteligente do projeto
- ✅ Sugestões personalizadas
- ✅ Debugging avançado

### **Automação**
- ✅ Build automático com GitHub Actions
- ✅ Executável gerado automaticamente
- ✅ Deploy simplificado

## 🔄 Comandos Úteis

### **Atualizações Diárias**
```bash
# Adicionar mudanças
git add .

# Fazer commit
git commit -m "Descrição das mudanças"

# Enviar para GitHub
git push
```

### **Verificar Status**
```bash
# Status do repositório
git status

# Histórico de commits
git log --oneline

# Branches
git branch -a
```

### **Sincronizar Mudanças**
```bash
# Baixar mudanças do GitHub
git pull origin main

# Verificar diferenças
git diff
```

## 🆘 Solução de Problemas

### **Erro: "Repository not found"**
- Verifique se o repositório foi criado corretamente
- Confirme o nome do usuário no comando

### **Erro: "Permission denied"**
- Verifique se você tem acesso ao repositório
- Confirme se o repositório é privado

### **Erro: "Authentication failed"**
- Configure suas credenciais Git
- Use token de acesso pessoal se necessário

### **Cursor não acessa repositório**
- Verifique configuração do GitHub no Cursor
- Confirme autorização para repositórios privados

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do Git
2. Consulte a documentação do GitHub
3. Verifique as configurações do Cursor
4. Abra uma issue no repositório

---

**🎉 Seu projeto está agora seguro no GitHub privado!**

O agente do Cursor terá acesso total para te ajudar com desenvolvimento, debugging e melhorias. 