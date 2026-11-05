# CloudRacer AI — Laboratório prático na AWS Academy

Neste laboratório, você vai treinar um agente de **aprendizado por reforço** para controlar um carro em uma pista 2D. O agente recebe informações de sensores, decide como dirigir e aprende com as recompensas obtidas ao longo das tentativas.

A execução é feita **pela interface gráfica da AWS**, utilizando **CloudFormation, Amazon S3, AWS Lambda e Amazon SageMaker AI**. 

> **Sobre o simulador:** esta versão é uma adaptação didática do conceito [CloudRacer / Neural Network Racing](https://github.com/akshaybhandare/neural_network). Utiliza um ambiente 2D próprio, com sensores, rede neural PyTorch e o algoritmo REINFORCE. Ela não executa diretamente o jogo Pygame do repositório de referência.

## 1. Pré-requisitos

- Acesso ao **AWS Academy Learner Lab** e permissão para iniciar a sessão.
- Navegador e acesso ao **Console de Gerenciamento da AWS**.
- Arquivos deste projeto, especialmente:
  - [`infra/cloudracer.yaml`](infra/cloudracer.yaml) — template de infraestrutura para o CloudFormation.
  - [`code/source.tar.gz`](code/source.tar.gz) — pacote de código para o treinamento no SageMaker.

**Importante:** baixe e extraia o ZIP completo do projeto em seu computador. O arquivo `source.tar.gz` deve permanecer compactado.

## 2. Iniciar o Learner Lab

1. Entre no ambiente do **AWS Academy Learner Lab**.
2. Clique em **Start Lab**.
3. Depois que o laboratório for iniciado, clique no link **AWS** para abrir o console.
4. No seletor de região, no canto superior direito, escolha **US East (N. Virginia) — `us-east-1`**.

## 3. Criar a infraestrutura pelo CloudFormation

1. Na barra de pesquisa do console, procure por **CloudFormation** e abra o serviço.
2. Entre em **Stacks (Pilhas)** e clique em **Create stack (Criar pilha)**. Se aparecer uma opção, escolha **With new resources (standard)**.
3. Em **Specify template (Especificar modelo)**, selecione **Upload a template file (Carregar arquivo de modelo)**.
4. Clique em **Choose file (Escolher arquivo)** e selecione:

   ```text
   infra/cloudracer.yaml
   ```

5. Avance para a configuração da pilha.
6. Em **Stack name (Nome da pilha)**, informe:

   ```text
   cloudracer
   ```

7. Mantenha as demais configurações padrão e avance até a revisão.
8. Clique em **Submit (Enviar)** para criar a pilha.
9. Aguarde o status **`CREATE_COMPLETE`**.
10. Abra a aba **Outputs (Saídas)** e localize:

   | Saída | Para que será utilizada |
   |---|---|
   | `BucketName` | Nome do bucket S3 que receberá o código e os resultados |
   | `ControllerName` | Nome da função Lambda que iniciará o treinamento |
   | `TrainingImage` | Identificação da imagem PyTorch utilizada pelo SageMaker |

**Resultado esperado:** a pilha cria um bucket S3 privado e uma função Lambda. A função usa a role **`LabRole`**, já existente no Learner Lab.


## 4. Enviar o código para o Amazon S3

1. Pesquise por **S3** e abra o serviço.
2. Entre em **Buckets** e selecione o bucket indicado na saída **`BucketName`** do CloudFormation.
3. Clique em **Create folder (Criar pasta)**, informe `code` e confirme. Se a pasta já existir, apenas abra-a.
4. Dentro da pasta `code/`, clique em **Upload (Carregar)** e depois em **Add files (Adicionar arquivos)**.
5. Selecione o arquivo:

   ```text
   code/source.tar.gz
   ```

6. Confirme o upload.
7. Verifique se o objeto está no caminho:

   ```text
   s3://NOME_DO_BUCKET/code/source.tar.gz
   ```

Substitua `NOME_DO_BUCKET` pelo valor de `BucketName`. **Não extraia nem renomeie `source.tar.gz`.**

## 5. Iniciar o treinamento na Lambda

1. Pesquise por **Lambda** no console.
2. Entre em **Functions (Funções)** e abra a função cujo nome aparece em **`ControllerName`** na saída do CloudFormation.
3. Na aba **Test (Testar)**, crie ou selecione um evento de teste.
4. Dê ao evento um nome como `TreinarCloudRacer`.
5. Substitua o conteúdo do evento pelo JSON abaixo:

   ```json
   {
     "acao": "treinar",
     "episodios": 100,
     "max_passos": 350,
     "semente": 42
   }
   ```

6. Salve o evento, se a interface solicitar, e clique em **Test (Testar)**.
7. Confira a resposta da função. Se o treinamento for iniciado, o resultado deverá conter informações semelhantes a:

   ```json
   {
     "acao": "treinar",
     "job": "cloudracer-original-...",
     "status": "Iniciado",
     "training_job_arn": "arn:aws:sagemaker:..."
   }
   ```

8. **Copie o valor exato de `job`**, pois ele identifica o treinamento que você acabou de iniciar.

> **Não execute a ação `treinar` repetidamente para consultar o progresso.** Cada execução bem-sucedida inicia um novo Training Job e pode gerar novas cobranças.

### Parâmetros do treinamento

| Campo | Significado |
|---|---|
| `acao` | Operação solicitada à Lambda; aqui, `treinar` |
| `episodios` | Quantidade de episódios de aprendizagem |
| `max_passos` | Limite de passos por episódio |
| `semente` | Valor utilizado para reproduzir a inicialização aleatória |

O controlador aceita de **5 a 400 episódios** e de **100 a 1.000 passos** por episódio. Para seguir o tutorial, mantenha os valores do exemplo.

## 6. Acompanhar o treinamento no Amazon SageMaker AI

1. Pesquise por **Amazon SageMaker AI** no console.
2. No menu, localize **Training → Training jobs (Trabalhos de treinamento)**. A localização dessa opção pode variar conforme a versão do console.
3. Encontre o job cujo nome corresponde ao valor `job` retornado pela Lambda.
4. Abra os detalhes do treinamento e acompanhe o **Training job status**:
   - `InProgress`: treinamento em execução;
   - `Completed`: treinamento concluído;
   - `Failed`: treinamento falhou;
   - `Stopped`: treinamento interrompido.
5. Confira o tipo de instância **`ml.m5.large`**, as informações de execução e os registros de logs disponibilizados na página do job e no **Amazon CloudWatch**.
6. Continue somente quando o status for **`Completed`**.

Se preferir consultar o status pela própria função Lambda, crie outro evento de teste com o seguinte conteúdo, substituindo `NOME_EXATO_DO_JOB` pelo identificador copiado na etapa anterior:

```json
{
  "acao": "status",
  "job": "NOME_EXATO_DO_JOB"
}
```

Essa consulta **não inicia outro treinamento**.

## 7. Publicar os resultados no Amazon S3

Quando o treinamento estiver com status `Completed`:

1. Volte ao console do **Lambda** e abra a mesma função de controle.
2. Na aba **Test (Testar)**, crie um novo evento com o nome `PublicarResultados`.
3. Informe o JSON abaixo, substituindo `NOME_EXATO_DO_JOB` pelo nome do treinamento concluído:

   ```json
   {
     "acao": "publicar",
     "job": "NOME_EXATO_DO_JOB"
   }
   ```

4. Clique em **Test (Testar)**.
5. Verifique se o retorno contém o campo `arquivos_s3`, com três arquivos publicados na pasta `resultados/NOME_EXATO_DO_JOB/`:

   | Arquivo | Conteúdo |
   |---|---|
   | `viewer.html` | Visualizador da pista, dos sensores e das trajetórias antes e depois do treino |
   | `metrics.csv` | Histórico das recompensas e avaliações do treinamento |
   | `summary.json` | Resumo das métricas e dos resultados obtidos |

Se a função informar que o treinamento ainda não terminou, volte ao SageMaker e confira o status do job.

## 8. Visualizar o carro e analisar o resultado

1. Abra **Amazon S3 → Buckets**.
2. Entre no bucket criado pelo CloudFormation.
3. Navegue até:

   ```text
   resultados/NOME_EXATO_DO_JOB/
   ```

4. Selecione **`viewer.html`** e clique em **Download (Baixar)**.
5. Abra o arquivo HTML baixado no navegador do computador.
6. Utilize as opções **Antes**, **Depois** e **Reproduzir** para observar o movimento do carro e a leitura dos sensores.
7. Se desejar analisar os dados, baixe também `metrics.csv` e `summary.json`.

Compare a recompensa média antes e depois do treinamento, as colisões e o progresso na pista. **A melhoria não é garantida em toda execução**: os resultados dependem do treinamento e podem variar.

## 9. Excluir os recursos do laboratório

Quando terminar, remova os recursos para evitar consumo desnecessário do orçamento.

1. Em **SageMaker AI → Training jobs**, verifique se o job ainda está em execução. Se estiver e não precisar continuar, utilize a opção de **interromper** o treinamento, se disponível.
2. Baixe os arquivos de resultados que deseja guardar.
3. Em **Amazon S3 → Buckets**, abra o bucket do laboratório e utilize **Empty (Esvaziar)** para remover todos os objetos. Confirme a exclusão conforme as instruções exibidas pelo console.
4. Volte ao **CloudFormation → Stacks**.
5. Selecione a pilha `cloudracer-original` e clique em **Delete (Excluir)**.
6. Verifique se o status final é **`DELETE_COMPLETE`**.

**Observações:** a exclusão da pilha não interrompe automaticamente Training Jobs iniciados pela Lambda. O bucket precisa estar vazio para que o CloudFormation consiga excluí-lo. Logs no CloudWatch também podem permanecer fora da pilha.

# Passo a passo manual na interface da AWS

## Arquivos necessários

Baixe e extraia o ZIP do projeto no computador. Use os seguintes arquivos **sem alterar ou extrair seu conteúdo interno**:

| Arquivo | Quando usar |
|---|---|
| `code/source.tar.gz` | Enviar ao S3 na pasta `code/` |
| `lambda/cloudracer-control.zip` | Enviar na aba **Code** da função Lambda |
| `source/train.py`, `source/racer_env.py`, `source/viewer.py` | Código Python do treinamento, para consulta |

## Etapa 1 — Criar o bucket no Amazon S3

1. No console AWS, abra **Amazon S3 → Buckets → Create bucket**.
2. Em **AWS Region**, escolha `us-east-1`.
3. Em **Bucket type**, selecione **General purpose**, caso a opção seja apresentada.
4. Em **Bucket name**, escolha um nome globalmente exclusivo, com letras minúsculas, números e hífens. Exemplo de padrão: `cloudracer-ai-<identificador>-lab9`. Substitua `<identificador>` por algo exclusivo de sua conta. **Anote exatamente o nome escolhido**.
5. Em **Object Ownership**, mantenha **ACLs disabled / Bucket owner enforced**.
6. Em **Block Public Access**, mantenha **Block all public access** ativado.
7. Em **Bucket Versioning**, pode manter **Disable** para este exercício.
8. Em **Default encryption**, selecione **SSE-S3 (Amazon S3 managed keys)**. Não é necessário criar uma chave KMS.
9. Clique em **Create bucket**.
10. Abra o bucket e escolha **Create folder**. Crie uma pasta chamada `code` (a interface mostrará `code/`).
11. Entre em `code/` → **Upload → Add files** e selecione `code/source.tar.gz` do projeto. Conclua o upload.
12. Verifique que o objeto ficou exatamente em **`code/source.tar.gz`**, e não em `code/code/source.tar.gz`.

**Evidência:** o arquivo `source.tar.gz` deve aparecer dentro de `code/`, mantendo a extensão `.tar.gz`.

## Etapa 2 — Localizar a role IAM já existente

1. No console, abra **IAM → Roles** e procure por **`LabRole`**. Se necessário, use a busca do console.
2. Abra a role e copie o campo **ARN**, que terá formato semelhante a `arn:aws:iam::123456789012:role/LabRole`.
3. Guarde esse valor para configurar a Lambda. Não crie uma nova role.

> O número de conta no ARN acima é **apenas um exemplo**. Use sempre o ARN exibido na sua conta.

## Etapa 3 — Criar a função AWS Lambda

1. Acesse **AWS Lambda → Functions → Create function**.
2. Selecione **Author from scratch / Criar do zero**.
3. Configure os campos:

   | Campo | Valor |
   |---|---|
   | Function name | `cloudracer-manual-control` |
   | Runtime | **Python 3.12** |
   | Architecture | `x86_64` (padrão) |
   | Execution role | **Use an existing role / Usar função existente** |
   | Existing role | **`LabRole`** |

4. Clique em **Create function**.
5. Na aba **Code**, procure **Code source → Upload from → .zip file**.
6. Selecione o arquivo **`lambda/cloudracer-control.zip`** e confirme a substituição do código inicial. **Não extraia o ZIP**: ele contém `index.py` na raiz.
7. Verifique em **Runtime settings / Configurações do runtime** que o **Handler** é `index.handler`. Se for diferente, clique **Edit**, corrija e salve.
8. Abra **Configuration → General configuration → Edit** e defina:

   | Campo | Valor |
   |---|---|
   | Memory | **512 MB** |
   | Timeout | **1 minuto e 30 segundos** (90 s) |

9. Salve as configurações.

> O código da Lambda usa somente bibliotecas padrão do Python e `boto3`, disponível no runtime gerenciado Python da AWS. O arquivo de treinamento PyTorch é **outro arquivo** (`code/source.tar.gz`) e permanece no S3.

## Etapa 4 — Configurar as variáveis de ambiente da Lambda

1. Ainda na função, abra **Configuration → Environment variables → Edit**.
2. Adicione exatamente estas duas variáveis:

   | Chave | Valor |
   |---|---|
   | `LAB_BUCKET` | Nome **exato** do bucket criado na Etapa 1 |
   | `LAB_ROLE_ARN` | ARN **exato** de `LabRole` copiado na Etapa 2 |

3. Salve as alterações.
4. Volte à aba **Code** e confira que o arquivo `index.py` aparece no pacote e que o handler está em `index.handler`.

**Não crie a variável `AWS_REGION`:** ela é fornecida automaticamente pelo runtime da AWS Lambda.

## Etapa 5 — Iniciar o treinamento do carro

1. Na função `cloudracer-manual-control`, entre na aba **Test / Testar**.
2. Crie um novo evento de teste, por exemplo `TreinarCloudRacer`.
3. Substitua o conteúdo do evento por:

```json
{
  "acao": "treinar",
  "episodios": 200,
  "max_passos": 500,
  "semente": 42,
  "learning_rate": 0.001
}
```

4. Salve o evento e clique **Testar** **uma única vez**.
5. Verifique a resposta. Espera-se um JSON contendo `acao: "treinar"`, `job`, `status: "Iniciado"` e `training_job_arn`.

**O que acontece:** a Lambda verifica `code/source.tar.gz`, chama a API `CreateTrainingJob` do SageMaker e termina. O treinamento continua no SageMaker independentemente da Lambda. Ele usa **1 instância `ml.m5.large`**, imagem oficial de treinamento PyTorch, `LabRole` e limite de execução de **1.200 segundos**.

Não é necessário abrir o endereço **TrainingImage** no navegador; ele identifica uma imagem de container usada automaticamente pelo SageMaker, não uma página de login.

## Etapa 6 — Acompanhar o Training Job no SageMaker AI

1. Abra **Amazon SageMaker AI → Training jobs** (use a busca do serviço, se o menu tiver mudado).
2. Localize o job mais recente cujo nome começa com **`cloudracer-original-`**.
3. Abra o job e acompanhe seu **Training job status**:
   - `InProgress`: está treinando;
   - `Completed`: finalizou;
   - `Failed`: falhou; abra o motivo e os logs;
   - `Stopped`: foi interrompido.
4. Em **Monitor** ou **CloudWatch**, observe `train:reward` e `eval:reward` caso sejam apresentados. Esses valores medem o progresso do treinamento, mas não garantem uma volta completa.
5. Espere o estado **`Completed`** para prosseguir.

O SageMaker cria automaticamente o arquivo de artefatos **`model.tar.gz`** em `jobs/<nome-do-job>/output/` dentro do bucket do laboratório.

## Etapa 7 — Publicar os resultados automaticamente

1. Volte à função **`cloudracer-manual-control` → Testar**.
2. Crie ou selecione um evento chamado `PublicarResultados` com este conteúdo:

```json
{
  "acao": "publicar"
}
```

3. Clique **Testar**.
4. O controlador localiza automaticamente o job CloudRacer mais recente, verifica se está `Completed`, lê o `model.tar.gz` e salva os arquivos extraídos na pasta `resultados/<nome-do-job>/` do S3.
5. Abra **S3 → seu bucket → resultados/**, acesse a pasta indicada na resposta e baixe:
   - `viewer.html` — animação do carro antes e depois;
   - `metrics.csv` — métricas por iteração;
   - `summary.json` — resumo das avaliações e do melhor checkpoint.
6. Abra **`viewer.html`** no navegador e utilize os controles de reprodução.

**Não é necessário informar o nome do job no evento.** Atenção: a seleção automática procura o último job com o prefixo CloudRacer na **conta/região**, não necessariamente o último job bem-sucedido nem um job associado ao seu bucket. Para evitar misturar instalações, execute **apenas um dos métodos por conta** ou certifique-se de que o último job foi iniciado pela sua Lambda. Se duas instalações independentes forem usadas na mesma conta, a seleção automática poderá escolher o job da outra instalação.

Se quiser consultar o andamento pela Lambda sem abrir o SageMaker, execute:

```json
{
  "acao": "status"
}
```

## Etapa 8 — Verificar o aprendizado

Abra `summary.json` e procure os seguintes campos:

| Campo | Significado |
|---|---|
| `episodios_treino` | Número de iterações solicitadas |
| `max_passos` | Limite de passos por trajetória |
| `learning_rate` | Taxa de aprendizado do otimizador |
| `largadas_aleatorias_no_treinamento` | Indica o uso de pontos de largada variados |
| `episodio_melhor_checkpoint` | Iteração em que foi registrada a melhor avaliação |
| `recompensa_media_antes_3_partidas` | Média da avaliação inicial |
| `recompensa_media_depois_3_partidas` | Média da avaliação do modelo selecionado |

Um aumento da recompensa pode mostrar aprendizado, mas compare também colisões, passos e comportamento no visualizador. **Não há garantia de que o carro complete uma volta** na pista sinuosa.

## Etapa 9 — Limpeza dos recursos criados manualmente

1. Confirme em **SageMaker AI → Training jobs** que nenhum job da atividade está `InProgress`. Se necessário, interrompa o job pelo console. Os registros históricos de Training Jobs podem permanecer.
2. Baixe os arquivos de resultados que deseja preservar.
3. Em **Lambda → Functions**, selecione `cloudracer-manual-control` e escolha **Delete / Excluir**. Confirme a exclusão.
4. Em **S3 → Buckets**, abra o bucket do CloudRacer e escolha **Empty / Esvaziar**. Essa ação remove os arquivos do bucket, inclusive os resultados.
5. Depois de esvaziá-lo, selecione **Delete bucket / Excluir bucket**. Confirme o nome quando solicitado.
6. Confira os logs do **CloudWatch** associados à função e ao treinamento; remova grupos de logs do projeto se for adequado e permitido na conta.
7. **Não exclua a role `LabRole`**, pois ela foi criada previamente pelo AWS Academy e pode ser utilizada por outras atividades.

> Este método **não cria uma stack CloudFormation**. Portanto, excluir uma stack não limpará os recursos criados manualmente. Lembre-se de apagar Lambda e bucket separadamente.


## Referências

- Documentação AWS: [criar bucket S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)
- Documentação AWS: [criar Lambda e enviar ZIP](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)
- Documentação AWS: [métricas de Training Job](https://docs.aws.amazon.com/sagemaker/latest/dg/view-train-metrics.html)
- Restrições da AWS Academy: arquivo `readme.html` fornecido com o projeto de laboratório.
