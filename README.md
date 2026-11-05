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

Use a região **US East (N. Virginia) — `us-east-1`** durante todo o laboratório. O `readme.html` do Learner Lab também permite `us-west-2`, mas este tutorial utiliza `us-east-1` como padrão.

## 2. Iniciar o Learner Lab

1. Entre no ambiente do **AWS Academy Learner Lab**.
2. Clique em **Start Lab**.
3. Depois que o laboratório for iniciado, clique no link **AWS** para abrir o console.
4. No seletor de região, no canto superior direito, escolha **US East (N. Virginia) — `us-east-1`**.
5. Verifique o orçamento disponível no ambiente do laboratório antes de criar recursos.

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


## Estrutura dos arquivos utilizados

```text
cn-aws-cloudracer-ai-lab/
├── README.md                     # Este tutorial
├── infra/
│   └── cloudracer.yaml  # Infraestrutura CloudFormation
├── code/
│   └── source.tar.gz             # Código enviado ao S3
├── source/                        # Arquivos-fonte do treinamento
    ├── train.py
    ├── racer_env.py
    └── viewer.py
```

