# Smart Security
Solução de controle de acesso à internet por whitelist

Em ambientes de trabalho, o acesso irrestrito à internet está diretamente relacionado à produtividade do empregado. Este documento descreve o desenvolvimento de uma solução que limita os websites que podem ser acessados durante o horário de trabalho.

A proposta consiste no uso de uma lista de permissões (whitelist), onde o usuário pode acessar apenas um conjunto seleto de domínios, sendo todos os demais automaticamente bloqueados.

---

## Visão geral da solução

Existem múltiplas abordagens para implementar esse tipo de controle, incluindo:

- Alteração de configurações de Firewall
- Uso de Proxy
- Modificação do arquivo "hosts" do Windows
- Objetos de Política de Grupo (GPO)

Considerando um cenário com múltiplas máquinas que não estão conectadas a um mesmo servidor ou domínio, optou-se por uma solução alternativa baseada em extensões de navegador.

---

## Extensões de lojas oficiais

Os principais navegadores utilizados em ambientes corporativos — Google Chrome, Mozilla Firefox e Microsoft Edge — possuem lojas oficiais de extensões integradas.

Foi escolhida a extensão **LeechBlock NG**, por ser:

- De código aberto
- Amplamente utilizada
- Bem avaliada pela comunidade

O objetivo foi instalar a mesma extensão em todos os navegadores, garantindo um comportamento uniforme.

---

## Instalação automatizada da extensão

A instalação da extensão pode ser automatizada por meio de arquivos de lote (.bat), que adicionam chaves específicas ao Registro do Windows.

Exemplo de comando utilizado para o Google Chrome:

set EXT_ID1=blaaajhemilngeeffpbfkdjjoefldkok
set UPDATE_URL1=https://clients2.google.com/service/update2/crx
REG ADD "HKLM\Software\Policies\Google\Chrome\ExtensionInstallForcelist" /v 1 /t REG_SZ /d "%EXT_ID1%;%UPDATE_URL1%" /f


Esse comando define:

- O ID da extensão
- A URL oficial da loja
- A chave de registro responsável por forçar a instalação

Como resultado:

- A extensão é instalada automaticamente pelo navegador
- A desinstalação manual pelo navegador é bloqueada

Observação: caso o usuário possua acesso administrativo ao Editor de Registro, ainda é possível remover a extensão apagando manualmente a chave registrada.

---

## Aplicação Smart Security

Para facilitar a automação e o gerenciamento dessas alterações, foi desenvolvido o aplicativo **Smart Security**.

Ele é responsável por:

- Gerenciar as chaves de registro
- Ativar e desativar o bloqueio de websites
- Bloquear portas USB para dispositivos de armazenamento
- Manter funcionamento normal de mouses, teclados e fones de ouvido

---

## Instalação e uso do Smart Security

Ao ser executado, o programa:

- Requer privilégios de administrador
- Solicita uma senha de acesso

Após a autenticação, é exibido um painel com quatro opções:

- Ativar Bloqueio de Websites
- Desativar Bloqueio de Websites
- Ativar Bloqueio de Portas USB
- Desativar Bloqueio de Portas USB

Na parte superior do painel, existem dois indicadores visuais que mostram:

- Se a extensão está instalada ou não
- Se as portas USB estão ativas ou bloqueadas

---

## Ativação do bloqueio de websites

Ao selecionar a opção "Ativar Bloqueio de Websites":

- A extensão LeechBlock NG é instalada nos navegadores:
  - Google Chrome
  - Microsoft Edge
  - Mozilla Firefox
- Um arquivo chamado `options.txt` é gerado na área de trabalho

Esse arquivo contém:

- Configurações de bloqueio da extensão
- Um link para a whitelist hospedada no GitHub da empresa

---

## Configuração manual nos navegadores

Após a instalação da extensão, é necessário realizar uma configuração manual inicial.

O processo é idêntico em todos os navegadores. O Google Chrome é utilizado como exemplo:

1. Acesse a aba de extensões do navegador
2. Selecione a extensão LeechBlock NG
3. Clique em "Opções"

Ao abrir o painel da extensão:

- Acesse a aba "General"
- Ative a opção "Requires the user to input a password"
- Defina uma senha no campo "Password"


Após isso:

- No campo "Import file", selecione o arquivo `options.txt`
- Confirme a importação para aplicar automaticamente as regras de bloqueio

---

## Alteração da whitelist

A whitelist de sites permitidos está hospedada no GitHub, junto ao código-fonte do projeto.

Para alterá-la:

1. Acesse o repositório "SmartSecurity" no GitHub da Icomportamento
2. Abra o arquivo `whitelist.txt`
3. Clique em editar
4. Adicione ou remova os domínios desejados

Observação importante:

- Cada domínio deve obrigatoriamente iniciar com o símbolo `+`
- Sem esse prefixo, o domínio não será reconhecido pela extensão

---

## Desinstalação manual

Caso o Smart Security seja removido ou fique inacessível, é possível reverter as configurações manualmente pelo Editor de Registro do Windows.

Passos:

1. Pressione `Win + R`
2. Digite `regedit`
3. Confirme o acesso como administrador

As chaves utilizadas estão localizadas em:
HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Google\Chrome\ExtensionInstallForcelist
HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Edge\ExtensionInstallForcelist


No caso do Mozilla Firefox, as configurações ficam armazenadas em um diretório específico dentro da estrutura de políticas do navegador.

---

## Código-fonte

O código do Smart Security é composto por:

- Lógica em Python para controle de menus
- Execução de arquivos `.bat` que interagem com o Registro do Windows

As duas partes principais são:

- Interface gráfica construída com a biblioteca `tkinter`
- Execução de comandos via arquivos de lote

Após finalizado, o projeto é convertido em um executável único por meio do PyInstaller


O resultado é um arquivo `.exe` autônomo.

---

## Administração das whitelists

O funcionamento completo do Smart Security envolve:

- Autenticação em uma base de dados
- Seleção da whitelist desejada
- Atualização do arquivo `.txt` com o link da whitelist
- Inserção desse arquivo na extensão do navegador

Por meio de uma aplicação web, será possível:

- Editar whitelists remotamente
- Atualizar automaticamente as regras nos navegadores
- Manter centralizado o controle de acesso

As whitelists serão hospedadas no domínio `smartmft.com.br`.



