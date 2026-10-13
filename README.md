# IFAM Office

Suíte de escritório do **IFAM – Campus São Gabriel da Cachoeira**, construída a partir do código-fonte do LibreOffice (versão estável 26.2.7). Ela funciona e se apresenta como o Microsoft Office em português.

## O que muda em relação ao LibreOffice

| Item | IFAM Office |
|---|---|
| Atalhos | Os do Word, do Excel e do PowerPoint em português (tabela abaixo) |
| Interface | Em abas, parecida com a faixa de opções do Office |
| Ícones | Tema Colibre (no estilo do Office) |
| Formato padrão | .docx, .xlsx e .pptx, sem o aviso "manter formato atual?" |
| Fonte padrão (Writer) | Calibri 11 pt; títulos em Calibri Light |
| Nome e marca | "IFAM Office", com tela de abertura, logotipo e janela Sobre próprios |
| Idioma | Interface e corretor ortográfico em português do Brasil |

### Atalhos

| Função | Atalho | Onde |
|---|---|---|
| Negrito / Itálico / Sublinhado | Ctrl+N / Ctrl+I / Ctrl+S | todos |
| Salvar / Salvar como | Ctrl+B / F12 | todos |
| Selecionar tudo | Ctrl+T | todos |
| Novo / Abrir | Ctrl+O / Ctrl+A | todos |
| Localizar / Substituir | Ctrl+L / Ctrl+U | todos |
| Hiperlink | Ctrl+K | todos |
| Centralizar / Justificar / Esquerda / Direita | Ctrl+E / Ctrl+J / Ctrl+Q / Ctrl+G | Writer e Impress |
| Refazer | Ctrl+R (e Ctrl+Y) | Writer e Impress |
| Fonte / Recuo + / Recuo − / Ir para | Ctrl+D / Ctrl+M / Ctrl+Shift+M / F5 | Writer |
| Preencher para baixo / à direita | Ctrl+D / Ctrl+R | Calc |
| Novo slide / Apresentar | Ctrl+M / F5 | Impress |

## Estrutura

```
scripts/personalizar.py    altera os arquivos de configuração do código-fonte
scripts/compilar.sh        baixa o código, aplica as mudanças e compila o .msi
branding/                  tela de abertura, logotipos e imagem da janela Sobre
branding/fonte/            gerador das imagens (edite as cores e os textos aqui)
.github/workflows/         compilação automática no GitHub (Windows)
```

## Como gerar o instalador (GitHub Actions)

1. Abra a aba **Actions**, escolha **Compilar IFAM Office (Windows)** e clique em **Run workflow**.
2. Ao terminar, baixe o **IFAM-Office-instalador** na página da execução. Ele contém o .msi e o .diff com as mudanças aplicadas.

A primeira compilação pode levar várias horas. As próximas execuções reaproveitam o código-fonte original, as traduções, os downloads de bibliotecas e os resultados disponíveis no cache de compilação (sccache). O cache das fontes é salvo antes da compilação, para continuar disponível mesmo se o build falhar.

O fluxo valida a definição dos produtos do instalador antes de compilar. Em seguida, compila os binários sem gerar o MSI e salva um ponto de retomada com as fontes configuradas, `workdir` e `instdir`. Só depois gera o instalador. Se o empacotamento falhar, outra execução com a mesma base, personalização e imagem Windows pode restaurar esse build e ir diretamente para a geração do MSI. Correções exclusivas do instalador não invalidam esse ponto de retomada; mudanças nas opções de compilação ou nas ferramentas exigem atualizar a versão da chave `lo-build-windows` no workflow.

O GitHub interrompe jobs que passam de 6 horas. Os caches dependem da disponibilidade e da retenção do GitHub; quando não houver ponto de retomada completo, as fontes e os resultados disponíveis no sccache ainda podem ser reaproveitados. O sccache não guarda todos os arquivos, especialmente os compilados com determinados parâmetros de cabeçalhos pré-compilados do MSVC.

## Atualizar para uma nova versão do LibreOffice

Em **Run workflow**, informe outra versão (por exemplo, `libreoffice-26.8.1.1`). O script aplica as mesmas mudanças automaticamente e avisa se algum arquivo tiver mudado de estrutura.

## Licença

O código do LibreOffice é distribuído sob a MPL 2.0. As modificações deste repositório seguem a mesma licença e o diff exato de cada compilação é publicado junto com o instalador. "LibreOffice" é marca da The Document Foundation e "Microsoft Office" é marca da Microsoft; o IFAM Office não usa nenhuma das duas, nem os ícones da Microsoft.
